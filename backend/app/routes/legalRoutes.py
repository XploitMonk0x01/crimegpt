"""
Legal Intelligence routes — RAG-powered legal Q&A.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_role
from app.models.officer import Officer
from app.schemas.rag_schema import RAGUrlIngestRequest
from app.services.legalService import LegalService
from app.services.ragService import RAGService
from app.types.enums import OfficerRole

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


@router.post(
    "/corpus/ingest",
    summary="Ingest Legal Corpus into RAG",
    dependencies=[Depends(require_role(OfficerRole.ADMIN))],
)
async def ingest_corpus(
    corpus_dir: str = Query(default="./corpus", description="Path to corpus directory"),
    officer: Officer = Depends(get_current_user),
):
    """Admin-only: Ingest legal documents into ChromaDB vector store."""
    rag = RAGService()
    result = await rag.ingest_corpus(corpus_dir)
    return {"success": True, "data": result}


@router.post(
    "/corpus/ingest-urls",
    summary="Ingest Legal URLs into RAG",
    dependencies=[Depends(require_role(OfficerRole.ADMIN))],
)
async def ingest_urls(
    body: RAGUrlIngestRequest,
    officer: Officer = Depends(get_current_user),
):
    """Admin-only: Ingest public legal URLs into ChromaDB vector store."""
    rag = RAGService()
    result = await rag.ingest_urls(body)
    return {"success": True, "data": result}


@router.get("/corpus/stats", summary="RAG Corpus Statistics")
async def corpus_stats(
    officer: Officer = Depends(get_current_user),
):
    """Get vector store statistics — chunk count, connection status."""
    rag = RAGService()
    stats = await rag.get_stats()
    return {"success": True, "data": stats}
