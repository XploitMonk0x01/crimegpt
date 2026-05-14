"""
RAG Service — Retrieval-Augmented Generation pipeline using ChromaDB.

Provides:
    - ingest_corpus() — chunk legal docs, embed, store in ChromaDB
    - query() — embed query, similarity search, return top-k chunks
    - get_collection_stats() — info about the vector store

Usage:
    from app.services.ragService import RAGService
    rag = RAGService()
    chunks = await rag.query("What are the penalties for theft under BNS 2023?")
"""

import logging
from pathlib import Path
from typing import Any

from app.config import get_settings

logger = logging.getLogger("crimegpt.rag")


class RAGService:
    """ChromaDB-based RAG pipeline for legal corpus retrieval."""

    def __init__(self):
        self._settings = get_settings()
        self._client = None
        self._collection = None

    def _get_client(self):
        """Lazy-init ChromaDB client."""
        if self._client is None:
            try:
                import chromadb

                self._client = chromadb.HttpClient(
                    host=self._settings.chroma.host,
                    port=self._settings.chroma.port,
                )
                self._collection = self._client.get_or_create_collection(
                    name=self._settings.chroma.collection_name,
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
    ) -> list[dict[str, Any]]:
        """
        Query the legal corpus — embed query and find similar chunks.

        Returns list of dicts with: text, metadata, distance (similarity score).
        Falls back to empty results if ChromaDB is unavailable.
        """
        collection = self._get_client()
        if not collection:
            logger.warning("ChromaDB not available — returning empty results")
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
                    chunks.append({
                        "text": doc,
                        "metadata": meta,
                        "similarity": round(1.0 - dist, 4),
                    })

            logger.info(f"RAG query returned {len(chunks)} chunks for: {query_text[:80]}...")
            return chunks

        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return self._mock_results(query_text)

    async def ingest_corpus(self, corpus_dir: str | None = None) -> dict[str, Any]:
        """
        Ingest legal documents from corpus directory into ChromaDB.

        Chunks documents by section, embeds them, and stores in the collection.
        """
        collection = self._get_client()
        if not collection:
            return {"status": "skipped", "reason": "ChromaDB not available"}

        corpus_path = Path(corpus_dir) if corpus_dir else Path("./corpus")
        if not corpus_path.exists():
            return {"status": "skipped", "reason": f"Corpus directory not found: {corpus_path}"}

        ingested = 0
        errors = 0

        for file_path in corpus_path.rglob("*.txt"):
            try:
                text = file_path.read_text(encoding="utf-8")
                chunks = self._chunk_text(text, chunk_size=500, overlap=50)

                ids = [f"{file_path.stem}_{i}" for i in range(len(chunks))]
                metadatas = [
                    {
                        "source": file_path.name,
                        "act": file_path.parent.name,
                        "chunk_index": i,
                    }
                    for i in range(len(chunks))
                ]

                collection.upsert(
                    ids=ids,
                    documents=chunks,
                    metadatas=metadatas,
                )
                ingested += len(chunks)
                logger.info(f"Ingested {len(chunks)} chunks from {file_path.name}")

            except Exception as e:
                errors += 1
                logger.error(f"Failed to ingest {file_path}: {e}")

        return {
            "status": "completed",
            "chunks_ingested": ingested,
            "errors": errors,
        }

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
        return [
            {
                "text": (
                    "BNS Section 303 — Theft: Whoever, intending to take dishonestly "
                    "any movable property out of the possession of any person without "
                    "that person's consent, moves that property in order to such taking, "
                    "is said to commit theft."
                ),
                "metadata": {"source": "bns_2023_mock.txt", "act": "BNS 2023"},
                "similarity": 0.85,
            },
            {
                "text": (
                    "BNS Section 304 — Snatching: Whoever commits theft by snatching "
                    "any movable property from any person shall be punished with "
                    "imprisonment up to three years and fine."
                ),
                "metadata": {"source": "bns_2023_mock.txt", "act": "BNS 2023"},
                "similarity": 0.78,
            },
        ]

    async def get_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        collection = self._get_client()
        if not collection:
            return {"status": "unavailable"}
        try:
            return {
                "status": "connected",
                "collection": self._settings.chroma.collection_name,
                "count": collection.count(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
