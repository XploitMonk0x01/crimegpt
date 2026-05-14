"""
FIR repository — data access for First Information Reports.

All FIR-related database queries live here.
"""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fir import FIR
from app.repositories.base import BaseRepository
from app.types.enums import FIRStatus


class FIRRepository(BaseRepository[FIR]):
    """FIR-specific data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(FIR, db)

    async def get_by_fir_number(self, fir_number: str) -> FIR | None:
        """Look up a FIR by its registration number."""
        return await self.get_one(fir_number=fir_number)

    async def list_by_officer(
        self,
        officer_id: uuid.UUID,
        *,
        status: FIRStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[FIR]:
        """List FIRs filed by a specific officer, with optional status filter."""
        stmt = select(FIR).where(FIR.officer_id == officer_id)
        if status:
            stmt = stmt.where(FIR.status == status)
        stmt = stmt.order_by(FIR.created_at.desc()).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_officer(
        self,
        officer_id: uuid.UUID,
        *,
        status: FIRStatus | None = None,
    ) -> int:
        """Count FIRs filed by a specific officer."""
        stmt = select(func.count()).select_from(FIR).where(FIR.officer_id == officer_id)
        if status:
            stmt = stmt.where(FIR.status == status)
        result = await self._db.execute(stmt)
        return result.scalar() or 0

    async def list_by_station(
        self,
        station_id: uuid.UUID,
        *,
        status: FIRStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[FIR]:
        """List FIRs for a station (via officer join) — Inspector/Station Head view."""
        from app.models.officer import Officer

        stmt = (
            select(FIR)
            .join(Officer, FIR.officer_id == Officer.id)
            .where(Officer.station_id == station_id)
        )
        if status:
            stmt = stmt.where(FIR.status == status)
        stmt = stmt.order_by(FIR.created_at.desc()).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def list_pending_approval(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[FIR]:
        """List all submitted FIRs pending approval (for Inspector view)."""
        return await self.get_many(
            filters={"status": FIRStatus.SUBMITTED},
            offset=offset,
            limit=limit,
            order_by="created_at",
            order_desc=True,
        )
