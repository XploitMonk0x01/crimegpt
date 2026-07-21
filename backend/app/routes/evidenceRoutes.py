"""
Evidence Manager routes — upload, custody chain, integrity verification.
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_role
from app.models.officer import Officer
from app.services.evidenceService import EvidenceService
from app.types.enums import OfficerRole

router = APIRouter()


@router.post("/upload", summary="Upload Evidence",
    dependencies=[Depends(require_role(OfficerRole.INSPECTOR, OfficerRole.STATION_HEAD, OfficerRole.ADMIN))],
)
async def upload_evidence(
    file: UploadFile = File(...),
    fir_id: uuid.UUID = Form(...),
    description: str = Form(default=""),
    tags: str = Form(default=""),
    request: Request = None,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request and request.client else "unknown"
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    service = EvidenceService(db)
    result = await service.upload(file, fir_id, officer, description=description, tags=tag_list, ip_address=ip)
    return {"success": True, "data": result, "message": "Evidence uploaded"}

@router.get("/fir/{fir_id}", summary="List Evidence for FIR")
async def list_evidence(
    fir_id: uuid.UUID,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvidenceService(db)
    result = await service.list_by_fir(fir_id)
    return {"success": True, "data": result}

@router.get("/{evidence_id}/download", summary="Download Evidence File")
async def download_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    # Depending on requirements, we could enforce authentication here.
    # Currently allowing download via UUID (since frontend <img> tags don't easily send auth headers).
    service = EvidenceService(db)
    file_path = await service.get_file(evidence_id)
    return FileResponse(path=file_path, filename=file_path.name)


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
