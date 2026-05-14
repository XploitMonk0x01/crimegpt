"""
Legal Intelligence routes — RAG-powered legal Q&A.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.officer import Officer
from app.services.legalService import LegalService

router = APIRouter()


@router.post("/query", summary="Legal RAG Query")
async def legal_query(
    question: str = Query(..., min_length=5, description="Legal question"),
    language: str = Query(default="en"),
    officer: Officer = Depends(get_current_user),
):
    service = LegalService()
    result = await service.ask_question(question, language=language)
    return {"success": True, "data": result}


@router.get("/sections/search", summary="Search Legal Sections")
async def search_sections(
    keyword: str = Query(..., min_length=2),
    act: str | None = Query(default=None),
    n_results: int = Query(default=10, ge=1, le=50),
    officer: Officer = Depends(get_current_user),
):
    service = LegalService()
    results = await service.search_sections(keyword, act=act, n_results=n_results)
    return {"success": True, "data": results}
