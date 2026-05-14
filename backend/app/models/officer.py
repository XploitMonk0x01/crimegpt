"""
Officer model — police officer accounts with RBAC roles.

Maps to the `officers` table.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.types.enums import OfficerRole


class Officer(Base):
    __tablename__ = "officers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    badge_no: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    role: Mapped[OfficerRole] = mapped_column(
        SAEnum(OfficerRole, name="officer_role", create_constraint=True),
        nullable=False,
        default=OfficerRole.CONSTABLE,
    )
    station_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    firs = relationship("FIR", back_populates="officer", lazy="selectin", foreign_keys="[FIR.officer_id]")
    evidence_uploads = relationship("Evidence", back_populates="officer", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Officer {self.badge_no} ({self.role.value})>"
