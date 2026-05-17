"""
Document Generation validation schemas (Pydantic v2).

Request/response models for the auto-generated legal documents
(Chargesheet, Medical Letter, Remand Request, Seizure Receipt, etc.).
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.types.enums import DocumentType


# ───────────────── Request Schemas ─────────────────


class DocumentGenerateRequest(BaseModel):
    """Request to generate a legal document from an existing FIR."""

    fir_id: uuid.UUID = Field(
        ...,
        description="UUID of the FIR to generate the document from",
    )
    document_type: DocumentType = Field(
        ...,
        description="Type of legal document to generate",
    )
    language: str = Field(
        default="en",
        description="Output language (en/hi/gu)",
    )
    additional_context: str | None = Field(
        default=None,
        max_length=5000,
        description="Additional officer notes or context for the document",
    )


class DocumentExportPdfRequest(BaseModel):
    """Request to export a generated document as PDF."""

    document_type: DocumentType
    title: str
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    fir_number: str | None = None


# ───────────────── Response Schemas ─────────────────


class DocumentTypeInfo(BaseModel):
    """Info about a single document type."""

    type: DocumentType
    label: str
    description: str
    icon: str = ""


class DocumentGenerateResponse(BaseModel):
    """Response from document generation."""

    document_type: DocumentType
    title: str
    content: str
    fir_id: uuid.UUID
    fir_number: str | None = None
    sections_used: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime
    language: str = "en"


class DocumentTypesResponse(BaseModel):
    """List of available document types."""

    types: list[DocumentTypeInfo]
