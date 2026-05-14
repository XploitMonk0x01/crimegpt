"""
Uvicorn entry point.

Run with:
    python -m app.server
    OR
    uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
"""

from app.main import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    from app.config import get_settings

    settings = get_settings()

    uvicorn.run(
        "app.server:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
