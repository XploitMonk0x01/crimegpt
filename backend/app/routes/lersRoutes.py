"""
LERS (Law Enforcement Request System) Mock API Routes.

Simulates Meta / WhatsApp / Instagram / Telegram / X LERS-compliant
law enforcement request generation and filing.

Supports:
- Emergency Disclosure Request
- Account Preservation Request
- Subscriber & IP Log Request
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.middleware.auth import get_current_user
from app.models.officer import Officer

logger = logging.getLogger("crimegpt.lers")
router = APIRouter(tags=["LERS"])


# ─── Request Schemas ──────────────────────────────────────────────────────────

class LERSRequestPayload(BaseModel):
    platform: str = Field(..., description="Target platform: meta | whatsapp | instagram | telegram | x")
    request_type: str = Field(..., description="Type: emergency_disclosure | preservation | subscriber_ip")
    fir_reference: str | None = Field(default=None, description="FIR number reference")
    section_of_law: str = Field(default="Section 94 BNSS / Section 91 CrPC")
    target_identifier: str = Field(..., description="Phone/Email/Username/IP of the target account")
    target_identifier_type: str = Field(default="phone", description="phone | email | username | ip | uid")
    description_of_crime: str = Field(default="", description="Brief description of the alleged offence")
    data_requested: list[str] = Field(default_factory=list, description="List of data categories requested")
    urgency: str = Field(default="standard", description="emergency | urgent | standard")
    station_name: str | None = None
    date_of_incident: str | None = None


# ─── Platform Metadata ────────────────────────────────────────────────────────

PLATFORM_META = {
    "meta": {
        "full_name": "Meta Platforms, Inc.",
        "lers_portal": "https://www.facebook.com/records",
        "legal_entity": "Meta Platforms Ireland Limited",
        "jurisdiction": "Republic of Ireland / USA",
        "legal_team_email": "records@facebook.com",
        "response_sla_emergency": "within 20 minutes",
        "response_sla_standard": "within 10 business days",
    },
    "whatsapp": {
        "full_name": "WhatsApp LLC (a Meta Company)",
        "lers_portal": "https://www.facebook.com/records",
        "legal_entity": "WhatsApp LLC",
        "jurisdiction": "USA (California)",
        "legal_team_email": "records@facebook.com",
        "response_sla_emergency": "within 20 minutes",
        "response_sla_standard": "within 10 business days",
    },
    "instagram": {
        "full_name": "Instagram LLC (a Meta Company)",
        "lers_portal": "https://www.facebook.com/records",
        "legal_entity": "Meta Platforms Ireland Limited",
        "jurisdiction": "Republic of Ireland / USA",
        "legal_team_email": "records@facebook.com",
        "response_sla_emergency": "within 20 minutes",
        "response_sla_standard": "within 10 business days",
    },
    "telegram": {
        "full_name": "Telegram Messenger Inc.",
        "lers_portal": "https://telegram.org/privacy#law-enforcement",
        "legal_entity": "Telegram Messenger Inc.",
        "jurisdiction": "Dubai, UAE",
        "legal_team_email": "abuse@telegram.org",
        "response_sla_emergency": "Varies",
        "response_sla_standard": "Varies",
    },
    "x": {
        "full_name": "X Corp. (formerly Twitter Inc.)",
        "lers_portal": "https://help.twitter.com/en/rules-and-policies/x-legal-faqs",
        "legal_entity": "X Corp.",
        "jurisdiction": "USA (California)",
        "legal_team_email": "privacy@x.com",
        "response_sla_emergency": "within 24 hours",
        "response_sla_standard": "within 14 business days",
    },
}

REQUEST_TYPE_LABELS = {
    "emergency_disclosure": "Emergency Disclosure Request (EDR)",
    "preservation": "Account Preservation Request (APR)",
    "subscriber_ip": "Subscriber Information & IP Log Request",
}


def _make_reference_id(platform: str, req_type: str) -> str:
    short = {"emergency_disclosure": "EDR", "preservation": "APR", "subscriber_ip": "IPR"}.get(req_type, "REQ")
    plat_code = platform.upper()[:3]
    return f"LERS-{plat_code}-{short}-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"


def _build_template(
    payload: LERSRequestPayload,
    officer: Officer,
    platform_info: dict,
    ref_id: str,
    now: datetime,
) -> str:
    type_label = REQUEST_TYPE_LABELS.get(payload.request_type, payload.request_type)
    expiry = (now + timedelta(days=90)).strftime("%d %B %Y")

    # Build data request list
    data_list = "\n".join(f"    {i+1}. {d}" for i, d in enumerate(payload.data_requested)) if payload.data_requested else "    1. Account registration details\n    2. Associated phone number and email\n    3. IP log for last 90 days\n    4. Account activity and login history"

    urgency_text = {
        "emergency": "⚠ EMERGENCY REQUEST — IMMEDIATE RESPONSE REQUIRED WITHIN 20 MINUTES",
        "urgent": "URGENT REQUEST — Response required within 24 hours",
        "standard": "Standard Request",
    }.get(payload.urgency, "Standard Request")

    template = f"""
