"""
Global exception handler middleware.

Catches all unhandled exceptions across the application and returns
standardized error responses. Integrates with Sentry for error tracking.

This is the last line of defense — individual controllers should still
handle expected errors via BaseController.handle_error().
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None  # type: ignore[assignment]

from app.types.responses import ErrorDetail, ErrorResponse

logger = logging.getLogger("crimegpt")


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions (404, 401, 403, etc.)."""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                success=False,
                message=str(exc.detail),
            ).model_dump(mode="json"),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors.
        Converts Pydantic errors to our standardized ErrorResponse format.
        """
        errors = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"]) if error["loc"] else None
            errors.append(
                ErrorDetail(
                    field=field,
                    message=error["msg"],
                    code=error["type"],
                )
            )

        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                success=False,
                message="Validation failed",
                errors=errors,
            ).model_dump(mode="json"),
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(
        request: Request, exc: PermissionError
    ) -> JSONResponse:
        """Handle authorization failures."""
        return JSONResponse(
            status_code=403,
            content=ErrorResponse(
                success=False,
                message=str(exc) or "Insufficient permissions",
            ).model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch-all for unhandled exceptions.
        Logs the error, sends to Sentry, returns a generic 500.
        """
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc}",
            exc_info=True,
        )

        # Send to Sentry
        if sentry_sdk is not None:
            try:
                sentry_sdk.capture_exception(exc)
            except Exception:
                pass

        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                success=False,
                message="Internal server error",
            ).model_dump(mode="json"),
        )
