"""
Evidence service — chain-of-custody evidence management.

Provides:
    - upload() — receive file, compute SHA-256, store, create custody entry
    - get_custody_chain() — immutable custody log for evidence
    - verify_integrity() — re-compute SHA-256 and compare with stored hash
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.evidence import Evidence
from app.models.officer import Officer
from app.repositories.base import BaseRepository
from app.services.auditService import AuditService
from app.types.enums import AuditAction, ResourceType
from app.utils.hashing import sha256_hash

logger = logging.getLogger("crimegpt.evidence")


class EvidenceRepository(BaseRepository[Evidence]):
    """Evidence-specific data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(Evidence, db)


class EvidenceService:
    """Evidence management with chain-of-custody tracking."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._repo = EvidenceRepository(db)
        self._audit = AuditService(db)
        self._settings = get_settings()

    async def upload(
        self,
        file: UploadFile,
        fir_id: uuid.UUID,
        officer: Officer,
        *,
        description: str = "",
        ip_address: str = "unknown",
    ) -> dict[str, Any]:
        """Upload evidence file with SHA-256 integrity hash."""
        # Read file content
        content = await file.read()

        # Check file size
        max_size = self._settings.evidence.max_file_size_mb * 1024 * 1024
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds {self._settings.evidence.max_file_size_mb}MB limit",
            )

        # Compute SHA-256 hash
        file_hash = sha256_hash(content)

        # Store file on disk
        storage_dir = Path(self._settings.evidence.storage_path) / str(fir_id)
        storage_dir.mkdir(parents=True, exist_ok=True)

        evidence_id = uuid.uuid4()
        file_ext = Path(file.filename or "unknown").suffix
        file_path = storage_dir / f"{evidence_id}{file_ext}"
        file_path.write_bytes(content)

        # Initial custody entry
        custody_entry = {
            "action": "UPLOADED",
            "officer_id": str(officer.id),
            "officer_badge": officer.badge_no,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ip_address": ip_address,
            "notes": description,
        }

        # Create DB record
        evidence = Evidence(
            id=evidence_id,
            fir_id=fir_id,
            officer_id=officer.id,
            filename=file.filename or "unknown",
            file_type=file.content_type or "application/octet-stream",
            file_size_bytes=len(content),
            sha256_hash=file_hash,
            metadata_json={
                "original_filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(content),
                "description": description,
            },
            chain_of_custody=[custody_entry],
            stored_path=str(file_path),
        )

        created = await self._repo.create(evidence)

        # Audit
        await self._audit.log(
            officer_id=officer.id,
            action=AuditAction.EVIDENCE_UPLOAD,
            resource_type=ResourceType.EVIDENCE,
            resource_id=created.id,
            details={"filename": file.filename, "hash": file_hash},
            ip_address=ip_address,
        )

        logger.info(f"Evidence {evidence_id} uploaded by {officer.badge_no} for FIR {fir_id}")

        return {
            "id": str(created.id),
            "filename": created.filename,
            "sha256_hash": file_hash,
            "file_size": len(content),
            "fir_id": str(fir_id),
            "uploaded_by": officer.badge_no,
            "created_at": created.uploaded_at.isoformat() if created.uploaded_at else None,
        }

    async def get_custody_chain(
        self,
        evidence_id: uuid.UUID,
        officer: Officer,
    ) -> dict[str, Any]:
        """Get the immutable chain-of-custody for an evidence item."""
        evidence = await self._repo.get_by_id(evidence_id)
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

        # Audit the access
        await self._audit.log(
            officer_id=officer.id,
            action=AuditAction.EVIDENCE_ACCESS,
            resource_type=ResourceType.EVIDENCE,
            resource_id=evidence_id,
        )

        return {
            "id": str(evidence.id),
            "filename": evidence.filename,
            "sha256_hash": evidence.sha256_hash,
            "chain_of_custody": evidence.chain_of_custody or [],
            "total_events": len(evidence.chain_of_custody or []),
        }

    async def verify_integrity(
        self,
        evidence_id: uuid.UUID,
        officer: Officer,
    ) -> dict[str, Any]:
        """Re-compute SHA-256 and compare with stored hash."""
        evidence = await self._repo.get_by_id(evidence_id)
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

        file_path = Path(evidence.stored_path)
        if not file_path.exists():
            return {
                "id": str(evidence.id),
                "integrity": "FILE_MISSING",
                "stored_hash": evidence.sha256_hash,
                "current_hash": None,
                "match": False,
            }

        current_hash = sha256_hash(file_path.read_bytes())
        match = current_hash == evidence.sha256_hash

        # Audit
        await self._audit.log(
            officer_id=officer.id,
            action=AuditAction.EVIDENCE_VERIFY,
            resource_type=ResourceType.EVIDENCE,
            resource_id=evidence_id,
            details={"match": match, "current_hash": current_hash},
        )

        return {
            "id": str(evidence.id),
            "filename": evidence.filename,
            "integrity": "VERIFIED" if match else "TAMPERED",
            "stored_hash": evidence.sha256_hash,
            "current_hash": current_hash,
            "match": match,
        }
