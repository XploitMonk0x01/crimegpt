"""
Search routes — full-text search across FIRs by keyword or case number.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.fir import FIR
from app.models.officer import Officer

router = APIRouter()


@router.get("", summary="Search FIRs")
async def search_firs(
    q: str = Query(..., min_length=1, description="Search query — keyword, FIR number, or location"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    officer: Officer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search FIRs by keyword, FIR number, incident description, or location.
    Returns paginated results.
    """
    offset = (page - 1) * page_size
    search_term = f"%{q}%"

    # Build search filter — search across multiple text columns
    search_filter = or_(
        FIR.fir_no.ilike(search_term),
        FIR.incident_description.ilike(search_term),
        FIR.location.ilike(search_term),
        FIR.ai_narrative.ilike(search_term),
    )

    # Count
    count_stmt = select(func.count()).select_from(FIR).where(search_filter)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Fetch
    stmt = (
        select(FIR)
        .where(search_filter)
        .order_by(FIR.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    firs = list(result.scalars().all())

    return {
        "success": True,
        "data": [
            {
                "id": str(f.id),
                "fir_number": f.fir_no,
                "status": f.status.value if f.status else None,
                "incident_description": (f.incident_description or "")[:200],
                "incident_location": f.location,
                "sections": f.sections or [],
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "complainant_name": (f.complainant or {}).get("name"),
            }
            for f in firs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "query": q,
    }
