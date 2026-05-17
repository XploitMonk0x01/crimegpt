"""
Case Diary service — timeline-based investigation diary from FIR to arrest.

Provides:
    - add_entry() — add a manual diary entry
    - get_diary() — get full timeline for a FIR
    - auto_log() — automatically log system events (FIR submit, evidence upload, etc.)
    - delete_entry() — remove an entry (Inspector+ only)
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_diary import CaseDiaryEntry
from app.models.officer import Officer
from app.repositories.FIRRepository import FIRRepository
from app.services.auditService import AuditService
from app.types.enums import (
    AuditAction,
    CaseDiaryEntryType,
    OfficerRole,
    ResourceType,
)

logger = logging.getLogger("crimegpt.diary")


class CaseDiaryService:
    """Case diary — timeline-based investigation log."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._fir_repo = FIRRepository(db)
        self._audit = AuditService(db)

    async def add_entry(
        self,
        fir_id: uuid.UUID,
        officer: Officer,
        *,
        entry_type: CaseDiaryEntryType,
        title: str,
        description: str | None = None,
        entry_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Add a diary entry to a FIR's case diary."""
        # Verify FIR exists
        fir = await self._fir_repo.get_by_id(fir_id)
        if not fir:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FIR {fir_id} not found",
            )

        entry = CaseDiaryEntry(
            fir_id=fir_id,
            officer_id=officer.id,
            entry_type=entry_type,
            title=title,
            description=description,
            entry_date=entry_date or datetime.now(timezone.utc),
        )

        self._db.add(entry)
        await self._db.flush()
        await self._db.refresh(entry)

        # Audit
        await self._audit.log(
            officer_id=officer.id,
            action=AuditAction.DIARY_ENTRY_ADD,
            resource_type=ResourceType.CASE_DIARY,
            resource_id=entry.id,
            details={
                "fir_id": str(fir_id),
                "entry_type": entry_type.value,
                "title": title,
            },
        )

        logger.info(f"Diary entry added for FIR {fir.fir_no}: {entry_type.value} — {title}")

        return self._serialize_entry(entry, officer_name=officer.name, officer_badge=officer.badge_no)

    async def get_diary(
        self,
        fir_id: uuid.UUID,
        officer: Officer,
    ) -> dict[str, Any]:
        """Get the full case diary timeline for a FIR."""
        fir = await self._fir_repo.get_by_id(fir_id)
        if not fir:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FIR {fir_id} not found",
            )

        stmt = (
            select(CaseDiaryEntry)
            .where(CaseDiaryEntry.fir_id == fir_id)
            .order_by(CaseDiaryEntry.entry_date.asc())
        )
        result = await self._db.execute(stmt)
        entries = list(result.scalars().all())

        return {
            "fir_id": str(fir_id),
            "fir_number": fir.fir_no,
            "total_entries": len(entries),
            "entries": [
                self._serialize_entry(e)
                for e in entries
            ],
        }

    async def delete_entry(
        self,
        entry_id: uuid.UUID,
        officer: Officer,
    ) -> dict[str, str]:
        """Delete a diary entry. Inspector+ only."""
        if officer.role not in (
            OfficerRole.INSPECTOR,
            OfficerRole.STATION_HEAD,
            OfficerRole.ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Inspector or above can delete diary entries",
            )

        stmt = select(CaseDiaryEntry).where(CaseDiaryEntry.id == entry_id)
        result = await self._db.execute(stmt)
        entry = result.scalar_one_or_none()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diary entry not found",
            )

        await self._db.delete(entry)
        await self._db.flush()

        # Audit
        await self._audit.log(
            officer_id=officer.id,
            action=AuditAction.DIARY_ENTRY_DELETE,
            resource_type=ResourceType.CASE_DIARY,
            resource_id=entry_id,
            details={"fir_id": str(entry.fir_id), "title": entry.title},
        )

        logger.info(f"Diary entry {entry_id} deleted by {officer.badge_no}")
        return {"message": "Entry deleted", "id": str(entry_id)}

    async def auto_log(
        self,
        fir_id: uuid.UUID,
        officer_id: uuid.UUID,
        entry_type: CaseDiaryEntryType,
        title: str,
        description: str | None = None,
    ) -> None:
        """
        Automatically add a diary entry — used by other services.
        Silently skips on error so it never breaks the main flow.
        """
        try:
            entry = CaseDiaryEntry(
                fir_id=fir_id,
                officer_id=officer_id,
                entry_type=entry_type,
                title=title,
                description=description,
                entry_date=datetime.now(timezone.utc),
            )
            self._db.add(entry)
            await self._db.flush()
        except Exception as e:
            logger.warning(f"Auto-log diary entry failed (non-fatal): {e}")

    @staticmethod
    def get_entry_types() -> list[dict[str, str]]:
        """Return all available diary entry types."""
        labels = {
            CaseDiaryEntryType.COMPLAINT_RECEIVED: "Complaint Received",
            CaseDiaryEntryType.FIR_REGISTERED: "FIR Registered",
            CaseDiaryEntryType.INVESTIGATION_STARTED: "Investigation Started",
            CaseDiaryEntryType.WITNESS_EXAMINED: "Witness Examined",
            CaseDiaryEntryType.EVIDENCE_SEIZED: "Evidence Seized",
            CaseDiaryEntryType.SPOT_VISIT: "Spot Visit / Scene Inspection",
            CaseDiaryEntryType.ARREST_MADE: "Arrest Made",
            CaseDiaryEntryType.REMAND_REQUESTED: "Remand Requested",
            CaseDiaryEntryType.CHARGESHEET_FILED: "Chargesheet Filed",
            CaseDiaryEntryType.COURT_HEARING: "Court Hearing",
            CaseDiaryEntryType.OTHER: "Other",
        }
        return [
            {"type": t.value, "label": labels.get(t, t.value)}
            for t in CaseDiaryEntryType
        ]

    @staticmethod
    def _serialize_entry(
        entry: CaseDiaryEntry,
        *,
        officer_name: str | None = None,
        officer_badge: str | None = None,
    ) -> dict[str, Any]:
        """Serialize a CaseDiaryEntry to a dict."""
        return {
            "id": str(entry.id),
            "fir_id": str(entry.fir_id),
            "officer_id": str(entry.officer_id),
            "officer_name": officer_name,
            "officer_badge": officer_badge,
            "entry_type": entry.entry_type.value,
            "title": entry.title,
            "description": entry.description,
            "entry_date": entry.entry_date.isoformat() if entry.entry_date else None,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        }
