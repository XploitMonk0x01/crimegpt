"""
AuditLog repository — data access for immutable audit trail.

This table is APPEND-ONLY. Only create and read operations are permitted.
No updates or deletes — ever.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.types.enums import AuditAction, ResourceType


class AuditLogRepository:
    """
    Audit log data access — INSERT and SELECT only.

    Does NOT extend BaseRepository because we deliberately exclude
    update and delete operations for immutability.
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        *,
        officer_id: uuid.UUID,
        action: AuditAction,
        resource_type: ResourceType,
        resource_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str = "unknown",
    ) -> AuditLog:
        """Create an immutable audit log entry."""
        entry = AuditLog(
            officer_id=officer_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        self._db.add(entry)
        await self._db.flush()
        return entry

    async def get_by_officer(
        self,
        officer_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get audit logs for a specific officer."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.officer_id == officer_id)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_resource(
        self,
        resource_type: ResourceType,
        resource_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get audit logs for a specific resource."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.resource_type == resource_type)
            .where(AuditLog.resource_id == resource_id)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_recent(
        self,
        *,
        action: AuditAction | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get recent audit logs, optionally filtered by action type."""
        stmt = select(AuditLog)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **filters) -> int:
        """Count audit log entries."""
        stmt = select(func.count()).select_from(AuditLog)
        if "officer_id" in filters:
            stmt = stmt.where(AuditLog.officer_id == filters["officer_id"])
        if "action" in filters:
            stmt = stmt.where(AuditLog.action == filters["action"])
        result = await self._db.execute(stmt)
        return result.scalar() or 0