================================================================================
        {urgency_text}
        GOVERNMENT OF INDIA — LAW ENFORCEMENT REQUEST
        LERS-COMPLIANT FORMAL LEGAL NOTICE
================================================================================

Reference Number  : {ref_id}
Date of Issue     : {now.strftime("%d %B %Y, %H:%M hrs IST")}
Issuing Authority : {payload.station_name or officer.name + " / Police Station"}
Legal Framework   : {payload.section_of_law}
Classification    : RESTRICTED — LAW ENFORCEMENT USE ONLY

TO,
The Legal / Law Enforcement Team,
{platform_info["full_name"]}
({platform_info["legal_entity"]})
LERS Portal: {platform_info["lers_portal"]}

FROM,
Officer : {officer.name}
Badge No: {officer.badge_no}
Role    : {(officer.role or "IO").upper()}
Station : {payload.station_name or "Police Station — India"}

────────────────────────────────────────────────────────────────────────────────
SUBJECT: {type_label.upper()} — FIR Ref: {payload.fir_reference or "PENDING"}
────────────────────────────────────────────────────────────────────────────────

1. LEGAL AUTHORITY
   This request is issued under {payload.section_of_law}, which empowers any
   police officer not below the rank of Sub-Inspector to issue production
   orders to any entity in possession of electronically stored records relevant
   to a cognizable offence under investigation.

2. NATURE OF OFFENCE
   {payload.description_of_crime or "Details of the cognizable offence are contained in the referenced FIR."}

3. TARGET ACCOUNT DETAILS
   Platform          : {payload.platform.title()}
   Identifier Type   : {payload.target_identifier_type.upper()}
   Identifier Value  : {payload.target_identifier}
   {'FIR Reference    : ' + payload.fir_reference if payload.fir_reference else ''}

4. DATA REQUESTED
   The following user data records are requested for the account identified above:
{data_list}

5. PRESERVATION DIRECTIVE
   You are hereby directed to PRESERVE all data associated with the target account
   for a minimum period of 90 days from the date of this notice (until {expiry}),
   pending further legal process.

6. URGENCY & RESPONSE
   Request Priority  : {payload.urgency.upper()}
   Expected SLA      : {platform_info["response_sla_emergency"] if payload.urgency == "emergency" else platform_info["response_sla_standard"]}
   Please acknowledge receipt and respond to the issuing authority's official
   contact within the stated SLA.

7. CONFIDENTIALITY
   This request and its contents are STRICTLY CONFIDENTIAL. You are requested NOT
   to disclose this notice to the target account holder or any third party, as
   doing so may obstruct the course of justice under Section 238 BNS (Obstructing
   a public servant in discharge of public functions).

