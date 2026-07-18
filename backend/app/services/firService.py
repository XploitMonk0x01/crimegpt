"""
FIR service — business logic for the FIR Automation Engine.

Handles:
    - generate_draft() — AI-powered FIR drafting using NER and RAG
    - submit_fir() — persist a finalized FIR
    - edit_fir() — update a draft FIR
    - approve_reject() — supervisor action on submitted FIRs
    - get_fir() / list_firs() — retrieval with RBAC scoping
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fir import FIR
from app.models.officer import Officer
from app.repositories.FIRRepository import FIRRepository
from app.schemas.fir_schema import (
    FIRApproveRejectRequest,
    FIRDraftResponse,
    FIREditRequest,
    FIRGenerateRequest,
    FIRResponse,
    FIRSubmitRequest,
)
from app.services.auditService import AuditService
from app.services.llmService import LLMService
from app.services.legalService import LegalService
from app.types.enums import AuditAction, FIRStatus, OfficerRole, ResourceType

logger = logging.getLogger("crimegpt.fir")


class FIRService:
    """FIR business logic — the core engine."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._repo = FIRRepository(db)
        self._audit = AuditService(db)
        self._llm = LLMService()
        self._legal = LegalService()

    async def generate_draft(
        self,
        request: FIRGenerateRequest,
        officer: Officer,
    ) -> FIRDraftResponse:
        """
        Generate an AI-drafted FIR from a natural language incident description.
        Integrates NER -> RAG -> LLM pipeline.
        """
        logger.info(f"Generating FIR draft for officer {officer.badge_no}")

        # 1. RAG: Get recommended sections from Legal Service
        try:
            recommended_sections_data = await self._legal.recommend_sections(request.incident_description)
            # Format sections for the draft response
            recommended_sections = [
                f"BNS {s.get('section', '')} - {s.get('title', '')}" 
                for s in recommended_sections_data if isinstance(s, dict)
            ]
        except Exception as e:
            logger.warning(f"Failed to get section recommendations: {e}")
            recommended_sections = ["Unable to recommend sections at this time"]

        # 2. NER: Extract entities
        ner_prompt = (
            f"Extract key entities from this incident description.\n\n"
            f"Incident: {request.incident_description}\n\n"
            f"Output JSON with these keys: suspects (list), victims (list), locations (list), weapons (list), vehicles (list). "
            f"If an entity is unknown, leave the list empty."
        )
        try:
            ner_response = await self._llm.generate(
                system_prompt="You are a legal NER system. Output ONLY valid JSON.",
                user_prompt=ner_prompt,
                temperature=0.0,
                max_tokens=300,
                json_mode=True,
                model_tier="fast"
            )
            import json
            extracted_entities = json.loads(ner_response)
        except Exception as e:
            logger.warning(f"Failed to extract entities: {e}")
            extracted_entities = {"error": "Entity extraction failed"}

        # 3. LLM: Draft the FIR Narrative
        draft_prompt = (
            f"Draft a professional First Information Report (FIR) narrative based on the following details.\n\n"
            f"Incident Description: {request.incident_description}\n"
            f"Recommended Sections: {', '.join(recommended_sections)}\n"
            f"Extracted Entities: {extracted_entities}\n\n"
            f"Instructions:\n"
            f"1. Write in formal legal/police language.\n"
            f"2. Incorporate the recommended BNS sections logically into the narrative.\n"
            f"3. Ensure the tone is objective and factual.\n"
            f"4. Do NOT output markdown formatting (like **), just clean text."
        )
        
        try:
            ai_narrative = await self._llm.generate(
                system_prompt="You are an AI assistant drafting FIRs for Indian Law Enforcement.",
                user_prompt=draft_prompt,
                temperature=0.3,
                max_tokens=1000,
                model_tier="primary"
            )
        except Exception as e:
            logger.warning(f"Failed to draft narrative: {e}")
            ai_narrative = f"Based on the incident described, a First Information Report is drafted.\n\n{request.incident_description}"

        draft = FIRDraftResponse(
            ai_narrative=ai_narrative.strip(),
            recommended_sections=recommended_sections,
            extracted_entities=extracted_entities,
            confidence_score=0.85,  # Heuristic for now
        )

        try:
            await self._audit.log(
                officer_id=officer.id,
                action=AuditAction.FIR_CREATE,
                resource_type=ResourceType.FIR,
                details={"phase": "draft_generation", "language": request.language},
            )
        except Exception as audit_err:
            # Audit failure must never crash the primary business flow
            logger.warning(f"Audit log failed for draft generation: {audit_err}")

        return draft

    async def submit_fir(
        self,
        request: FIRSubmitRequest,
        officer: Officer,
        ip_address: str = "unknown",
    ) -> FIRResponse:
        """Submit a finalized FIR for supervisor approval."""
        existing = await self._repo.get_by_fir_number(request.fir_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"FIR number {request.fir_number} already exists",
            )

        fir = FIR(
            fir_number=request.fir_number,
            status=FIRStatus.SUBMITTED,
            incident_description=request.incident_description,
            incident_date=request.incident_date,
            incident_location=request.incident_location,
            complainant=request.complainant.model_dump() if request.complainant else None,
            accused=request.accused.model_dump() if request.accused else None,
            sections=request.sections,
            ai_narrative=request.ai_narrative,
            ai_recommended_sections=request.ai_recommended_sections,
            officer_id=officer.id,
        )

        created = await self._repo.create(fir)

        await self._audit.log(
            officer_id=officer.id,
            action=AuditAction.FIR_SUBMIT,
            resource_type=ResourceType.FIR,
            resource_id=created.id,
            details={"fir_number": request.fir_number},
            ip_address=ip_address,
        )

        logger.info(f"FIR {request.fir_number} submitted by {officer.badge_no}")
        return FIRResponse.model_validate(created)

    async def edit_fir(
        self,
        fir_id: uuid.UUID,
        request: FIREditRequest,
        officer: Officer,
    ) -> FIRResponse:
        """Edit a draft/submitted FIR. Only owner or Inspector+ can edit."""
        fir = await self._repo.get_by_id(fir_id)
        if not fir:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FIR not found")

        if fir.officer_id != officer.id and officer.role not in (
            OfficerRole.INSPECTOR, OfficerRole.STATION_HEAD, OfficerRole.ADMIN,
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own FIRs")

        if fir.status not in (FIRStatus.DRAFT, FIRStatus.SUBMITTED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot edit FIR in '{fir.status.value}' status",
            )

        update_data = request.model_dump(exclude_unset=True)
        if "complainant" in update_data and update_data["complainant"]:
            update_data["complainant"] = request.complainant.model_dump()
        if "accused" in update_data and update_data["accused"]:
            update_data["accused"] = request.accused.model_dump()

        for field, value in update_data.items():
            setattr(fir, field, value)

        fir.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(fir)

        await self._audit.log(
            officer_id=officer.id,
            action=AuditAction.FIR_EDIT,
            resource_type=ResourceType.FIR,
            resource_id=fir.id,
            details={"edited_fields": list(update_data.keys())},
        )

        return FIRResponse.model_validate(fir)

    async def approve_reject(
        self,
        fir_id: uuid.UUID,
        request: FIRApproveRejectRequest,
        officer: Officer,
    ) -> FIRResponse:
        """Approve or reject a submitted FIR. Inspector+ only."""
        fir = await self._repo.get_by_id(fir_id)
        if not fir:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FIR not found")

        if fir.status != FIRStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"FIR is in '{fir.status.value}' status — can only approve/reject submitted FIRs",
            )

        if request.action == "approve":
            fir.status = FIRStatus.APPROVED
            audit_action = AuditAction.FIR_APPROVE
        else:
            fir.status = FIRStatus.REJECTED
            audit_action = AuditAction.FIR_REJECT
            if not request.remarks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Remarks are required when rejecting a FIR",
                )

        fir.approved_by_id = officer.id
        fir.supervisor_remarks = request.remarks
        fir.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(fir)

        await self._audit.log(
            officer_id=officer.id,
            action=audit_action,
            resource_type=ResourceType.FIR,
            resource_id=fir.id,
            details={"action": request.action, "remarks": request.remarks},
        )

        logger.info(f"FIR {fir.fir_number} {request.action}d by {officer.badge_no}")
        return FIRResponse.model_validate(fir)

    async def get_fir(self, fir_id: uuid.UUID, officer: Officer) -> FIRResponse:
        """Get a single FIR by ID with RBAC scoping."""
        fir = await self._repo.get_by_id(fir_id)
        if not fir:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FIR not found")

        if officer.role == OfficerRole.CONSTABLE and fir.officer_id != officer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own FIRs")

        return FIRResponse.model_validate(fir)

    async def list_firs(
        self,
        officer: Officer,
        *,
        status_filter: FIRStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[FIRResponse], int]:
        """List FIRs: Constable sees own, Inspector+ sees all."""
        offset = (page - 1) * page_size

        if officer.role == OfficerRole.CONSTABLE:
            firs = await self._repo.list_by_officer(
                officer.id, status=status_filter, offset=offset, limit=page_size
            )
            total = await self._repo.count_by_officer(officer.id, status=status_filter)
        else:
            firs = await self._repo.get_many(
                filters={"status": status_filter} if status_filter else None,
                offset=offset,
                limit=page_size,
                order_by="created_at",
                order_desc=True,
            )
            total = await self._repo.count(
                **({"status": status_filter} if status_filter else {})
            )

        return [FIRResponse.model_validate(f) for f in firs], total
