"""
Case Diary routes — timeline-based investigation diary.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_role
from app.models.officer import Officer
from app.services.caseDiaryService import CaseDiaryService
from app.types.enums import CaseDiaryEntryType, OfficerRole

router = APIRouter()


class AddDiaryEntryRequest(BaseModel):
    entry_type: CaseDiaryEntryType = Field(
        default=CaseDiaryEntryType.OTHER,
        description="Type of investigative action",
    )
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    entry_date: datetime | None = Field(
        default=None,
        description="When the action took place (defaults to now)",
    )


@router.get("/types", summary="List Diary Entry Types")
async def list_entry_types(
    officer: Officer = Depends(get_current_user),
):
    """Get all available diary entry types."""
    types = CaseDiaryService.get_entry_types()
    return {"success": True, "data": types}


@router.post("/{fir_id}/entry", summary="Add Diary Entry")
async def add_entry(
    fir_id: uuid.UUID,
    body: AddDiaryEntryRequest,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new entry to a case diary."""
    service = CaseDiaryService(db)
    result = await service.add_entry(
        fir_id=fir_id,
        officer=officer,
        entry_type=body.entry_type,
        title=body.title,
        description=body.description,
        entry_date=body.entry_date,
    )
    return {"success": True, "data": result, "message": "Diary entry added"}


@router.get("/{fir_id}", summary="Get Case Diary")
async def get_diary(
    fir_id: uuid.UUID,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the full case diary timeline for a FIR."""
    service = CaseDiaryService(db)
    result = await service.get_diary(fir_id, officer)
    return {"success": True, "data": result}


@router.delete(
    "/entry/{entry_id}",
    summary="Delete Diary Entry",
    dependencies=[Depends(require_role(OfficerRole.INSPECTOR, OfficerRole.STATION_HEAD, OfficerRole.ADMIN))],
)
async def delete_entry(
    entry_id: uuid.UUID,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a diary entry. Inspector+ only."""
    service = CaseDiaryService(db)
    result = await service.delete_entry(entry_id, officer)
    return {"success": True, "data": result}
