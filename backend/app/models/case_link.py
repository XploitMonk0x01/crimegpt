"""
CaseLink model — cross-case linkage for pattern detection.

Maps to the `case_links` table.
Created when the case linkage system detects semantically similar FIRs
and an Inspector formally links them.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CaseLink(Base):
    __tablename__ = "case_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    fir_id_a: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("firs.id"),
        nullable=False,
        index=True,
    )
    fir_id_b: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("firs.id"),
        nullable=False,
        index=True,
    )

    # Semantic similarity score (0.0 — 1.0)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Reason for linking (AI-generated or manual)
    link_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Officer who formally linked the cases
    linked_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("officers.id"),
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    fir_a = relationship("FIR", back_populates="case_links_a", foreign_keys=[fir_id_a])
    fir_b = relationship("FIR", back_populates="case_links_b", foreign_keys=[fir_id_b])
    linked_by_officer = relationship("Officer", foreign_keys=[linked_by])

    def __repr__(self) -> str:
        return f"<CaseLink {self.fir_id_a} ↔ {self.fir_id_b} ({self.similarity_score:.2f})>"
