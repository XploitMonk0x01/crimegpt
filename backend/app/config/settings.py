"""
Centralized Configuration — the ONLY source of config in the application.

Replaces `unifiedConfig` pattern from backend-dev-guidelines.
Usage:
    from app.config import get_settings
    settings = get_settings()
    settings.auth.jwt_secret  # ✅
    os.environ["JWT_SECRET"]  # ❌ NEVER

All env vars are validated at startup via Pydantic BaseSettings.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    url: str = Field(
        default="postgresql+asyncpg://crimegpt:pass@localhost:5432/crimegpt",
        alias="DATABASE_URL",
    )
    pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    echo: bool = Field(default=False, alias="DB_ECHO")

    model_config = {"env_prefix": "", "extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}


class RedisSettings(BaseSettings):
    """Redis configuration."""

    url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    session_ttl_seconds: int = Field(default=28800, alias="REDIS_SESSION_TTL")  # 8 hours

    model_config = {"env_prefix": "", "extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}


class AuthSettings(BaseSettings):
    """Authentication & authorization configuration."""

    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiry_hours: int = Field(default=8, alias="JWT_EXPIRY_HOURS")
    refresh_token_expiry_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRY_DAYS")

    model_config = {"env_prefix": "", "extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}


class LLMSettings(BaseSettings):
    """LLM provider configuration — supports cloud (Groq) and local (Ollama)."""

    mode: Literal["cloud", "local"] = Field(default="cloud", alias="LLM_MODE")

    # Groq (cloud / demo)
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")

    # Multi-model routing — different models for different tasks
    groq_model_primary: str = Field(
        default="meta-llama/llama-4-scout-17b-16e-instruct",
        alias="GROQ_MODEL_PRIMARY",
        description="FIR drafting, legal Q&A, section recommendation",
    )
    groq_model_fast: str = Field(
        default="llama-3.1-8b-instant",
        alias="GROQ_MODEL_FAST",
        description="NER, classification, quick tasks",
    )
    groq_model_fallback: str = Field(
        default="llama-3.3-70b-versatile",
        alias="GROQ_MODEL_FALLBACK",
        description="Complex legal reasoning fallback",
    )
    groq_model_whisper: str = Field(
        default="whisper-large-v3-turbo",
        alias="GROQ_MODEL_WHISPER",
        description="Speech-to-text transcription",
    )

    # Legacy alias — routes to primary model
    groq_model: str = Field(default="meta-llama/llama-4-scout-17b-16e-instruct", alias="GROQ_MODEL")

    # Ollama (local / production)
    ollama_base_url: str = Field(default="http://ollama:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="mistral:7b-instruct", alias="OLLAMA_MODEL")

    model_config = {"env_prefix": "", "extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}


class ChromaSettings(BaseSettings):
    """ChromaDB vector database configuration."""

    host: str = Field(default="localhost", alias="CHROMA_HOST")
    port: int = Field(default=8001, alias="CHROMA_PORT")
    collection_name: str = Field(default="legal_corpus", alias="CHROMA_COLLECTION")

    model_config = {"env_prefix": "", "extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}


class SentrySettings(BaseSettings):
    """Sentry observability configuration."""

    dsn: str | None = Field(default=None, alias="SENTRY_DSN")
    traces_sample_rate: float = Field(default=1.0, alias="SENTRY_TRACES_SAMPLE_RATE")
    environment: str = Field(default="development", alias="SENTRY_ENVIRONMENT")

    model_config = {"env_prefix": "", "extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}


class EvidenceSettings(BaseSettings):
    """Evidence file storage configuration."""

    storage_path: str = Field(default="./storage/evidence", alias="EVIDENCE_STORAGE_PATH")
    max_file_size_mb: int = Field(default=50, alias="EVIDENCE_MAX_FILE_SIZE_MB")

    model_config = {"env_prefix": "", "extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}


class Settings(BaseSettings):
    """
    Root application settings.

    All configuration is loaded from environment variables (or .env file).
    Sub-settings are composed for clean namespaced access:
        settings.auth.jwt_secret
        settings.db.url
        settings.llm.groq_api_key
    """

    # Application
    app_name: str = Field(default="CrimeGPT", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS",
    )

    # Sub-settings (composed)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    chroma: ChromaSettings = Field(default_factory=ChromaSettings)
    sentry: SentrySettings = Field(default_factory=SentrySettings)
    evidence: EvidenceSettings = Field(default_factory=EvidenceSettings)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings singleton.
    Call this instead of constructing Settings() directly.
    """
    return Settings()
