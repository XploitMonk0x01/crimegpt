"""NLP & Translation routes — stub for Phase 11."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/transcribe", summary="Speech to Text")
async def transcribe():
    return {"message": "STT transcription — coming in Phase 11"}


@router.post("/translate", summary="Translate Text")
async def translate():
    return {"message": "Translation — coming in Phase 11"}


@router.get("/languages", summary="Supported Languages")
async def get_languages():
    return {"languages": ["en", "hi", "gu"]}
