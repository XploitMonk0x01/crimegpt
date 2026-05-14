"""
Dashboard routes — role-based analytics and overview.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_role
from app.models.officer import Officer
from app.services.dashboardService import DashboardService
from app.types.enums import OfficerRole

router = APIRouter()


@router.get("/officer", summary="Officer Dashboard")
async def officer_dashboard(
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    result = await service.get_officer_dashboard(officer)
    return {"success": True, "data": result}


@router.get(
    "/inspector",
    summary="Inspector Dashboard",
    dependencies=[Depends(require_role(OfficerRole.INSPECTOR, OfficerRole.STATION_HEAD, OfficerRole.ADMIN))],
)
async def inspector_dashboard(
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    result = await service.get_inspector_dashboard(officer)
    return {"success": True, "data": result}


@router.get(
    "/audit-logs",
    summary="Audit Logs",
    dependencies=[Depends(require_role(OfficerRole.STATION_HEAD, OfficerRole.ADMIN))],
)
async def audit_logs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    result = await service.get_audit_logs(offset=offset, limit=limit)
    return {"success": True, "data": result}


@router.get("/analytics", summary="Crime Analytics")
async def analytics(
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    result = await service.get_analytics()
    return {"success": True, "data": result}
