"""
Audit service — business logic for immutable audit trail.

Every critical action in the system goes through this service.
The audit log is append-only — no edits or deletes.
"""

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.AuditLogRepository import AuditLogRepository
from app.types.enums import AuditAction, ResourceType

logger = logging.getLogger("crimegpt.audit")


class AuditService:
    """Audit logging service — records all critical actions."""

    def __init__(self, db: AsyncSession):
        self._repo = AuditLogRepository(db)

    async def log(
        self,
        *,
        officer_id: uuid.UUID,
        action: AuditAction,
        resource_type: ResourceType,
        resource_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str = "unknown",
    ) -> None:
        """
        Create an audit log entry.

        This is called by other services (auth, FIR, evidence, etc.)
        after every critical action.
        """
        await self._repo.create(
            officer_id=officer_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        logger.debug(
            f"Audit: {action.value} by officer {officer_id} "
            f"on {resource_type.value}:{resource_id}"
        )

    async def get_officer_logs(
        self,
        officer_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ):
        """Get audit logs for a specific officer."""
        return await self._repo.get_by_officer(officer_id, offset=offset, limit=limit)

    async def get_resource_logs(
        self,
        resource_type: ResourceType,
        resource_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ):
        """Get audit logs for a specific resource."""
        return await self._repo.get_by_resource(
            resource_type, resource_id, offset=offset, limit=limit
        )

    async def get_recent_logs(
        self,
        *,
        action: AuditAction | None = None,
        offset: int = 0,
        limit: int = 50,
    ):
        """Get recent audit logs."""
        return await self._repo.get_recent(action=action, offset=offset, limit=limit)
