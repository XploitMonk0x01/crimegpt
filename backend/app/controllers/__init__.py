"""
BaseController — all controllers MUST extend this class.

Provides:
    - handle_success(): standardized success response
    - handle_error(): standardized error response + Sentry capture
    - handle_paginated(): paginated list response

No raw `JSONResponse` or `dict` returns outside these helpers.
"""

import logging
import math
from typing import Any

from fastapi.responses import JSONResponse

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None  # type: ignore[assignment]

from app.types.responses import APIResponse, ErrorResponse, PaginatedResponse, PaginationMeta

logger = logging.getLogger("crimegpt")


class BaseController:
    """
    Base class for all controllers.

    Enforces the backend-dev-guidelines doctrine:
        - Controllers coordinate, services decide
        - All errors go to Sentry
        - Standardized response format
    """

    def handle_success(
        self,
        data: Any = None,
        message: str = "OK",
        status_code: int = 200,
    ) -> JSONResponse:
        """Return a standardized success response."""
        response = APIResponse(
            success=True,
            message=message,
            data=data,
        )
        return JSONResponse(
            content=response.model_dump(mode="json"),
            status_code=status_code,
        )

    def handle_created(self, data: Any = None, message: str = "Created") -> JSONResponse:
        """Return a 201 Created response."""
        return self.handle_success(data=data, message=message, status_code=201)

    def handle_paginated(
        self,
        data: list[Any],
        page: int,
        page_size: int,
        total_items: int,
        message: str = "OK",
    ) -> JSONResponse:
        """Return a paginated list response."""
        total_pages = math.ceil(total_items / page_size) if page_size > 0 else 0
        response = PaginatedResponse(
            success=True,
            message=message,
            data=data,
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages,
            ),
        )
        return JSONResponse(
            content=response.model_dump(mode="json"),
            status_code=200,
        )

    def handle_error(
        self,
        error: Exception,
        context: str = "",
        status_code: int = 500,
        message: str = "Internal server error",
    ) -> JSONResponse:
        """
        Handle an error: log it, send to Sentry, return standardized error response.

        NEVER swallow errors silently.
        """
        # Log with context
        logger.error(f"[{context}] {type(error).__name__}: {error}", exc_info=True)

        # Send to Sentry (if configured)
        if sentry_sdk is not None:
            try:
                sentry_sdk.capture_exception(error)
            except Exception:
                pass  # Sentry itself failing should not crash the app

        response = ErrorResponse(
            success=False,
            message=message,
        )
        return JSONResponse(
            content=response.model_dump(mode="json"),
            status_code=status_code,
        )
