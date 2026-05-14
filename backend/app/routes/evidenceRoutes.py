"""
Evidence Manager routes — upload, custody chain, integrity verification.
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.officer import Officer
from app.services.evidenceService import EvidenceService

router = APIRouter()


@router.post("/upload", summary="Upload Evidence")
async def upload_evidence(
    file: UploadFile = File(...),
    fir_id: uuid.UUID = Form(...),
    description: str = Form(default=""),
    request: Request = None,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request and request.client else "unknown"
    service = EvidenceService(db)
    result = await service.upload(file, fir_id, officer, description=description, ip_address=ip)
    return {"success": True, "data": result, "message": "Evidence uploaded"}


@router.get("/{evidence_id}/custody", summary="Evidence Custody Chain")
async def get_custody(
    evidence_id: uuid.UUID,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvidenceService(db)
    result = await service.get_custody_chain(evidence_id, officer)
    return {"success": True, "data": result}


@router.get("/{evidence_id}/verify", summary="Verify Evidence Integrity")
async def verify_evidence(
    evidence_id: uuid.UUID,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvidenceService(db)
    result = await service.verify_integrity(evidence_id, officer)
    return {"success": True, "data": result}
