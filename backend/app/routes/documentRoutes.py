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


@router.get("/{fir_id}/versions", summary="List Document Versions")
async def list_document_versions(
    fir_id: uuid.UUID,
    document_type: DocumentType = Query(..., description="Document type"),
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List stored versions for a FIR and document type."""
    service = DocumentService(db)
    versions = await service.list_versions(fir_id=fir_id, document_type=document_type)
    return {
        "success": True,
        "data": [
            {
                "id": str(v.id),
                "fir_id": str(v.fir_id),
                "document_type": v.document_type,
                "version_no": v.version_no,
                "title": v.title,
                "metadata": v.metadata,
                "changed_by": str(v.changed_by),
                "changed_at": v.changed_at.isoformat(),
            }
            for v in versions
        ],
    }


@router.get("/versions/{version_id}", summary="Get Document Version")
async def get_document_version(
    version_id: uuid.UUID,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get one stored document version snapshot."""
    service = DocumentService(db)
    version = await service.get_version(version_id=version_id)
    return {
        "success": True,
        "data": {
            "id": str(version.id),
            "fir_id": str(version.fir_id),
            "document_type": version.document_type,
            "version_no": version.version_no,
            "title": version.title,
            "content": version.content,
            "metadata": version.metadata,
            "changed_by": str(version.changed_by),
            "changed_at": version.changed_at.isoformat(),
        },
    }
