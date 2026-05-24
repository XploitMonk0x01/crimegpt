"""
RAG Query Cache — Redis-backed semantic response cache.

Caches two layers:
  1. LLM answer cache  — keyed by (query_hash + act_filter), TTL: 1 hour
  2. Retrieval cache   — keyed by (query_hash + act_filter), TTL: 6 hours

Design decisions:
  - Keys are SHA-256 of normalized query + filter so minor whitespace differences
    don't break cache hits.
  - Serializes with json (no pickle) for safety and cross-process compatibility.
  - Fails silently on every Redis error so the pipeline never breaks when Redis
    is down.
  - Separate TTLs: retrieval chunks are cheaper to refresh, answers stay longer.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from app.db.redis_db import redis_client

logger = logging.getLogger("crimegpt.rag_cache")

# TTL constants
_ANSWER_TTL = 60 * 60          # 1 hour
_RETRIEVAL_TTL = 60 * 60 * 6  # 6 hours

_KEY_PREFIX = "rag"


def _make_key(namespace: str, query: str, extra: str = "") -> str:
    """Stable cache key: rag:{namespace}:{sha256(query+extra)[:16]}"""
    raw = f"{query.strip().lower()}|{extra}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{_KEY_PREFIX}:{namespace}:{digest}"


class RAGCache:
    """
    Two-layer Redis cache for the RAG pipeline.

    Usage:
        cache = RAGCache()

        # Retrieval layer
        chunks = await cache.get_chunks(query, act_filter)
        if chunks is None:
            chunks = await rag.query(...)
            await cache.set_chunks(query, act_filter, chunks)

        # Answer layer
        answer = await cache.get_answer(query, act_filter, language)
        if answer is None:
            answer = await llm.generate(...)
            await cache.set_answer(query, act_filter, language, answer)
    """

    # ─── Retrieval chunk cache ───────────────────────────────────────────

    async def get_chunks(
        self,
        query: str,
        act_filter: str = "",
    ) -> list[dict[str, Any]] | None:
        """Return cached retrieval chunks or None on miss."""
        key = _make_key("chunks", query, act_filter)
        try:
            raw = await redis_client.get(key)
            if raw:
                logger.debug("RAG chunk cache HIT for key %s", key)
                return json.loads(raw)
        except Exception as exc:
            logger.warning("RAG chunk cache GET failed (ignored): %s", exc)
        return None

    async def set_chunks(
        self,
        query: str,
        act_filter: str = "",
        chunks: list[dict[str, Any]] = None,
    ) -> None:
        """Store retrieval chunks in cache."""
        if not chunks:
            return
        key = _make_key("chunks", query, act_filter)
        try:
            await redis_client.setex(key, _RETRIEVAL_TTL, json.dumps(chunks))
            logger.debug("RAG chunk cache SET: %s chunks → key %s (TTL=%ds)", len(chunks), key, _RETRIEVAL_TTL)
        except Exception as exc:
            logger.warning("RAG chunk cache SET failed (ignored): %s", exc)

    # ─── Answer cache ────────────────────────────────────────────────────

    async def get_answer(
        self,
        query: str,
        act_filter: str = "",
        language: str = "en",
    ) -> dict[str, Any] | None:
        """Return a full cached answer dict or None on miss."""
        key = _make_key("answer", query, f"{act_filter}|{language}")
        try:
            raw = await redis_client.get(key)
            if raw:
                logger.info("RAG answer cache HIT for: %s...", query[:60])
                return json.loads(raw)
        except Exception as exc:
            logger.warning("RAG answer cache GET failed (ignored): %s", exc)
        return None

    async def set_answer(
        self,
        query: str,
        act_filter: str = "",
        language: str = "en",
        answer: dict[str, Any] = None,
    ) -> None:
        """Store a full answer dict in cache."""
        if not answer:
            return
        key = _make_key("answer", query, f"{act_filter}|{language}")
        try:
            await redis_client.setex(key, _ANSWER_TTL, json.dumps(answer))
            logger.info("RAG answer cache SET → key %s (TTL=%ds)", key, _ANSWER_TTL)
        except Exception as exc:
            logger.warning("RAG answer cache SET failed (ignored): %s", exc)

    # ─── Cache management ────────────────────────────────────────────────

    async def invalidate_query(self, query: str, act_filter: str = "", language: str = "en") -> None:
        """Invalidate both cache layers for a specific query."""
        keys = [
            _make_key("chunks", query, act_filter),
            _make_key("answer", query, f"{act_filter}|{language}"),
        ]
        try:
            await redis_client.delete(*keys)
            logger.debug("RAG cache invalidated %s keys", len(keys))
        except Exception as exc:
            logger.warning("RAG cache invalidate failed (ignored): %s", exc)

    async def flush_all(self) -> int:
        """Flush all RAG cache keys. Returns count of deleted keys."""
        try:
            keys = await redis_client.keys(f"{_KEY_PREFIX}:*")
            if keys:
                count = await redis_client.delete(*keys)
                logger.info("RAG cache flushed: %s keys deleted", count)
                return count
        except Exception as exc:
            logger.warning("RAG cache flush failed (ignored): %s", exc)
        return 0

    async def stats(self) -> dict[str, Any]:
        """Return cache key counts by namespace."""
        try:
            chunk_keys = await redis_client.keys(f"{_KEY_PREFIX}:chunks:*")
            answer_keys = await redis_client.keys(f"{_KEY_PREFIX}:answer:*")
            return {
                "chunk_keys": len(chunk_keys),
                "answer_keys": len(answer_keys),
                "total_keys": len(chunk_keys) + len(answer_keys),
                "chunk_ttl_seconds": _RETRIEVAL_TTL,
                "answer_ttl_seconds": _ANSWER_TTL,
            }
        except Exception as exc:
            logger.warning("RAG cache stats failed (ignored): %s", exc)
            return {"error": str(exc)}
