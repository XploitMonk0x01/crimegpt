"""
RAG ingestion schemas (Pydantic v2).
"""

from __future__ import annotations

from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field


class RAGUrlIngestItem(BaseModel):
    """Single URL source to ingest into the RAG corpus."""

    url: AnyHttpUrl
    act: str | None = Field(default=None, description="Legal act/category tag (optional)")
    title: str | None = Field(default=None, description="Optional source title override")
    tags: list[str] = Field(default_factory=list, description="Optional source tags")


class RAGUrlIngestRequest(BaseModel):
    """Batch URL ingestion request."""

    urls: list[RAGUrlIngestItem] = Field(..., min_length=1, max_length=200)
    chunk_size: int = Field(default=900, ge=200, le=4000)
    overlap: int = Field(default=120, ge=0, le=1000)
    min_text_length: int | None = Field(default=None, ge=200)


class RAGUrlIngestResult(BaseModel):
    """Per-URL ingestion result."""

    url: str
    status: Literal["ingested", "skipped", "error"]
    reason: str | None = None
    chunks: int | None = None
    content_hash: str | None = None
