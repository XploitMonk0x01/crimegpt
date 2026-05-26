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

import asyncio
import hashlib
import logging
import math
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.schemas.rag_schema import RAGUrlIngestRequest, RAGUrlIngestResult
from app.services.ragSafety import analyze_text, redact_pii, strip_prompt_injection
from app.utils.text_extraction import extract_text_from_html, normalize_whitespace
from app.utils.hybrid_retrieval import hybrid_rerank, sentence_boundary_chunk
from app.services.ragCache import RAGCache

logger = logging.getLogger("crimegpt.rag")

_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")
_SECTION_SPLIT_RE = re.compile(r"--- Section ([0-9A-Za-z-]+) ---")


class FastEmbedEmbeddingFunction:
    """Custom embedding function using FastEmbed for ChromaDB embeddings."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        try:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(model_name=model_name)
            self._model_name = model_name
        except ImportError:
            logger.warning("fastembed not installed; local embedding function disabled.")
            self._model = None
            self._model_name = model_name

    @property
    def name(self) -> str:
        """Return the embedding function name for ChromaDB v2 compatibility."""
        return f"fastembed_{self._model_name.split('/')[-1]}"

    def __call__(self, input: list[str]) -> list[list[float]]:
        if not self._model:
            return [[0.0] * 384] * len(input)  # Return dummy embeddings if model missing
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
        self._rag_settings = self._settings.rag
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

                # Use ChromaDB's default embedding function for v2 compatibility
                self._collection = self._client.get_or_create_collection(
                    name=self._settings.chroma.collection_name,
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
        rerank: bool = True,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Query the legal corpus and return top matching chunks.

        Pipeline:
        0. Check Redis retrieval cache (key = SHA-256 of query + act_filter)
        1. Retrieve n_results * 3 candidates (over-fetch for reranking)
        2. Apply hybrid BM25 + semantic reranking (Reciprocal Rank Fusion)
        3. Apply relevance threshold cutoff
        4. Store results in Redis cache, return top n_results

        ChromaDB is preferred. Falls back to local lexical search automatically.
        """
        act_filter = (where or {}).get("act", "")

        # ── Layer 0: Cache check ──
        if use_cache:
            cache = RAGCache()
            cached = await cache.get_chunks(query_text, act_filter)
            if cached is not None:
                return cached[:n_results]

        # Over-fetch candidates for reranking
        fetch_n = n_results * 3 if rerank else n_results

        collection = self._get_client()
        if collection is None:
            raw = self._query_local_corpus(
                query_text,
                n_results=fetch_n,
                where=where,
                min_similarity=min_similarity * 0.5,  # lower threshold before rerank
            )
            result = self._apply_rerank(raw, query_text, n_results=n_results,
                                         min_similarity=min_similarity, rerank=rerank)
            if use_cache and result:
                await RAGCache().set_chunks(query_text, act_filter, result)
            return result

        try:
            kwargs: dict[str, Any] = {
                "query_texts": [query_text],
                "n_results": max(fetch_n, 1),
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
                    # Chroma returns cosine distance (0=identical, 1=orthogonal)
                    similarity = round(max(0.0, 1.0 - float(dist)), 4)
                    chunks.append({"text": doc, "metadata": meta or {}, "similarity": similarity})

            result = self._apply_rerank(chunks, query_text, n_results=n_results,
                                         min_similarity=min_similarity, rerank=rerank)
            if use_cache and result:
                await RAGCache().set_chunks(query_text, act_filter, result)
            return result

        except Exception as e:
            logger.error("RAG query error; using local corpus fallback: %s", e)
            raw = self._query_local_corpus(
                query_text,
                n_results=fetch_n,
                where=where,
                min_similarity=min_similarity * 0.5,
            )
            result = self._apply_rerank(raw, query_text, n_results=n_results,
                                         min_similarity=min_similarity, rerank=rerank)
            if use_cache and result:
                await RAGCache().set_chunks(query_text, act_filter, result)
            return result

    def _apply_rerank(
        self,
        chunks: list[dict[str, Any]],
        query: str,
        *,
        n_results: int,
        min_similarity: float,
        rerank: bool,
    ) -> list[dict[str, Any]]:
        """Apply hybrid BM25+semantic reranking then enforce relevance threshold."""
        if not chunks:
            return chunks

        if rerank and len(chunks) > 1:
            chunks = hybrid_rerank(chunks, query)
            score_key = "hybrid_score"
        else:
            score_key = "similarity"

        # Relevance threshold cutoff — filter low-confidence chunks
        filtered = [c for c in chunks if c.get(score_key, 0) >= min_similarity]

        # Gracefully fall back to top-N if threshold removes everything
        if not filtered:
            logger.warning(
                "All %s chunks below threshold %.2f; returning top-%s unfiltered",
                len(chunks), min_similarity, min(n_results, len(chunks)),
            )
            filtered = chunks[:n_results]

        result = filtered[:n_results]
        logger.info(
            "RAG returned %s/%s chunks (rerank=%s, threshold=%.2f) for: %s...",
            len(result), len(chunks), rerank, min_similarity, query[:60],
        )
        return result

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

    async def ingest_urls(self, request: RAGUrlIngestRequest) -> dict[str, Any]:
        """Ingest public/legal URLs into ChromaDB for RAG."""
        collection = self._get_client()
        if collection is None:
            return {
                "status": "skipped",
                "reason": "ChromaDB not available; local corpus fallback is active",
            }

        timeout = httpx.Timeout(self._rag_settings.request_timeout_seconds)
        headers = {"User-Agent": self._rag_settings.user_agent}
        min_text_length = request.min_text_length or self._rag_settings.min_text_length

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            semaphore = asyncio.Semaphore(max(1, self._rag_settings.max_concurrency))

            async def _run(item):
                async with semaphore:
                    try:
                        return await self._ingest_url_item(
                            item=item,
                            client=client,
                            collection=collection,
                            chunk_size=request.chunk_size,
                            overlap=request.overlap,
                            min_text_length=min_text_length,
                        )
                    except Exception as exc:
                        logger.exception("URL ingest failed for %s", getattr(item, "url", "unknown"))
                        return RAGUrlIngestResult(url=str(item.url), status="error", reason=str(exc))

            results: list[RAGUrlIngestResult] = list(await asyncio.gather(*[_run(item) for item in request.urls]))

        summary = {
            "status": "completed",
            "ingested": sum(1 for r in results if r.status == "ingested"),
            "skipped": sum(1 for r in results if r.status == "skipped"),
            "errors": sum(1 for r in results if r.status == "error"),
            "results": [r.model_dump() for r in results],
        }
        return summary

    def _resolve_corpus_path(self, corpus_dir: str | None = None) -> Path:
        if corpus_dir:
            path = Path(corpus_dir)
            if path.exists():
                return path
            backend_relative = Path(__file__).resolve().parents[2] / corpus_dir
            if backend_relative.exists():
                return backend_relative
        return _default_corpus_dir()

    async def _ingest_url_item(
        self,
        *,
        item,
        client: httpx.AsyncClient,
        collection,
        chunk_size: int,
        overlap: int,
        min_text_length: int,
    ) -> RAGUrlIngestResult:
        url = str(item.url)
        if not self._is_url_allowed(url):
            return RAGUrlIngestResult(url=url, status="skipped", reason="URL domain not allowed")

        try:
            content, content_type = await self._fetch_url_content(url, client)
        except (httpx.HTTPError, ValueError) as exc:
            return RAGUrlIngestResult(url=url, status="error", reason=str(exc))

        text = self._extract_text(content, content_type)
        if len(text) < min_text_length:
            return RAGUrlIngestResult(
                url=url,
                status="skipped",
                reason=f"Extracted text too short ({len(text)} chars)",
            )

        signals = analyze_text(text)
        if self._rag_settings.redact_pii:
            text = redact_pii(text)
        stripped_lines = 0
        if self._rag_settings.strip_prompt_injection:
            text, stripped_lines = strip_prompt_injection(text)

        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        existing = collection.get(where={"content_hash": content_hash})
        if existing and existing.get("ids"):
            return RAGUrlIngestResult(url=url, status="skipped", reason="Duplicate content", content_hash=content_hash)

        chunks = self._chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            return RAGUrlIngestResult(url=url, status="skipped", reason="No chunks generated")

        now = datetime.now(timezone.utc).isoformat()
        safe_source = re.sub(r"[^a-zA-Z0-9_-]+", "_", urlparse(url).netloc or "source")
        ids = [f"url_{safe_source}_{content_hash[:12]}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": item.title or url,
                "source_type": "url",
                "url": url,
                "act": item.act or "unknown",
                "tags": item.tags,
                "content_hash": content_hash,
                "ingested_at": now,
                "chunk_index": i,
                "prompt_injection": signals.prompt_injection,
                "pii_matches": signals.pii_matches,
                "prompt_injection_stripped": stripped_lines,
            }
            for i in range(len(chunks))
        ]

        batch_size = 100
        for start in range(0, len(chunks), batch_size):
            end = start + batch_size
            collection.upsert(
                ids=ids[start:end],
                documents=chunks[start:end],
                metadatas=metadatas[start:end],
            )

        logger.info("Ingested %s chunks from URL %s", len(chunks), url)
        return RAGUrlIngestResult(url=url, status="ingested", chunks=len(chunks), content_hash=content_hash)

    def _is_url_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in ("https", "http"):
            return False
        if parsed.scheme == "http" and not self._rag_settings.allow_http_urls:
            return False
        host = (parsed.hostname or "").lower()
        allowed = [domain.strip().lower() for domain in self._rag_settings.allowed_url_domains if domain.strip()]
        if not allowed:
            return True
        return any(host == domain or host.endswith(f".{domain}") for domain in allowed)

    async def _fetch_url_content(
        self, url: str, client: httpx.AsyncClient
    ) -> tuple[str, str | None]:
        max_bytes = self._rag_settings.max_url_bytes
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            final_url = str(response.url)
            if not self._is_url_allowed(final_url):
                raise ValueError(f"Redirected URL not allowed: {final_url}")
            content_type = response.headers.get("content-type")
            if content_type and not content_type.startswith("text/") and "html" not in content_type:
                raise ValueError(f"Unsupported content-type: {content_type}")

            body = bytearray()
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body) > max_bytes:
                    raise ValueError(f"Content exceeds max size ({max_bytes} bytes)")

        try:
            content = body.decode("utf-8", errors="ignore")
        except UnicodeDecodeError as exc:
            raise ValueError("Failed to decode response body as UTF-8") from exc

        return content, content_type

    def _extract_text(self, content: str, content_type: str | None) -> str:
        if content_type and "html" in content_type:
            return extract_text_from_html(content)
        return normalize_whitespace(content)

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

    def _chunk_text(self, text: str, chunk_size: int = 900, overlap: int = 50) -> list[str]:
        """
        Sentence-boundary aware chunking (primary) with character fallback.

        Prefers splitting at sentence boundaries to preserve context.
        Falls back to character-based splitting for very long texts without
        sentence breaks (e.g. dense legal tables).
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        # Try sentence-boundary chunking first
        sent_chunks = sentence_boundary_chunk(
            text,
            target_size=chunk_size,
            overlap_sentences=2,
        )
        if sent_chunks:
            return sent_chunks

        # Fallback: character-based splitting
        if overlap < 0 or overlap >= chunk_size:
            overlap = min(50, chunk_size // 5)
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
