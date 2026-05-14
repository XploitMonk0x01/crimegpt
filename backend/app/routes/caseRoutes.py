"""
Case Linkage routes — similar case detection and formal linking.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_role
from app.models.officer import Officer
from app.services.caseService import CaseService
from app.types.enums import OfficerRole

router = APIRouter()


class LinkCasesRequest(BaseModel):
    fir_id_a: uuid.UUID
    fir_id_b: uuid.UUID
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    link_reason: str = Field(default="", max_length=2000)


@router.get("/similar/{fir_id}", summary="Find Similar Cases")
async def find_similar(
    fir_id: uuid.UUID,
    threshold: float = Query(default=0.70, ge=0.0, le=1.0),
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    result = await service.find_similar_cases(fir_id, officer, threshold=threshold)
    return {"success": True, "data": result}


@router.post(
    "/link",
    summary="Link Cases",
    dependencies=[Depends(require_role(OfficerRole.INSPECTOR, OfficerRole.STATION_HEAD, OfficerRole.ADMIN))],
)
async def link_cases(
    body: LinkCasesRequest,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    result = await service.link_cases(
        body.fir_id_a, body.fir_id_b, officer,
        similarity_score=body.similarity_score,
        link_reason=body.link_reason,
    )
    return {"success": True, "data": result, "message": "Cases linked"}


@router.get("/clusters", summary="MO Cluster Analysis")
async def get_clusters(
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    result = await service.get_clusters(officer)
    return {"success": True, "data": result}
