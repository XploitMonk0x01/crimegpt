"""
RAG Service — Retrieval-Augmented Generation pipeline using ChromaDB.

Provides:
    - ingest_corpus() — chunk legal docs, embed, store in ChromaDB
    - query() — embed query, similarity search, return top-k chunks
    - get_collection_stats() — info about the vector store

Supports two chunking strategies:
    - Section-aware: splits on `--- Section N ---` markers (preferred for BNS)
    - Character-based: fallback for unstructured docs

Usage:
    from app.services.ragService import RAGService
    rag = RAGService()
    chunks = await rag.query("What are the penalties for theft under BNS 2023?")
"""

import logging
import re
from pathlib import Path
from typing import Any

from app.config import get_settings

logger = logging.getLogger("crimegpt.rag")


class FastEmbedEmbeddingFunction:
    """Custom embedding function using FastEmbed for pure-Python embeddings."""
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        # Lazy import to avoid loading weights unnecessarily
        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name=model_name)
        
    def __call__(self, input: list[str]) -> list[list[float]]:
        # Returns a generator of numpy arrays, we convert to list of lists
        embeddings = self._model.embed(input)
        return [list(e) for e in embeddings]


class RAGService:
    """ChromaDB-based RAG pipeline for legal corpus retrieval."""

    def __init__(self):
        self._settings = get_settings()
        self._client = None
        self._collection = None
        self._embedding_fn = None

    def _get_client(self):
        """Lazy-init ChromaDB client and FastEmbed function."""
        if self._client is None:
            try:
                import chromadb

                if not self._embedding_fn:
                    logger.info("Initializing FastEmbed embedding model...")
                    self._embedding_fn = FastEmbedEmbeddingFunction()

                self._client = chromadb.HttpClient(
                    host=self._settings.chroma.host,
                    port=self._settings.chroma.port,
                )
                self._collection = self._client.get_or_create_collection(
                    name=self._settings.chroma.collection_name,
                    embedding_function=self._embedding_fn,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(
                    f"Connected to ChromaDB at "
                    f"{self._settings.chroma.host}:{self._settings.chroma.port}"
                )
            except Exception as e:
                logger.warning(f"ChromaDB not available: {e}")
                self._client = None
                self._collection = None
        return self._collection

    async def query(
        self,
        query_text: str,
        *,
        n_results: int = 5,
        where: dict | None = None,
        min_similarity: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Query the legal corpus — embed query and find similar chunks.

        Returns list of dicts with: text, metadata, distance (similarity score).
        Falls back to mock results if ChromaDB is unavailable.
        """
        collection = self._get_client()
        if not collection:
            logger.warning("ChromaDB not available — returning mock results")
            return self._mock_results(query_text)

        try:
            kwargs: dict[str, Any] = {
                "query_texts": [query_text],
                "n_results": n_results,
            }
            if where:
                kwargs["where"] = where

            results = collection.query(**kwargs)

            chunks = []
            if results and results.get("documents"):
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                dists = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

                for doc, meta, dist in zip(docs, metas, dists):
                    # Chroma returns cosine distance (0 is identical, 1 is orthogonal)
                    # For fastembed BGE models, good matches are usually distance < 0.5 (similarity > 0.5)
                    similarity = round(1.0 - dist, 4)
                    
                    if similarity >= min_similarity:
                        chunks.append({
                            "text": doc,
                            "metadata": meta,
                            "similarity": similarity,
                        })

            logger.info(f"RAG query returned {len(chunks)} chunks (threshold {min_similarity}) for: {query_text[:80]}...")
            return chunks

        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return self._mock_results(query_text)

    async def ingest_corpus(self, corpus_dir: str | None = None) -> dict[str, Any]:
        """
        Ingest legal documents from corpus directory into ChromaDB.

        Uses section-aware chunking for files with `--- Section N ---` markers,
        falls back to character-based chunking otherwise.
        """
        collection = self._get_client()
        if not collection:
            return {"status": "skipped", "reason": "ChromaDB not available"}

        corpus_path = Path(corpus_dir) if corpus_dir else Path("./corpus")
        if not corpus_path.exists():
            return {"status": "skipped", "reason": f"Corpus directory not found: {corpus_path}"}

        ingested = 0
        errors = 0
        files_processed = []

        for file_path in corpus_path.rglob("*.txt"):
            # Skip README, gitkeep, etc.
            if file_path.name.startswith(".") or file_path.name.lower() == "readme.md":
                continue

            try:
                text = file_path.read_text(encoding="utf-8")
                act_name = file_path.parent.name  # e.g., "bns_2023"

                # Choose chunking strategy
                if "--- Section" in text:
                    chunks, chunk_metas = self._chunk_by_section(text, act_name, file_path.name)
                else:
                    chunks = self._chunk_text(text, chunk_size=500, overlap=50)
                    chunk_metas = [
                        {
                            "source": file_path.name,
                            "act": act_name,
                            "chunk_index": i,
                        }
                        for i in range(len(chunks))
                    ]

                if not chunks:
                    continue

                ids = [f"{file_path.stem}_{i}" for i in range(len(chunks))]

                # Upsert in batches of 100 (ChromaDB limit)
                batch_size = 100
                for start in range(0, len(chunks), batch_size):
                    end = start + batch_size
                    collection.upsert(
                        ids=ids[start:end],
                        documents=chunks[start:end],
                        metadatas=chunk_metas[start:end],
                    )

                ingested += len(chunks)
                files_processed.append({
                    "file": file_path.name,
                    "chunks": len(chunks),
                    "act": act_name,
                })
                logger.info(f"Ingested {len(chunks)} chunks from {file_path.name}")

            except Exception as e:
                errors += 1
                logger.error(f"Failed to ingest {file_path}: {e}")

        return {
            "status": "completed",
            "chunks_ingested": ingested,
            "files": files_processed,
            "errors": errors,
        }

    def _chunk_by_section(
        self, text: str, act_name: str, filename: str
    ) -> tuple[list[str], list[dict]]:
        """
        Section-aware chunking for BNS-style legal documents.

        Splits on `--- Section N ---` markers, then sub-chunks sections
        that exceed max_chunk_size. Each chunk preserves section number
        and act name in metadata for precise citation.
        """
        max_chunk_size = 1500  # chars — larger than char-based to keep sections intact
        sub_chunk_size = 800
        sub_chunk_overlap = 100

        # Split by section markers
        parts = re.split(r'--- Section (\d+) ---', text)

        chunks: list[str] = []
        metas: list[dict] = []

        # parts[0] = preamble (before first section)
        preamble = parts[0].strip()
        if preamble and len(preamble) > 50:
            chunks.append(preamble)
            metas.append({
                "source": filename,
                "act": act_name,
                "section": "preamble",
                "chunk_index": 0,
            })

        # Process section pairs: parts[1]=section_num, parts[2]=content, ...
        for i in range(1, len(parts) - 1, 2):
            section_num = parts[i]
            section_text = parts[i + 1].strip()

            if not section_text:
                continue

            # Prepend section number for context
            section_header = f"Section {section_num}."
            full_section = f"{section_header} {section_text}"

            if len(full_section) <= max_chunk_size:
                # Section fits in one chunk
                chunks.append(full_section)
                metas.append({
                    "source": filename,
                    "act": act_name,
                    "section": section_num,
                    "chunk_index": len(chunks) - 1,
                })
            else:
                # Sub-chunk large sections
                sub_chunks = self._chunk_text(full_section, sub_chunk_size, sub_chunk_overlap)
                for j, sc in enumerate(sub_chunks):
                    chunks.append(sc)
                    metas.append({
                        "source": filename,
                        "act": act_name,
                        "section": section_num,
                        "sub_chunk": j,
                        "chunk_index": len(chunks) - 1,
                    })

        logger.info(
            f"Section-aware chunking: {len(chunks)} chunks from "
            f"{(len(parts)-1)//2} sections in {filename}"
        )
        return chunks, metas

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """Split text into overlapping chunks by character count."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start = end - overlap
        return chunks

    def _mock_results(self, query_text: str) -> list[dict[str, Any]]:
        """Fallback mock results when ChromaDB is unavailable."""
        # Provide realistic mock data covering common BNS sections
        mock_db = [
            {
                "text": (
                    "Section 303. Theft — Whoever, intending to take dishonestly "
                    "any movable property out of the possession of any person without "
                    "that person's consent, moves that property in order to such taking, "
                    "is said to commit theft. Punishment: imprisonment up to three years, "
                    "or fine, or both."
                ),
                "metadata": {"source": "bns-2023.txt", "act": "bns_2023", "section": "303"},
                "similarity": 0.85,
            },
            {
                "text": (
                    "Section 304. Snatching — Whoever commits theft by snatching "
                    "any movable property from any person shall be punished with "
                    "imprisonment of either description for a term which may extend "
                    "to three years, and shall also be liable to fine."
                ),
                "metadata": {"source": "bns-2023.txt", "act": "bns_2023", "section": "304"},
                "similarity": 0.78,
            },
            {
                "text": (
                    "Section 101. Murder — Except in the cases hereinafter excepted, "
                    "culpable homicide is murder if the act by which the death is caused "
                    "is done with the intention of causing death, or with the intention of "
                    "causing such bodily injury as the offender knows to be likely to cause "
                    "the death of the person to whom the harm is caused."
                ),
                "metadata": {"source": "bns-2023.txt", "act": "bns_2023", "section": "101"},
                "similarity": 0.72,
            },
            {
                "text": (
                    "Section 63. Rape — A man is said to commit rape if he penetrates "
                    "his penis, to any extent, into the vagina, mouth, urethra or anus of "
                    "a woman or makes her to do so with him or any other person, under "
                    "circumstances falling under any of seven descriptions including "
                    "against her will or without her consent."
                ),
                "metadata": {"source": "bns-2023.txt", "act": "bns_2023", "section": "63"},
                "similarity": 0.70,
            },
        ]

        # Basic keyword matching for relevant mock results
        query_lower = query_text.lower()
        scored = []
        for item in mock_db:
            score = 0
            for word in query_lower.split():
                if word in item["text"].lower():
                    score += 1
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        if scored:
            return [item for _, item in scored[:3]]
        return mock_db[:2]

    async def get_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        collection = self._get_client()
        if not collection:
            return {"status": "unavailable", "using_mock": True}
        try:
            count = collection.count()
            return {
                "status": "connected",
                "collection": self._settings.chroma.collection_name,
                "count": count,
                "using_mock": False,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
