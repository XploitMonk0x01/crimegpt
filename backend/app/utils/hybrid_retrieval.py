"""
Hybrid retrieval utilities — BM25 + vector Reciprocal Rank Fusion.

Provides zero-dependency BM25 scoring (no rank_bm25 package needed)
and RRF fusion to combine lexical + semantic rankings for better precision
on legal section queries like "BNS 302" or "POCSO 4".
"""

from __future__ import annotations

import math
import re
from typing import Any

_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")

# ─── BM25 constants (Okapi BM25) ───
_BM25_K1 = 1.5   # term frequency saturation
_BM25_B = 0.75   # length normalization weight
_RRF_K = 60      # RRF constant (higher = less penalty for lower ranks)


def tokenize(text: str) -> list[str]:
    """Simple whitespace + alphanumeric tokenizer."""
    return [t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 1]


class BM25:
    """
    Okapi BM25 scorer — pure Python, no dependencies.

    Usage:
        bm25 = BM25(corpus_texts)
        scores = bm25.score_all(query)
    """

    def __init__(self, corpus: list[str]):
        self._n = len(corpus)
        self._tokenized = [tokenize(doc) for doc in corpus]
        self._avgdl = sum(len(t) for t in self._tokenized) / max(self._n, 1)

        # Build inverted document-frequency index
        self._df: dict[str, int] = {}
        for tokens in self._tokenized:
            for term in set(tokens):
                self._df[term] = self._df.get(term, 0) + 1

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        return math.log((self._n - df + 0.5) / (df + 0.5) + 1)

    def score(self, query_tokens: list[str], doc_index: int) -> float:
        """Score a single document against query tokens."""
        tokens = self._tokenized[doc_index]
        dl = len(tokens)
        tf_map: dict[str, int] = {}
        for t in tokens:
            tf_map[t] = tf_map.get(t, 0) + 1

        score = 0.0
        for term in query_tokens:
            if term not in tf_map:
                continue
            tf = tf_map[term]
            idf = self._idf(term)
            norm = tf * (_BM25_K1 + 1) / (
                tf + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / max(self._avgdl, 1))
            )
            score += idf * norm
        return score

    def score_all(self, query: str) -> list[float]:
        """Return BM25 scores for all documents."""
        q_tokens = tokenize(query)
        if not q_tokens:
            return [0.0] * self._n
        return [self.score(q_tokens, i) for i in range(self._n)]


def reciprocal_rank_fusion(
    ranked_lists: list[list[int]],
    *,
    k: int = _RRF_K,
) -> list[tuple[int, float]]:
    """
    Combine multiple ranked lists (indices) using Reciprocal Rank Fusion.

    Returns: sorted list of (doc_index, rrf_score) descending.
    """
    scores: dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, doc_idx in enumerate(ranked):
            scores[doc_idx] = scores.get(doc_idx, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def hybrid_rerank(
    chunks: list[dict[str, Any]],
    query: str,
    *,
    semantic_weight: float = 0.6,
    bm25_weight: float = 0.4,
) -> list[dict[str, Any]]:
    """
    Rerank a list of RAG chunks using hybrid BM25 + semantic scores.

    Args:
        chunks: List of dicts with "text" and "similarity" keys.
        query: The original query string.
        semantic_weight: Weight for semantic (vector) similarity.
        bm25_weight: Weight for BM25 lexical score.

    Returns:
        Reranked chunks with updated "hybrid_score" field.
    """
    if not chunks:
        return chunks

    texts = [c["text"] for c in chunks]
    bm25 = BM25(texts)
    bm25_scores = bm25.score_all(query)

    # Normalize BM25 scores to [0, 1]
    max_bm25 = max(bm25_scores) if bm25_scores else 1.0
    if max_bm25 == 0:
        max_bm25 = 1.0
    norm_bm25 = [s / max_bm25 for s in bm25_scores]

    # Combine with semantic similarity
    scored = []
    for i, chunk in enumerate(chunks):
        semantic = float(chunk.get("similarity", 0.0))
        bm25_norm = norm_bm25[i]
        hybrid = round(semantic_weight * semantic + bm25_weight * bm25_norm, 4)
        scored.append({**chunk, "bm25_score": round(bm25_norm, 4), "hybrid_score": hybrid})

    return sorted(scored, key=lambda c: c["hybrid_score"], reverse=True)


def sentence_boundary_chunk(
    text: str,
    *,
    target_size: int = 900,
    overlap_sentences: int = 2,
) -> list[str]:
    """
    Sentence-boundary aware chunking.

    Splits text at sentence boundaries (. ! ?) respecting `target_size`
    and includes `overlap_sentences` sentences of context between chunks.

    Args:
        text: Input text to chunk.
        target_size: Target character size per chunk.
        overlap_sentences: Number of trailing sentences to repeat in next chunk.

    Returns:
        List of text chunks.
    """
    # Split into sentences
    sentence_re = re.compile(r"(?<=[.!?])\s+")
    sentences = [s.strip() for s in sentence_re.split(text) if s.strip()]

    if not sentences:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    i = 0
    while i < len(sentences):
        sent = sentences[i]
        if current_len + len(sent) > target_size and current:
            # Flush current chunk
            chunks.append(" ".join(current))
            # Keep overlap sentences for next chunk
            overlap = current[-overlap_sentences:] if overlap_sentences else []
            current = overlap[:]
            current_len = sum(len(s) for s in current)
        current.append(sent)
        current_len += len(sent)
        i += 1

    if current:
        chunks.append(" ".join(current))

    return chunks
