"""
CaseDiaryEntry model — timeline-based investigation diary.

Maps to the `case_diary_entries` table.
Tracks every investigative step from the initial complaint to arrest.
Each entry is tied to a specific FIR and logged by an officer.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.types.enums import CaseDiaryEntryType


class CaseDiaryEntry(Base):
    __tablename__ = "case_diary_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    fir_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("firs.id"),
        nullable=False,
        index=True,
    )
    officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("officers.id"),
        nullable=False,
        index=True,
    )

    # Entry classification
    entry_type: Mapped[CaseDiaryEntryType] = mapped_column(
        SAEnum(CaseDiaryEntryType, name="diary_entry_type", create_constraint=True),
        nullable=False,
        default=CaseDiaryEntryType.OTHER,
    )

    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # When the investigative action took place (may differ from created_at)
    entry_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    fir = relationship("FIR", foreign_keys=[fir_id])
    officer = relationship("Officer", foreign_keys=[officer_id])

    def __repr__(self) -> str:
        return f"<CaseDiaryEntry {self.entry_type.value}: {self.title[:40]}>"
