"""
Document Generation routes — auto-generate legal documents from FIR data.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.officer import Officer
from app.schemas.document_schema import DocumentGenerateRequest, DocumentExportPdfRequest
from app.services.documentService import DocumentService
from app.types.enums import DocumentType

router = APIRouter()


@router.get("/types", summary="List Document Types")
async def list_document_types(
    officer: Officer = Depends(get_current_user),
):
    """Get all available document types and their descriptions."""
    types = DocumentService.get_available_types()
    return {"success": True, "data": types}


@router.post("/generate", summary="Generate Legal Document")
async def generate_document(
    body: DocumentGenerateRequest,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a legal document from FIR data using AI."""
    service = DocumentService(db)
    result = await service.generate_document(
        fir_id=body.fir_id,
        document_type=body.document_type,
        officer=officer,
        language=body.language,
        additional_context=body.additional_context,
    )
    return {"success": True, "data": result}


@router.post("/export-pdf", summary="Export Document as PDF")
async def export_pdf(
    body: DocumentExportPdfRequest,
    officer: Officer = Depends(get_current_user),
):
    """Export a generated document as downloadable PDF."""
    from app.services.pdfService import PDFService

    pdf_service = PDFService()
    pdf_bytes = pdf_service.generate_pdf(
        title=body.title,
        content=body.content,
        document_type=body.document_type.value,
        fir_number=body.fir_number,
        metadata=body.metadata,
    )

    from fastapi.responses import Response

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{body.document_type.value}_{body.fir_number or "doc"}.pdf"'
        },
    )
