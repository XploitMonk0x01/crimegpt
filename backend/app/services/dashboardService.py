"""
Dashboard service — analytics and overview data.

Provides role-based dashboard views:
    - Officer: own FIRs, evidence, status counts
    - Inspector: station queue, pending approvals, case links
    - Station Head: audit logs, analytics, crime trends
"""

import logging
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fir import FIR
from app.models.evidence import Evidence
from app.models.audit_log import AuditLog
from app.models.case_link import CaseLink
from app.models.officer import Officer
from app.repositories.FIRRepository import FIRRepository
from app.repositories.AuditLogRepository import AuditLogRepository
from app.types.enums import FIRStatus

logger = logging.getLogger("crimegpt.dashboard")


class DashboardService:
    """Dashboard analytics and overview."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._fir_repo = FIRRepository(db)
        self._audit_repo = AuditLogRepository(db)

    async def get_officer_dashboard(self, officer: Officer) -> dict[str, Any]:
        """Dashboard for Constable — own FIRs and stats."""
        # FIR counts by status
        draft_count = await self._fir_repo.count_by_officer(officer.id, status=FIRStatus.DRAFT)
        submitted_count = await self._fir_repo.count_by_officer(officer.id, status=FIRStatus.SUBMITTED)
        approved_count = await self._fir_repo.count_by_officer(officer.id, status=FIRStatus.APPROVED)
        rejected_count = await self._fir_repo.count_by_officer(officer.id, status=FIRStatus.REJECTED)

        # Recent FIRs
        recent_firs = await self._fir_repo.list_by_officer(officer.id, limit=5)

        # Evidence count
        stmt = select(func.count()).select_from(Evidence).where(Evidence.officer_id == officer.id)
        result = await self._db.execute(stmt)
        evidence_count = result.scalar() or 0

        return {
            "officer": {
                "name": officer.name,
                "badge_no": officer.badge_no,
                "role": officer.role.value,
            },
            "fir_stats": {
                "draft": draft_count,
                "submitted": submitted_count,
                "approved": approved_count,
                "rejected": rejected_count,
                "total": draft_count + submitted_count + approved_count + rejected_count,
            },
            "evidence_count": evidence_count,
            "recent_firs": [
                {
                    "id": str(f.id),
                    "fir_number": f.fir_number,
                    "status": f.status.value if f.status else None,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                }
                for f in recent_firs
            ],
        }

    async def get_inspector_dashboard(self, officer: Officer) -> dict[str, Any]:
        """Dashboard for Inspector — pending approvals, station overview."""
        # Pending approvals
        pending = await self._fir_repo.list_pending_approval(limit=10)

        # Total FIR counts
        total_firs = await self._fir_repo.count()
        submitted_count = await self._fir_repo.count(status=FIRStatus.SUBMITTED)

        # Case links count
        stmt = select(func.count()).select_from(CaseLink)
        result = await self._db.execute(stmt)
        link_count = result.scalar() or 0

        return {
            "officer": {
                "name": officer.name,
                "badge_no": officer.badge_no,
                "role": officer.role.value,
            },
            "pending_approvals": [
                {
                    "id": str(f.id),
                    "fir_number": f.fir_number,
                    "officer_id": str(f.officer_id),
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                }
                for f in pending
            ],
            "stats": {
                "total_firs": total_firs,
                "pending_review": submitted_count,
                "case_links": link_count,
            },
        }

    async def get_audit_logs(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Get recent audit logs — Station Head only."""
        logs = await self._audit_repo.get_recent(offset=offset, limit=limit)
        total = await self._audit_repo.count()

        return {
            "logs": [
                {
                    "id": str(log.id),
                    "officer_id": str(log.officer_id),
                    "action": getattr(log.action, "value", log.action) if log.action else None,
                    "resource_type": getattr(log.resource_type, "value", log.resource_type) if log.resource_type else None,
                    "resource_id": str(log.resource_id) if log.resource_id else None,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    async def get_analytics(self) -> dict[str, Any]:
        """Crime analytics — FIR volume, section frequency."""
        # FIR counts by status
        stats = {}
        for s in FIRStatus:
            stats[s.value] = await self._fir_repo.count(status=s)

        total = sum(stats.values())

        return {
            "fir_by_status": stats,
            "total_firs": total,
            "note": "Detailed analytics (trends, section frequency, heatmaps) coming in future updates",
        }
