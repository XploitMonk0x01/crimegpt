"""
Document Generation service — auto-generates 7 legal document types.

Uses the Unified Case Data Pool (FIR + Evidence + Complainant/Accused data)
and LLM to dynamically populate document templates.

Supported documents:
    1. Purvani Chargesheet
    2. Medical Treatment Letter
    3. Remand Request Letter (Police Custody)
    4. Seizure Receipt
    5. Court Custody Letter
    6. Accused Panchanama
    7. Accused Face Identification Form
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fir import FIR
from app.models.evidence import Evidence
from app.models.officer import Officer
from app.repositories.FIRRepository import FIRRepository
from app.services.llmService import LLMService
from app.services.auditService import AuditService
from app.types.enums import AuditAction, DocumentType, ResourceType

logger = logging.getLogger("crimegpt.documents")

# ─── Document-specific system prompts ───

_DOC_SYSTEM_PROMPT = """You are a professional legal document drafter for Indian Law Enforcement.
You generate formal legal documents in compliance with Indian criminal procedure standards
(Bharatiya Nagarik Suraksha Sanhita / BNSS 2023, Bharatiya Nyaya Sanhita / BNS 2023, Bharatiya Sakshya Adhiniyam / BSA 2023).

Rules:
1. Use formal, precise legal language
2. Include all required fields per the document type
3. Reference specific legal sections where applicable
4. Use proper salutations and sign-off blocks
5. Output clean text — no markdown formatting (no **, ##, etc.)
6. Include placeholder brackets [___] for fields not available in the data
"""

_DOC_TEMPLATES: dict[DocumentType, dict[str, str]] = {
    DocumentType.CHARGESHEET: {
        "label": "Purvani Chargesheet",
        "description": "Preliminary chargesheet compiling FIR details, sections, complainant/accused info, and evidence list",
        "icon": "📋",
        "prompt": (
            "Generate a formal Purvani Chargesheet (Preliminary Chargesheet) based on the following case data.\n\n"
            "Include these sections:\n"
            "1. Case Header — FIR Number, Police Station, District, Date\n"
            "2. Complainant Details — Name, Address, Contact, ID Proof\n"
            "3. Accused Details — Name, Description, Address\n"
            "4. Brief Facts of the Case — Incident narrative\n"
            "5. Applicable Legal Sections — BNS/BNSS/BSA sections\n"
            "6. Evidence Summary — List of seized items and digital evidence\n"
            "7. Investigation Summary — Steps taken\n"
            "8. Prayer/Request — Charges sought\n"
            "9. Verification and Signature Block\n\n"
            "Case Data:\n{case_data}\n"
        ),
    },
    DocumentType.MEDICAL_LETTER: {
        "label": "Medical Treatment Letter",
        "description": "Referral letter for victim medical examination at a government hospital",
        "icon": "🏥",
        "prompt": (
            "Generate a Medical Treatment Letter (referral letter) from the Station House Officer "
            "to the Medical Officer at the nearest Government Hospital.\n\n"
            "Include:\n"
            "1. Letter header with Police Station details and date\n"
            "2. Reference to FIR Number and sections\n"
            "3. Victim/complainant details (name, age, gender)\n"
            "4. Brief description of the incident and injuries reported\n"
            "5. Request for medical examination and medico-legal certificate\n"
            "6. Signature block for SHO\n\n"
            "Case Data:\n{case_data}\n"
        ),
    },
    DocumentType.REMAND_REQUEST: {
        "label": "Remand Request Letter (Police Custody)",
        "description": "Application to the Magistrate requesting police custody of the accused",
        "icon": "⚖️",
        "prompt": (
            "Generate a Police Custody Remand Request Letter addressed to the Judicial Magistrate.\n\n"
            "Include:\n"
            "1. Court header — 'Before the Judicial Magistrate First Class, [District]'\n"
            "2. Case reference — FIR Number, Police Station, Sections\n"
            "3. Accused details — Name, age, address\n"
            "4. Grounds for remand — why police custody is necessary for investigation\n"
            "5. Duration requested (typically up to 15 days under BNSS Section 187)\n"
            "6. Prayer clause\n"
            "7. Verification and IO signature block\n\n"
            "Case Data:\n{case_data}\n"
        ),
    },
    DocumentType.SEIZURE_RECEIPT: {
        "label": "Seizure Receipt (Panchanama)",
        "description": "Receipt issued for items seized during investigation as per BNSS Section 105",
        "icon": "📦",
        "prompt": (
            "Generate a Seizure Receipt / Seizure Memo (Panchanama) as per BNSS Section 105.\n\n"
            "Include:\n"
            "1. Header — Police Station, District, Date and Time\n"
            "2. FIR reference number and sections\n"
            "3. Location of seizure\n"
            "4. Details of items seized — description, quantity, condition, distinguishing marks\n"
            "5. Name and address of person from whom seized\n"
            "6. Panch witnesses — names and addresses (use [___] placeholders)\n"
            "7. Certification that items were sealed in presence of witnesses\n"
            "8. Signature blocks — IO, witnesses, person from whom seized\n\n"
            "Case Data:\n{case_data}\n"
        ),
    },
    DocumentType.COURT_CUSTODY_LETTER: {
        "label": "Court Custody Letter",
        "description": "Application for judicial custody / remand extension before the court",
        "icon": "🏛️",
        "prompt": (
            "Generate a Court Custody Letter / Judicial Custody Application.\n\n"
            "Include:\n"
            "1. Court header — 'Before the Judicial Magistrate First Class'\n"
            "2. Case details — FIR Number, Sections, Police Station\n"
            "3. Accused details\n"
            "4. Summary of investigation progress\n"
            "5. Reason for seeking judicial custody\n"
            "6. Statement of compliance with custody provisions\n"
            "7. Prayer for judicial remand\n"
            "8. Signature block\n\n"
            "Case Data:\n{case_data}\n"
        ),
    },
    DocumentType.ACCUSED_PANCHANAMA: {
        "label": "Accused Arrest Panchanama",
        "description": "Formal arrest panchanama documenting the arrest of the accused",
        "icon": "🔒",
        "prompt": (
            "Generate an Accused Arrest Panchanama as per BNSS provisions.\n\n"
            "Include:\n"
            "1. Header — Date, Time, Place of Arrest\n"
            "2. FIR reference and applicable sections\n"
            "3. Arresting Officer details\n"
            "4. Accused personal details — full name, father's name, age, address, "
            "physical description, identification marks\n"
            "5. Personal search details — items found on person\n"
            "6. Rights informed to accused (Right to legal counsel, right to inform "
            "relative — as per BNSS Section 36)\n"
            "7. Panch witnesses details\n"
            "8. Declaration and signature blocks\n\n"
            "Case Data:\n{case_data}\n"
        ),
    },
    DocumentType.FACE_ID_FORM: {
        "label": "Accused Face Identification Form",
        "description": "Test identification parade form for facial identification of the accused",
        "icon": "👤",
        "prompt": (
            "Generate an Accused Face Identification Form / Test Identification Parade (TIP) form.\n\n"
            "Include:\n"
            "1. Header — Police Station, Date\n"
            "2. FIR reference number\n"
            "3. Accused details — name, age, physical description\n"
            "4. Physical description fields:\n"
            "   - Height, Build, Complexion\n"
            "   - Hair color and style\n"
            "   - Eye color\n"
            "   - Facial hair\n"
            "   - Identification marks (scars, tattoos, moles)\n"
            "5. Photograph attachment section\n"
            "6. Identifying witness statement section\n"
            "7. TIP procedure summary\n"
            "8. Result of identification\n"
            "9. Signature blocks — IO, Magistrate, Witnesses\n\n"
            "Case Data:\n{case_data}\n"
        ),
    },
}


class DocumentService:
    """Auto-generates legal documents from the unified case data pool."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._fir_repo = FIRRepository(db)
        self._llm = LLMService()
        self._audit = AuditService(db)

    async def generate_document(
        self,
        fir_id: uuid.UUID,
        document_type: DocumentType,
        officer: Officer,
        *,
        language: str = "en",
        additional_context: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a legal document by pulling data from the unified case pool.

        Steps:
        1. Load FIR + evidence from DB
        2. Compile case data snapshot
        3. Send to LLM with document-specific prompt
        4. Return structured document
        """
        # 1. Load FIR
        fir = await self._fir_repo.get_by_id(fir_id)
        if not fir:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FIR {fir_id} not found",
            )

        # 2. Build unified case data snapshot
        case_data = self._build_case_data(fir, additional_context)

        # 3. Get template config
        template = _DOC_TEMPLATES[document_type]
        user_prompt = template["prompt"].format(case_data=case_data)

        if language != "en":
            lang_name = {"hi": "Hindi", "gu": "Gujarati"}.get(language, "English")
            user_prompt += f"\n\nIMPORTANT: Generate the document in {lang_name} language."

        # 4. Generate with LLM
        try:
            content = await self._llm.generate(
                system_prompt=_DOC_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=3000,
                model_tier="primary",
            )
        except Exception as e:
            logger.error(f"LLM document generation failed: {e}")
            content = self._fallback_document(document_type, fir, case_data)

        # 5. Audit
        await self._audit.log(
            officer_id=officer.id,
            action=AuditAction.DOCUMENT_GENERATE,
            resource_type=ResourceType.DOCUMENT,
            resource_id=fir.id,
            details={
                "document_type": document_type.value,
                "fir_number": fir.fir_no,
                "language": language,
            },
        )

        logger.info(
            f"Document [{document_type.value}] generated for FIR {fir.fir_no} by {officer.badge_no}"
        )

        return {
            "document_type": document_type.value,
            "title": template["label"],
            "content": content.strip(),
            "fir_id": str(fir_id),
            "fir_number": fir.fir_no,
            "sections_used": fir.sections or [],
            "metadata": {
                "complainant": fir.complainant,
                "accused": fir.accused,
                "location": fir.location,
                "officer_badge": officer.badge_no,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "language": language,
        }

    def _build_case_data(self, fir: FIR, additional_context: str | None = None) -> str:
        """Compile a text snapshot of all case data for the LLM prompt."""
        parts = [
            f"FIR Number: {fir.fir_no}",
            f"Status: {fir.status.value}",
            f"Incident Date: {fir.incident_date or 'Not specified'}",
            f"Location: {fir.location or 'Not specified'}",
            f"Applicable Sections: {', '.join(fir.sections or ['Not specified'])}",
        ]

        # Complainant
        comp = fir.complainant or {}
        parts.append("\n--- Complainant ---")
        parts.append(f"Name: {comp.get('name', 'Not specified')}")
        parts.append(f"Father's Name: {comp.get('father_name', 'Not specified')}")
        parts.append(f"Age: {comp.get('age', 'Not specified')}")
        parts.append(f"Gender: {comp.get('gender', 'Not specified')}")
        parts.append(f"Address: {comp.get('address', 'Not specified')}")
        parts.append(f"Contact: {comp.get('contact', comp.get('phone', 'Not specified'))}")
        parts.append(f"ID Type: {comp.get('id_type', 'Not specified')}")
        parts.append(f"ID Number: {comp.get('id_number', comp.get('id_proof', 'Not specified'))}")

        # Accused
        acc = fir.accused or {}
        parts.append("\n--- Accused ---")
        parts.append(f"Name: {acc.get('name', 'Not specified')}")
        parts.append(f"Description: {acc.get('description', 'Not specified')}")
        parts.append(f"Age: {acc.get('age', 'Not specified')}")
        parts.append(f"Gender: {acc.get('gender', 'Not specified')}")
        parts.append(f"Address: {acc.get('address', 'Not specified')}")
        parts.append(f"Relation to Complainant: {acc.get('relation_to_complainant', 'Not specified')}")

        # Incident narrative
        parts.append("\n--- Incident Description ---")
        parts.append(fir.incident_description or "No description provided.")

        if fir.ai_narrative:
            parts.append("\n--- AI-Generated Narrative ---")
            parts.append(fir.ai_narrative)

        # Evidence
        if hasattr(fir, "evidence_items") and fir.evidence_items:
            parts.append(f"\n--- Evidence ({len(fir.evidence_items)} items) ---")
            for i, ev in enumerate(fir.evidence_items, 1):
                parts.append(f"{i}. {ev.filename} ({ev.file_type}) — SHA-256: {ev.sha256_hash[:16]}...")

        if additional_context:
            parts.append("\n--- Additional Officer Notes ---")
            parts.append(additional_context)

        return "\n".join(parts)

    def _fallback_document(self, doc_type: DocumentType, fir: FIR, case_data: str) -> str:
        """Generate a basic fallback document when LLM is unavailable."""
        template = _DOC_TEMPLATES[doc_type]
        return (
            f"{'=' * 60}\n"
            f"{template['label'].upper()}\n"
            f"{'=' * 60}\n\n"
            f"FIR No.: {fir.fir_no}\n"
            f"Date: {datetime.now(timezone.utc).strftime('%d/%m/%Y')}\n"
            f"Police Station: [___]\n"
            f"District: [___]\n\n"
            f"--- CASE DATA ---\n{case_data}\n\n"
            f"--- END ---\n\n"
            f"Note: This is a template-generated document. "
            f"Configure the LLM provider for AI-enhanced document drafting.\n\n"
            f"Investigating Officer: [___]\n"
            f"Signature: [___]\n"
            f"Date: [___]\n"
        )

    @staticmethod
    def get_available_types() -> list[dict[str, str]]:
        """Return metadata about all available document types."""
        return [
            {
                "type": doc_type.value,
                "label": template["label"],
                "description": template["description"],
                "icon": template["icon"],
            }
            for doc_type, template in _DOC_TEMPLATES.items()
        ]
