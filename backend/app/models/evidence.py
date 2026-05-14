"""
Evidence model — digital evidence with chain-of-custody tracking.

Maps to the `evidence` table.
Every evidence file is hashed with SHA-256 on upload.
Chain of custody is an immutable JSONB array of custody events.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Evidence(Base):
    __tablename__ = "evidence"

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

    # File metadata
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)

    # Integrity verification
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Auto-extracted metadata (EXIF, GPS, timestamps, etc.)
    # Schema: {exif: {...}, gps: {lat, lng}, camera: {...}, created: "..."}
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Immutable chain of custody — append-only JSONB array
    # Each entry: {officer_id, officer_name, action, timestamp, ip_address, notes}
    chain_of_custody: Mapped[list[dict] | None] = mapped_column(
        ARRAY(JSONB), nullable=True
    )

    # Storage location
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    fir = relationship("FIR", back_populates="evidence_items")
    officer = relationship("Officer", back_populates="evidence_uploads")

    def __repr__(self) -> str:
        return f"<Evidence {self.filename} (FIR: {self.fir_id})>"
