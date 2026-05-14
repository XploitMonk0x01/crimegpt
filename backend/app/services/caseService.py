"""
Case Linkage service — cross-case pattern detection.

Provides:
    - find_similar_cases() — embed FIR narrative → find similar FIRs
    - link_cases() — formally link two related cases
    - get_clusters() — MO cluster analysis
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_link import CaseLink
from app.models.officer import Officer
from app.repositories.base import BaseRepository
from app.repositories.FIRRepository import FIRRepository
from app.services.auditService import AuditService
from app.services.ragService import RAGService
from app.types.enums import AuditAction, OfficerRole, ResourceType

logger = logging.getLogger("crimegpt.case")


class CaseLinkRepository(BaseRepository[CaseLink]):
    """CaseLink-specific data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(CaseLink, db)

    async def get_links_for_fir(self, fir_id: uuid.UUID) -> list[CaseLink]:
        from sqlalchemy import select, or_
        stmt = (
            select(CaseLink)
            .where(or_(CaseLink.fir_id_a == fir_id, CaseLink.fir_id_b == fir_id))
            .order_by(CaseLink.created_at.desc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())


class CaseService:
    """Case linkage — cross-case pattern detection and formal linking."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._case_repo = CaseLinkRepository(db)
        self._fir_repo = FIRRepository(db)
        self._rag = RAGService()
        self._audit = AuditService(db)

    async def find_similar_cases(
        self,
        fir_id: uuid.UUID,
        officer: Officer,
        *,
        threshold: float = 0.70,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """Find FIRs with similar incident descriptions using vector similarity."""
        fir = await self._fir_repo.get_by_id(fir_id)
        if not fir:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FIR not found")

        # Use incident description for similarity search
        query_text = fir.incident_description or ""
        if fir.ai_narrative:
            query_text += f"\n{fir.ai_narrative}"

        chunks = await self._rag.query(query_text, n_results=max_results)

        similar = [
            {
                "text_preview": c["text"][:200],
                "similarity": c.get("similarity", 0),
                "source": c.get("metadata", {}),
            }
            for c in chunks
            if c.get("similarity", 0) >= threshold
        ]

        # Also check existing case links
        existing_links = await self._case_repo.get_links_for_fir(fir_id)

        return {
            "fir_id": str(fir_id),
            "fir_number": fir.fir_number,
            "similar_cases": similar,
            "existing_links": [
                {
                    "id": str(link.id),
                    "linked_fir": str(link.fir_id_b if link.fir_id_a == fir_id else link.fir_id_a),
                    "similarity_score": link.similarity_score,
                    "link_reason": link.link_reason,
                }
                for link in existing_links
            ],
            "threshold": threshold,
        }

    async def link_cases(
        self,
        fir_id_a: uuid.UUID,
        fir_id_b: uuid.UUID,
        officer: Officer,
        *,
        similarity_score: float = 0.0,
        link_reason: str = "",
    ) -> dict[str, Any]:
        """Formally link two related cases. Inspector+ only."""
        if officer.role not in (OfficerRole.INSPECTOR, OfficerRole.STATION_HEAD, OfficerRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Inspector or above can link cases",
            )

        # Verify both FIRs exist
        fir_a = await self._fir_repo.get_by_id(fir_id_a)
        fir_b = await self._fir_repo.get_by_id(fir_id_b)
        if not fir_a or not fir_b:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both FIRs not found")

        # Create link
        case_link = CaseLink(
            fir_id_a=fir_id_a,
            fir_id_b=fir_id_b,
            linked_by_id=officer.id,
            similarity_score=similarity_score,
            link_reason=link_reason,
        )

        created = await self._case_repo.create(case_link)

        # Audit
        await self._audit.log(
            officer_id=officer.id,
            action=AuditAction.CASE_LINK,
            resource_type=ResourceType.CASE_LINK,
            resource_id=created.id,
            details={
                "fir_a": str(fir_id_a),
                "fir_b": str(fir_id_b),
                "reason": link_reason,
            },
        )

        logger.info(f"Cases linked: {fir_a.fir_number} <-> {fir_b.fir_number} by {officer.badge_no}")

        return {
            "id": str(created.id),
            "fir_a": str(fir_id_a),
            "fir_b": str(fir_id_b),
            "similarity_score": similarity_score,
            "link_reason": link_reason,
            "linked_by": officer.badge_no,
        }

    async def get_clusters(self, officer: Officer) -> dict[str, Any]:
        """Get MO cluster analysis — Station Head dashboard view."""
        # Phase 10: basic cluster stats from case links
        all_links = await self._case_repo.get_many(limit=100, order_by="created_at", order_desc=True)

        return {
            "total_links": len(all_links),
            "recent_links": [
                {
                    "id": str(link.id),
                    "fir_a": str(link.fir_id_a),
                    "fir_b": str(link.fir_id_b),
                    "similarity": link.similarity_score,
                    "reason": link.link_reason,
                }
                for link in all_links[:20]
            ],
            "note": "Full cluster analysis with MO pattern detection coming in future updates",
        }
