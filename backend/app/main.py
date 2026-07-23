"""
FastAPI application factory.

Creates and configures the FastAPI app with:
    - CORS middleware
    - Global exception handlers
    - Sentry integration (if DSN configured)
    - All API routers mounted under /api/v1
    - Health check endpoint
    - Startup/shutdown lifecycle events
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware.error_handler import register_exception_handlers

logger = logging.getLogger("crimegpt")


def _init_sentry(settings) -> None:
    """Initialize Sentry SDK if DSN is configured."""
    if settings.sentry.dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=settings.sentry.dsn,
                traces_sample_rate=settings.sentry.traces_sample_rate,
                environment=settings.sentry.environment,
                integrations=[
                    FastApiIntegration(transaction_style="endpoint"),
                    SqlalchemyIntegration(),
                ],
            )
            logger.info("Sentry initialized successfully")
        except ImportError:
            logger.warning("sentry-sdk not installed, skipping Sentry init")
    else:
        logger.info("No SENTRY_DSN configured, running without Sentry")


def _init_logging(settings) -> None:
    """Configure structured logging."""
    log_level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.setLevel(log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown events."""
    settings = get_settings()

    # --- STARTUP ---
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"   Debug mode: {settings.debug}")
    logger.info(f"   LLM mode: {settings.llm.mode}")
    logger.info(f"   API prefix: {settings.api_prefix}")

    yield

    # --- SHUTDOWN ---
    logger.info("🛑 Shutting down CrimeGPT backend...")

    # Close Redis connection
    from app.db.redis_db import close_redis

    await close_redis()
    logger.info("   Redis connection closed")

    # Dispose SQLAlchemy engine
    from app.db.session import engine

    await engine.dispose()
    logger.info("   Database connections closed")

    logger.info("✅ Shutdown complete")


def create_app() -> FastAPI:
    """
    Application factory — creates and configures the FastAPI app.

    This is the single entry point for app creation.
    """
    settings = get_settings()

    # Init logging first
    _init_logging(settings)

    # Init Sentry (must be before app creation for proper instrumentation)
    _init_sentry(settings)

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI-Powered Automation for Crime Documentation and Legal Intelligence. "
            "Built for Indian Law Enforcement Agencies."
        ),
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # --- Middleware ---

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Exception Handlers ---
    register_exception_handlers(app)

    # --- Health Check ---
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
        }

    # --- Register Routers ---
    _register_routers(app, settings)

    return app


def _register_routers(app: FastAPI, settings) -> None:
    """Mount all API routers under the configured prefix."""
    prefix = settings.api_prefix

    from app.routes.authRoutes import router as auth_router
    from app.routes.firRoutes import router as fir_router
    from app.routes.legalRoutes import router as legal_router
    from app.routes.evidenceRoutes import router as evidence_router
    from app.routes.caseRoutes import router as case_router
    from app.routes.nlpRoutes import router as nlp_router
    from app.routes.dashboardRoutes import router as dashboard_router
    from app.routes.documentRoutes import router as document_router
    from app.routes.caseDiaryRoutes import router as diary_router
    from app.routes.searchRoutes import router as search_router
    from app.routes.cctnsRoutes import router as cctns_router
    from app.routes.lersRoutes import router as lers_router

    app.include_router(auth_router, prefix=f"{prefix}/auth", tags=["Authentication"])
    app.include_router(fir_router, prefix=f"{prefix}/fir", tags=["FIR Management"])
    app.include_router(legal_router, prefix=f"{prefix}/legal", tags=["Legal Intelligence"])
    app.include_router(evidence_router, prefix=f"{prefix}/evidence", tags=["Evidence Management"])
    app.include_router(case_router, prefix=f"{prefix}/cases", tags=["Case Linkage"])
    app.include_router(nlp_router, prefix=f"{prefix}/nlp", tags=["NLP & Translation"])
    app.include_router(dashboard_router, prefix=f"{prefix}/dashboard", tags=["Dashboard"])
    app.include_router(document_router, prefix=f"{prefix}/documents", tags=["Document Generation"])
    app.include_router(diary_router, prefix=f"{prefix}/diary", tags=["Case Diary"])
    app.include_router(search_router, prefix=f"{prefix}/search", tags=["Search"])
    app.include_router(cctns_router, prefix=f"{prefix}/cctns", tags=["CCTNS & BharatPol Interoperability"])
    app.include_router(lers_router, prefix=f"{prefix}/lers", tags=["LERS Cyber Portal"])

    logger.info(f"   Registered 12 API routers under {prefix}")


# Module-level app instance for uvicorn / ASGI servers
app = create_app()
