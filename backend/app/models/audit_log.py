"""
AuditLog model — immutable audit trail for all critical actions.

Maps to the `audit_logs` table.
This table is APPEND-ONLY — no updates or deletes are permitted.
Every FIR creation, edit, approval, evidence access, and login is logged.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("officers.id"),
        nullable=False,
        index=True,
    )

    # Action performed — must be a valid AuditAction enum value
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Resource affected
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Additional context (e.g., "Changed status from draft to submitted")
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Immutable timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    officer = relationship("Officer", foreign_keys=[officer_id])

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.officer_id} at {self.timestamp}>"
