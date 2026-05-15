"""NLP, speech-to-text, and translation routes."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.services.llmService import LLMService

router = APIRouter()

_SUPPORTED_AUDIO_TYPES = {
    "audio/flac",
    "audio/mp3",
    "audio/mpeg",
    "audio/mp4",
    "audio/mpga",
    "audio/m4a",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
    "video/webm",
}
_MAX_AUDIO_BYTES = 25 * 1024 * 1024


@router.post("/transcribe", summary="Speech to Text")
async def transcribe(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: str | None = Form(default="en", description="ISO-639-1 language code"),
    prompt: str | None = Form(default=None, description="Optional transcription context"),
):
    """Transcribe an uploaded audio clip using the configured Groq Whisper model."""
    content_type = (file.content_type or "").split(";")[0].lower()
    if content_type and content_type not in _SUPPORTED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio type: {file.content_type}",
        )

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file is empty")
    if len(audio_bytes) > _MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio file is too large; maximum size is 25 MB",
        )

    try:
        result = await LLMService().transcribe_audio(
            file_bytes=audio_bytes,
            filename=file.filename or "incident-audio.webm",
            content_type=content_type or file.content_type,
            language=language,
            prompt=prompt,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Audio transcription failed") from exc

    return {"success": True, "data": result}


@router.post("/translate", summary="Translate Text")
async def translate():
    return {"message": "Translation — coming in Phase 11"}


@router.get("/languages", summary="Supported Languages")
async def get_languages():
    return {"languages": ["en", "hi", "gu"]}
