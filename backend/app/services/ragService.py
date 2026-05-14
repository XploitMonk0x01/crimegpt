"""
RAG Service — Retrieval-Augmented Generation pipeline using ChromaDB.

Provides:
    - ingest_corpus() — chunk legal docs, embed, store in ChromaDB
    - query() — embed query, similarity search, return top-k chunks
    - get_collection_stats() — info about the vector store

Supports two retrieval paths:
    - ChromaDB + FastEmbed when the vector server is available
    - Local lexical retrieval over backend/corpus as a zero-setup fallback

Usage:
    from app.services.ragService import RAGService
    rag = RAGService()
    chunks = await rag.query("What are the penalties for theft under BNS 2023?")
"""

import logging
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings

logger = logging.getLogger("crimegpt.rag")

_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")
_SECTION_SPLIT_RE = re.compile(r"--- Section ([0-9A-Za-z-]+) ---")


class FastEmbedEmbeddingFunction:
    """Custom embedding function using FastEmbed for ChromaDB embeddings."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        # Lazy import to avoid loading weights unless Chroma is actually reachable.
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model_name)

    def __call__(self, input: list[str]) -> list[list[float]]:
        # FastEmbed returns a generator of numpy arrays; Chroma expects plain floats.
        return [[float(value) for value in embedding] for embedding in self._model.embed(input)]


@lru_cache(maxsize=8)
def _load_local_chunks(corpus_dir: str) -> tuple[dict[str, Any], ...]:
    """Load and chunk corpus files for zero-setup local retrieval."""
    service = RAGService()
    corpus_path = Path(corpus_dir)
    chunks: list[dict[str, Any]] = []

    if not corpus_path.exists():
        logger.warning("Local corpus directory not found: %s", corpus_path)
        return tuple()

    for file_path in corpus_path.rglob("*.txt"):
        if file_path.name.startswith("."):
            continue

        try:
            text = file_path.read_text(encoding="utf-8")
            act_name = file_path.parent.name
            if "--- Section" in text:
                docs, metas = service._chunk_by_section(text, act_name, file_path.name)
            else:
                docs = service._chunk_text(text, chunk_size=900, overlap=120)
                metas = [
                    {"source": file_path.name, "act": act_name, "chunk_index": i}
                    for i in range(len(docs))
                ]

            for doc, meta in zip(docs, metas):
                chunks.append({"text": doc, "metadata": meta, "tokens": _tokenize(doc)})
        except Exception as exc:  # pragma: no cover - defensive file loading path
            logger.error("Failed to load local corpus file %s: %s", file_path, exc)

    logger.info("Loaded %s local RAG chunks from %s", len(chunks), corpus_path)
    return tuple(chunks)


def _tokenize(text: str) -> set[str]:
    """Tokenize text for lightweight lexical retrieval."""
    return {token.lower() for token in _TOKEN_RE.findall(text) if len(token) > 1}


def _default_corpus_dir() -> Path:
    """Return the backend corpus path independent of the process cwd."""
    return Path(__file__).resolve().parents[2] / "corpus"


class RAGService:
    """ChromaDB-based RAG pipeline with a local corpus fallback."""

    def __init__(self):
        self._settings = get_settings()
        self._client = None
        self._collection = None
        self._embedding_fn = None

    def _get_client(self):
        """Lazy-init ChromaDB client and FastEmbed function."""
        if self._client is None and self._collection is None:
            try:
                import chromadb

                self._client = chromadb.HttpClient(
                    host=self._settings.chroma.host,
                    port=self._settings.chroma.port,
                )
                # Verify server availability before loading embedding weights.
                self._client.heartbeat()

                if self._embedding_fn is None:
                    logger.info("Initializing FastEmbed embedding model...")
                    self._embedding_fn = FastEmbedEmbeddingFunction()

                self._collection = self._client.get_or_create_collection(
                    name=self._settings.chroma.collection_name,
                    embedding_function=self._embedding_fn,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(
                    "Connected to ChromaDB at %s:%s",
                    self._settings.chroma.host,
                    self._settings.chroma.port,
                )
            except Exception as e:
                logger.warning("ChromaDB not available; using local corpus fallback: %s", e)
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
        Query the legal corpus and return top matching chunks.

        ChromaDB is preferred. If ChromaDB or embeddings are unavailable, this method
        still returns useful results by searching the checked-in legal corpus locally.
        """
        collection = self._get_client()
        if collection is None:
            return self._query_local_corpus(
                query_text,
                n_results=n_results,
                where=where,
                min_similarity=min_similarity,
            )

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
                    # Chroma returns cosine distance (0 identical, 1 orthogonal).
                    similarity = round(max(0.0, 1.0 - float(dist)), 4)
                    if similarity >= min_similarity:
                        chunks.append({"text": doc, "metadata": meta or {}, "similarity": similarity})

            logger.info(
                "RAG query returned %s Chroma chunks (threshold %s) for: %s...",
                len(chunks),
                min_similarity,
                query_text[:80],
            )
            return chunks

        except Exception as e:
            logger.error("RAG query error; using local corpus fallback: %s", e)
            return self._query_local_corpus(
                query_text,
                n_results=n_results,
                where=where,
                min_similarity=min_similarity,
            )

    async def ingest_corpus(self, corpus_dir: str | None = None) -> dict[str, Any]:
        """
        Ingest legal documents from corpus directory into ChromaDB.

        Uses section-aware chunking for files with `--- Section N ---` markers,
        falls back to character-based chunking otherwise.
        """
        collection = self._get_client()
        if collection is None:
            return {
                "status": "skipped",
                "reason": "ChromaDB not available; local corpus fallback is active",
                "fallback_chunks": len(_load_local_chunks(str(self._resolve_corpus_path(corpus_dir)))),
            }

        corpus_path = self._resolve_corpus_path(corpus_dir)
        if not corpus_path.exists():
            return {"status": "skipped", "reason": f"Corpus directory not found: {corpus_path}"}

        ingested = 0
        errors = 0
        files_processed = []

        for file_path in corpus_path.rglob("*.txt"):
            if file_path.name.startswith("."):
                continue

            try:
                text = file_path.read_text(encoding="utf-8")
                act_name = file_path.parent.name

                if "--- Section" in text:
                    chunks, chunk_metas = self._chunk_by_section(text, act_name, file_path.name)
                else:
                    chunks = self._chunk_text(text, chunk_size=900, overlap=120)
                    chunk_metas = [
                        {"source": file_path.name, "act": act_name, "chunk_index": i}
                        for i in range(len(chunks))
                    ]

                if not chunks:
                    continue

                safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", file_path.stem)
                ids = [f"{act_name}_{safe_stem}_{i}" for i in range(len(chunks))]

                batch_size = 100
                for start in range(0, len(chunks), batch_size):
                    end = start + batch_size
                    collection.upsert(
                        ids=ids[start:end],
                        documents=chunks[start:end],
                        metadatas=chunk_metas[start:end],
                    )

                ingested += len(chunks)
                files_processed.append({"file": file_path.name, "chunks": len(chunks), "act": act_name})
                logger.info("Ingested %s chunks from %s", len(chunks), file_path.name)

            except Exception as e:
                errors += 1
                logger.error("Failed to ingest %s: %s", file_path, e)

        _load_local_chunks.cache_clear()
        return {
            "status": "completed",
            "chunks_ingested": ingested,
            "files": files_processed,
            "errors": errors,
        }

    def _resolve_corpus_path(self, corpus_dir: str | None = None) -> Path:
        if corpus_dir:
            path = Path(corpus_dir)
            if path.exists():
                return path
            backend_relative = Path(__file__).resolve().parents[2] / corpus_dir
            if backend_relative.exists():
                return backend_relative
        return _default_corpus_dir()

    def _query_local_corpus(
        self,
        query_text: str,
        *,
        n_results: int,
        where: dict | None,
        min_similarity: float,
    ) -> list[dict[str, Any]]:
        """Lightweight local search used when ChromaDB is unavailable."""
        corpus_path = self._resolve_corpus_path(None)
        chunks = _load_local_chunks(str(corpus_path))
        query_tokens = _tokenize(query_text)
        if not chunks or not query_tokens:
            return self._mock_results(query_text)[:n_results]

        scored: list[tuple[float, dict[str, Any]]] = []
        requested_act = where.get("act") if where else None
        requested_section = where.get("section") if where else None

        for chunk in chunks:
            metadata = chunk["metadata"]
            if requested_act and metadata.get("act") != requested_act:
                continue
            if requested_section and str(metadata.get("section")) != str(requested_section):
                continue

            doc_tokens = chunk["tokens"]
            overlap = query_tokens & doc_tokens
            if not overlap:
                continue

            # Weighted Jaccard-like score that rewards exact legal section mentions.
            lexical = len(overlap) / math.sqrt(max(len(query_tokens), 1) * max(len(doc_tokens), 1))
            section_bonus = 0.0
            section = str(metadata.get("section", ""))
            if section and section in query_tokens:
                section_bonus += 0.25
            if "section" in query_tokens and section:
                section_bonus += 0.05
            similarity = round(min(0.99, lexical + section_bonus), 4)

            if similarity >= min_similarity or len(scored) < n_results * 3:
                scored.append((similarity, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        results = [
            {"text": item["text"], "metadata": item["metadata"], "similarity": score}
            for score, item in scored[:n_results]
        ]

        if not results:
            return self._mock_results(query_text)[:n_results]

        logger.info("RAG local fallback returned %s chunks for: %s...", len(results), query_text[:80])
        return results

    def _chunk_by_section(self, text: str, act_name: str, filename: str) -> tuple[list[str], list[dict]]:
        """
        Section-aware chunking for BNS-style legal documents.

        Splits on `--- Section N ---` markers, then sub-chunks sections that exceed
        max_chunk_size. Each chunk preserves section number and act metadata.
        """
        max_chunk_size = 1800
        sub_chunk_size = 1000
        sub_chunk_overlap = 150

        parts = _SECTION_SPLIT_RE.split(text)
        chunks: list[str] = []
        metas: list[dict] = []

        preamble = parts[0].strip()
        if preamble and len(preamble) > 50:
            chunks.append(preamble)
            metas.append({"source": filename, "act": act_name, "section": "preamble", "chunk_index": 0})

        for i in range(1, len(parts) - 1, 2):
            section_num = parts[i].strip()
            section_text = parts[i + 1].strip()
            if not section_text:
                continue

            full_section = f"Section {section_num}. {section_text}"
            if len(full_section) <= max_chunk_size:
                chunks.append(full_section)
                metas.append({
                    "source": filename,
                    "act": act_name,
                    "section": section_num,
                    "chunk_index": len(chunks) - 1,
                })
            else:
                for j, sub_chunk in enumerate(self._chunk_text(full_section, sub_chunk_size, sub_chunk_overlap)):
                    chunks.append(sub_chunk)
                    metas.append({
                        "source": filename,
                        "act": act_name,
                        "section": section_num,
                        "sub_chunk": j,
                        "chunk_index": len(chunks) - 1,
                    })

        logger.info(
            "Section-aware chunking: %s chunks from %s sections in %s",
            len(chunks),
            (len(parts) - 1) // 2,
            filename,
        )
        return chunks, metas

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """Split text into overlapping chunks by character count."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be non-negative and smaller than chunk_size")

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == len(text):
                break
            start = end - overlap
        return chunks

    def _mock_results(self, query_text: str) -> list[dict[str, Any]]:
        """Last-resort mock results when no corpus is available."""
        mock_db = [
            {
                "text": (
                    "Section 303. Theft — Whoever, intending to take dishonestly any movable "
                    "property out of the possession of any person without that person's consent, "
                    "moves that property in order to such taking, is said to commit theft."
                ),
                "metadata": {"source": "fallback", "act": "bns_2023", "section": "303"},
                "similarity": 0.85,
            },
            {
                "text": (
                    "Section 304. Snatching — Whoever commits theft by snatching any movable "
                    "property from any person shall be punished with imprisonment and fine."
                ),
                "metadata": {"source": "fallback", "act": "bns_2023", "section": "304"},
                "similarity": 0.78,
            },
            {
                "text": "Section 101. Murder — Culpable homicide is murder in specified circumstances.",
                "metadata": {"source": "fallback", "act": "bns_2023", "section": "101"},
                "similarity": 0.72,
            },
        ]

        query_lower = query_text.lower()
        scored = []
        for item in mock_db:
            score = sum(1 for word in query_lower.split() if word in item["text"].lower())
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored] or mock_db[:2]

    async def get_stats(self) -> dict[str, Any]:
        """Get collection statistics and fallback status."""
        collection = self._get_client()
        fallback_chunks = len(_load_local_chunks(str(self._resolve_corpus_path(None))))
        if collection is None:
            return {
                "status": "fallback",
                "using_mock": fallback_chunks == 0,
                "local_corpus_chunks": fallback_chunks,
                "corpus_path": str(self._resolve_corpus_path(None)),
            }
        try:
            count = collection.count()
            return {
                "status": "connected",
                "collection": self._settings.chroma.collection_name,
                "count": count,
                "using_mock": False,
                "local_corpus_chunks": fallback_chunks,
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "local_corpus_chunks": fallback_chunks}
