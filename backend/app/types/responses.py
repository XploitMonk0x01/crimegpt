"""
Standardized API response types.

All API responses MUST use these wrappers for consistency.
Controllers use BaseController.handle_success() which wraps data in APIResponse.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Standard success response envelope.

    Example:
        {
            "success": true,
            "message": "FIR created successfully",
            "data": { ... }
        }
    """

    success: bool = True
    message: str = "OK"
    data: T | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated list response envelope.

    Example:
        {
            "success": true,
            "message": "OK",
            "data": [...],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_items": 150,
                "total_pages": 8
            }
        }
    """

    success: bool = True
    message: str = "OK"
    data: list[T] = Field(default_factory=list)
    pagination: "PaginationMeta | None" = None


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int
    page_size: int
    total_items: int
    total_pages: int


class ErrorDetail(BaseModel):
    """Structured error detail for API error responses."""

    field: str | None = None
    message: str
    code: str | None = None


class ErrorResponse(BaseModel):
    """
    Standard error response envelope.

    Example:
        {
            "success": false,
            "message": "Validation failed",
            "errors": [
                {"field": "badge_no", "message": "Badge number is required"}
            ]
        }
    """

    success: bool = False
    message: str = "An error occurred"
    errors: list[ErrorDetail] = Field(default_factory=list)
