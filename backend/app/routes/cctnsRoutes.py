"""
CCTNS & BharatPol Integration Routes — Mock API for National Crime Portal Interoperability.

Provides mock integration endpoints for:
    - CCTNS (Crime and Criminal Tracking Network & Systems) national FIR sync
    - BharatPol National Criminal & Wanted Person verification lookup
    - Real-time CCTNS synchronization audit & verification checking
"""

import uuid
import random
import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.officer import Officer
from app.repositories.FIRRepository import FIRRepository
from app.repositories.AuditLogRepository import AuditLogRepository
from app.types.enums import AuditAction, ResourceType

router = APIRouter()


class CCTNSSyncResponse(BaseModel):
    success: bool
    fir_id: str
    fir_number: str
    cctns_national_id: str
    sync_status: str
    national_grid_node: str
    verification_hash: str
    synced_at: str
    cctns_portal_url: str
    details: dict


class CriminalCheckResult(BaseModel):
    searched_query: str
    match_found: bool
    national_id: Optional[str] = None
    full_name: Optional[str] = None
    criminal_history_count: int = 0
    active_warrants: int = 0
    risk_level: str = "LOW"
    bharatpol_flag: Optional[str] = None
    registered_cases: list[dict] = Field(default_factory=list)


@router.post("/sync-fir/{fir_id}", response_model=CCTNSSyncResponse, summary="Sync FIR to CCTNS National Grid")
async def sync_fir_to_cctns(
    fir_id: uuid.UUID,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mock CCTNS Sync: Pushes an approved/submitted FIR to the national CCTNS database grid.
    Generates a deterministic CCTNS National Registry Reference ID and cryptographic verification hash.
    """
    fir_repo = FIRRepository(db)
    fir = await fir_repo.get_by_id(fir_id)
    if not fir:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FIR record not found")

    # Generate mock CCTNS National ID
    clean_fir = (fir.fir_number or f"FIR-{str(fir.id)[:8]}").replace("/", "-")
    cctns_national_id = f"CCTNS-2026-IN-{clean_fir}"

    # Generate payload verification hash
    raw_payload = f"{fir.id}:{fir.fir_number}:{fir.incident_description}:{officer.badge_no}"
    verification_hash = hashlib.sha256(raw_payload.encode()).hexdigest()[:16].upper()

    now_iso = datetime.now(timezone.utc).isoformat()

    # Log audit trail
    audit_repo = AuditLogRepository(db)
    await audit_repo.create(
        officer_id=officer.id,
        action=AuditAction.CCTNS_SYNC,
        resource_type=ResourceType.FIR,
        resource_id=fir.id,
        details={
            "target_system": "CCTNS_NATIONAL_GRID",
            "cctns_national_id": cctns_national_id,
            "verification_hash": verification_hash,
        },
    )

    return CCTNSSyncResponse(
        success=True,
        fir_id=str(fir.id),
        fir_number=fir.fir_number or "DRAFT-FIR",
        cctns_national_id=cctns_national_id,
        sync_status="SYNCED_VERIFIED",
        national_grid_node="NCRB_CENTRAL_NODE_DELHI_01",
        verification_hash=verification_hash,
        synced_at=now_iso,
        cctns_portal_url=f"https://cctns.gov.in/portal/verify?ref={cctns_national_id}",
        details={
            "state_grid": "UTTAR_PRADESH_POLICE_GRID",
            "district": "PRATAPGARH",
            "encryption": "AES-256-GCM / SHA-256",
            "interoperable_status": "BHARATPOL_READY",
        },
    )


@router.get("/verify-person", summary="BharatPol / CCTNS Criminal Record Check")
async def verify_person_bharatpol(
    query: str = Query(..., min_length=2, description="Name, Aadhaar, PAN, or Badge number to verify"),
    officer: Officer = Depends(get_current_user),
):
    """
    Mock BharatPol National Criminal Database Lookup.
    Searches across national wanted lists, past CCTNS records, and active warrants.
    """
    query_clean = query.strip()
    
    # Deterministic mock response based on search string
    is_suspicious = any(k in query_clean.lower() for k in ["tripathi", "gang", "extortion", "wanted", "mk"])
    
    if is_suspicious:
        return CriminalCheckResult(
            searched_query=query_clean,
            match_found=True,
            national_id=f"IND-CRIM-2024-{abs(hash(query_clean)) % 899999 + 100000}",
            full_name=f"{query_clean.upper()} (Verified Matches Found)",
            criminal_history_count=3,
            active_warrants=1,
            risk_level="HIGH",
            bharatpol_flag="ACTIVE_NOTICE_SERVED",
            registered_cases=[
                {
                    "case_no": "BNS-2024-UP-228",
                    "offence": "Fabricating False Evidence & Extortion",
                    "act": "BNS Section 228, 308",
                    "status": "UNDER_INVESTIGATION",
                    "station": "Pratapgarh HQ",
                },
                {
                    "case_no": "BNS-2023-DL-351",
                    "offence": "Criminal Intimidation",
                    "act": "BNS Section 351",
                    "status": "CHARGESHEET_FILED",
                    "station": "Delhi Special Cell",
                },
            ],
        )
    else:
        return CriminalCheckResult(
            searched_query=query_clean,
            match_found=False,
            criminal_history_count=0,
            active_warrants=0,
            risk_level="CLEAR",
            bharatpol_flag="NO_PRIOR_RECORD",
            registered_cases=[],
        )


@router.get("/status/{fir_id}", summary="Get CCTNS National Sync Status")
async def get_cctns_status(
    fir_id: uuid.UUID,
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check whether a specific FIR is synchronized with national CCTNS grid."""
    fir_repo = FIRRepository(db)
    fir = await fir_repo.get_by_id(fir_id)
    if not fir:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FIR not found")

    clean_fir = (fir.fir_number or f"FIR-{str(fir.id)[:8]}").replace("/", "-")
    cctns_id = f"CCTNS-2026-IN-{clean_fir}"

    return {
        "success": True,
        "fir_id": str(fir.id),
        "is_synced": True,
        "cctns_national_id": cctns_id,
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "sync_health": "OPTIMAL",
    }
