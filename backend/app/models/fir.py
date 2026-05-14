"""
FIR model — core First Information Report records.

Maps to the `firs` table.
Stores structured FIR data with JSONB fields for flexible complainant/accused info
and TEXT[] for legal section references.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.types.enums import FIRStatus


class FIR(Base):
    __tablename__ = "firs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    fir_no: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("officers.id"),
        nullable=False,
        index=True,
    )

    # Complainant and accused stored as JSONB for flexibility
    # Schema: {name, father_name, address, phone, id_proof, id_number}
    complainant: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    accused: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Incident details
    incident_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    incident_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    location: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Legal sections — e.g., ["BNS-318", "IT-66C", "POCSO-4"]
    sections: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )

    # AI-generated content
    ai_narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_sections_rationale: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Lifecycle
    status: Mapped[FIRStatus] = mapped_column(
        SAEnum(FIRStatus, name="fir_status", create_constraint=True),
        nullable=False,
        default=FIRStatus.DRAFT,
    )
    supervisor_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("officers.id"),
        nullable=True,
    )

    # PDF export
    pdf_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    sha256_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Language used for input
    input_language: Mapped[str | None] = mapped_column(String(5), nullable=True)

    # Timestamps
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
    officer = relationship("Officer", back_populates="firs", foreign_keys=[officer_id])
    evidence_items = relationship("Evidence", back_populates="fir", lazy="selectin")
    case_links_a = relationship(
        "CaseLink",
        back_populates="fir_a",
        foreign_keys="CaseLink.fir_id_a",
        lazy="selectin",
    )
    case_links_b = relationship(
        "CaseLink",
        back_populates="fir_b",
        foreign_keys="CaseLink.fir_id_b",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<FIR {self.fir_no} ({self.status.value})>"
