"""
FIR validation schemas (Pydantic v2).

Request/response validation for the FIR Automation Engine.
All FIR data flows through these models.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.types.enums import FIRStatus


# ───────────────── Nested Types ─────────────────


class ComplainantInfo(BaseModel):
    """Complainant details embedded in FIR."""

    name: str = Field(..., min_length=1, max_length=255)
    father_name: str | None = None
    age: int | None = Field(default=None, ge=1, le=150)
    gender: str | None = None
    address: str | None = None
    contact: str | None = None
    id_type: str | None = None
    id_number: str | None = None


class AccusedInfo(BaseModel):
    """Accused person details embedded in FIR."""

    name: str | None = None
    description: str | None = None
    address: str | None = None
    age: int | None = Field(default=None, ge=1, le=150)
    gender: str | None = None
    relation_to_complainant: str | None = None


# ───────────────── Request Schemas ─────────────────


class FIRGenerateRequest(BaseModel):
    """Request to generate an AI-drafted FIR from an incident description."""

    incident_description: str = Field(
        ...,
        min_length=20,
        max_length=10000,
        description="Natural language description of the incident",
        examples=["On May 12, 2026, at approximately 11:30 PM, the complainant's mobile phone (Samsung Galaxy S24) was snatched by two unknown persons on a motorcycle near Connaught Place, New Delhi."],
    )
    language: str = Field(
        default="en",
        description="Language of the incident description (en/hi/gu)",
    )
    complainant: ComplainantInfo | None = Field(
        default=None,
        description="Pre-filled complainant info (optional — can be added later)",
    )


class FIRSubmitRequest(BaseModel):
    """Submit a finalized FIR draft for supervisor approval."""

    fir_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="FIR registration number",
    )
    incident_description: str = Field(default="No description provided", min_length=1)
    incident_date: Any = Field(default_factory=datetime.utcnow)
    incident_location: str = Field(default="Pending Location", min_length=1)
    complainant: ComplainantInfo = Field(default_factory=lambda: ComplainantInfo(name="Unknown Complainant"))
    accused: AccusedInfo | None = None
    sections: list[str] = Field(
        default_factory=list,
        description="Applicable BNS/IPC sections",
    )
    ai_narrative: str | None = Field(
        default=None,
        description="AI-generated FIR narrative (from generate endpoint)",
    )
    ai_recommended_sections: list[str] | None = None

    @field_validator("incident_date", mode="before")
    @classmethod
    def validate_incident_date(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            return v
        if isinstance(v, str) and v.strip():
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except Exception:
                pass
        return datetime.utcnow()

    @field_validator("incident_location", "incident_description", mode="before")
    @classmethod
    def _coerce_str_fields(cls, v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return v.get("name") or v.get("text") or v.get("location") or v.get("address") or v.get("value") or str(v)
        return str(v)

    @field_validator("sections", mode="before")
    @classmethod
    def _coerce_sections_list(cls, v: Any) -> list[str]:
        if not v or not isinstance(v, list):
            return []
        res = []
        for item in v:
            if isinstance(item, str):
                res.append(item)
            elif isinstance(item, dict):
                sec_str = item.get("bns_section") or item.get("section") or item.get("code") or item.get("title") or str(item)
                res.append(sec_str)
            else:
                res.append(str(item))
        return res


class FIREditRequest(BaseModel):
    """Partial update to a draft FIR."""

    fir_number: str | None = None
    incident_description: str | None = None
    incident_date: datetime | None = None
    incident_location: str | None = None
    complainant: ComplainantInfo | None = None
    accused: AccusedInfo | None = None
    sections: list[str] | None = None
    ai_narrative: str | None = None


class FIRApproveRejectRequest(BaseModel):
    """Supervisor action on a submitted FIR."""

    action: str = Field(
        ...,
        pattern="^(approve|reject)$",
        description="Either 'approve' or 'reject'",
    )
    remarks: str | None = Field(
        default=None,
        max_length=2000,
        description="Supervisor remarks (required for rejection)",
    )


# ───────────────── Response Schemas ─────────────────


class FIRDraftResponse(BaseModel):
    """Response from the AI draft generation endpoint."""

    ai_narrative: str
    recommended_sections: list[str]
    extracted_entities: dict[str, Any] = Field(default_factory=dict)
    suggested_complainant: ComplainantInfo | None = None
    suggested_accused: AccusedInfo | None = None
    confidence_score: float = Field(ge=0.0, le=1.0)


class FIRResponse(BaseModel):
    """Full FIR record response."""

    id: uuid.UUID
    fir_number: str | None
    status: FIRStatus
    incident_description: str | None = None
    incident_date: datetime | None
    incident_location: str | None
    complainant: dict | None
    accused: dict | None
    sections: list[str] = Field(default_factory=list)
    ai_narrative: str | None
    ai_recommended_sections: list[str] | None
    officer_id: uuid.UUID
    approved_by_id: uuid.UUID | None
    supervisor_remarks: str | None
    pdf_url: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("sections", mode="before")
    @classmethod
    def _coerce_sections(cls, v):
        return [] if v is None else v

    model_config = {"from_attributes": True}


class FIRListItem(BaseModel):
    """Compact FIR item for list views."""

    id: uuid.UUID
    fir_number: str | None
    status: FIRStatus
    incident_location: str | None
    sections: list[str] = Field(default_factory=list)
    created_at: datetime

    @field_validator("sections", mode="before")
    @classmethod
    def _coerce_sections(cls, v):
        return [] if v is None else v

    model_config = {"from_attributes": True}
