"""
FIR routes — FastAPI router for FIR management endpoints.

Routes contain ZERO business logic.
"""

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.FIRController import FIRController
from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_role
from app.models.officer import Officer
from app.schemas.fir_schema import (
    FIRApproveRejectRequest,
    FIREditRequest,
    FIRGenerateRequest,
    FIRSubmitRequest,
)
from app.services.firService import FIRService
from app.types.enums import FIRStatus, OfficerRole

router = APIRouter()


def _get_fir_controller(db: AsyncSession = Depends(get_db)) -> FIRController:
    return FIRController(FIRService(db))


@router.post("/generate", summary="Generate AI FIR Draft")
async def generate_draft(
    body: FIRGenerateRequest,
    officer: Officer = Depends(get_current_user),
    controller: FIRController = Depends(_get_fir_controller),
):
    return await controller.generate_draft(body, officer)


@router.post("/submit", summary="Submit FIR")
async def submit_fir(
    body: FIRSubmitRequest,
    request: Request,
    officer: Officer = Depends(get_current_user),
    controller: FIRController = Depends(_get_fir_controller),
):
    return await controller.submit(body, officer, request)


@router.get("/list", summary="List FIRs")
async def list_firs(
    officer: Officer = Depends(get_current_user),
    controller: FIRController = Depends(_get_fir_controller),
    status: FIRStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return await controller.list_firs(officer, status, page, page_size)


@router.get("/{fir_id}", summary="Get FIR by ID")
async def get_fir(
    fir_id: uuid.UUID,
    officer: Officer = Depends(get_current_user),
    controller: FIRController = Depends(_get_fir_controller),
):
    return await controller.get_fir(fir_id, officer)


@router.patch("/{fir_id}/edit", summary="Edit Draft FIR")
async def edit_fir(
    fir_id: uuid.UUID,
    body: FIREditRequest,
    officer: Officer = Depends(get_current_user),
    controller: FIRController = Depends(_get_fir_controller),
):
    return await controller.edit(fir_id, body, officer)


@router.post(
    "/{fir_id}/review",
    summary="Approve/Reject FIR",
    dependencies=[Depends(require_role(OfficerRole.INSPECTOR, OfficerRole.STATION_HEAD, OfficerRole.ADMIN))],
)
async def approve_reject_fir(
    fir_id: uuid.UUID,
    body: FIRApproveRejectRequest,
    officer: Officer = Depends(get_current_user),
    controller: FIRController = Depends(_get_fir_controller),
):
    return await controller.approve_reject(fir_id, body, officer)