8. PENALTY FOR NON-COMPLIANCE
   Failure to comply with this legal notice may constitute an offence under
   Section 63 of the Information Technology Act, 2000, punishable with imprisonment
   up to 3 years and/or fine up to ₹5,00,000.

────────────────────────────────────────────────────────────────────────────────

DIGITAL ATTESTATION
  Reference ID    : {ref_id}
  Generated By    : CrimeGPT LERS Module (AI-Assisted Police Station System)
  Timestamp (UTC) : {now.isoformat()}

OFFICIAL SEAL & SIGNATURE

  _______________________________
  {officer.name}
  {(officer.role or "IO").upper()}, Badge No. {officer.badge_no}
  {payload.station_name or "Police Station — India"}

================================================================================
NOTE: This is a mock LERS request generated by CrimeGPT for demonstration and
training purposes. In a live deployment, this document would be digitally signed
and submitted through the official LERS portal of the respective platform.
================================================================================
"""
    return template.strip()


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/generate", summary="Generate LERS Compliant Request")
async def generate_lers_request(
    body: LERSRequestPayload,
    officer: Officer = Depends(get_current_user),
):
    platform = body.platform.lower()
    platform_info = PLATFORM_META.get(platform)
    if not platform_info:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}. Valid: {list(PLATFORM_META.keys())}")

    ref_id = _make_reference_id(platform, body.request_type)
    now = datetime.utcnow()
    template = _build_template(body, officer, platform_info, ref_id, now)

    logger.info(f"LERS {body.request_type} generated for {platform} by {officer.badge_no} [{ref_id}]")

    return {
        "success": True,
        "message": "LERS request generated successfully",
        "data": {
            "reference_id": ref_id,
            "platform": platform,
            "platform_info": platform_info,
            "request_type": body.request_type,
            "request_type_label": REQUEST_TYPE_LABELS.get(body.request_type, body.request_type),
            "template": template,
            "generated_at": now.isoformat(),
            "expires_preservation_at": (now + timedelta(days=90)).isoformat(),
            "urgency": body.urgency,
            "officer": {
                "name": officer.name,
                "badge_no": officer.badge_no,
                "role": officer.role,
            },
        },
    }


@router.get("/platforms", summary="List Supported LERS Platforms")
async def list_platforms(officer: Officer = Depends(get_current_user)):
    return {
        "success": True,
        "message": "Supported LERS platforms",
        "data": {
            k: {
                "name": v["full_name"],
                "portal": v["lers_portal"],
                "sla_emergency": v["response_sla_emergency"],
                "sla_standard": v["response_sla_standard"],
            }
            for k, v in PLATFORM_META.items()
        },
    }


@router.get("/request-types", summary="List LERS Request Types")
async def list_request_types(officer: Officer = Depends(get_current_user)):
    return {
        "success": True,
        "message": "Supported LERS request types",
        "data": [
            {
                "id": "emergency_disclosure",
                "label": "Emergency Disclosure Request (EDR)",
                "description": "For imminent threat to life or safety. Fastest response SLA.",
                "default_data": [
                    "Account registration info (name, phone, email)",
                    "Real-time IP address and geolocation",
                    "Last known login activity",
                    "Device identifiers (IMEI, IMSI, MSISDN)",
                ],
            },
            {
                "id": "preservation",
                "label": "Account Preservation Request (APR)",
                "description": "Directs platform to preserve account data for 90 days pending court order.",
                "default_data": [
                    "All account records (registration, activity, communications metadata)",
                    "Preserved for 90 days",
                ],
            },
            {
                "id": "subscriber_ip",
                "label": "Subscriber Information & IP Log Request",
                "description": "Requests subscriber identity and IP access logs for investigation.",
                "default_data": [
                    "Subscriber name and profile details",
                    "Registered phone number and email",
                    "IP login history (last 90 days)",
                    "Device information",
                    "Account creation details",
                ],
            },
        ],
    }
