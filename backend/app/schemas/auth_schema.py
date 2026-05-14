"""
Auth validation schemas (Pydantic v2).

Replaces Zod schemas from backend-dev-guidelines.
All request/response validation flows through these models — no raw dict access.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.types.enums import OfficerRole


# ───────────────── Request Schemas ─────────────────


class LoginRequest(BaseModel):
    """Login with badge number and PIN."""

    badge_no: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Officer badge number",
        examples=["DL-001"],
    )
    pin: str = Field(
        ...,
        min_length=4,
        max_length=128,
        description="Officer PIN / password",
    )

    @field_validator("badge_no")
    @classmethod
    def normalize_badge_no(cls, v: str) -> str:
        """Strip whitespace and normalize to uppercase."""
        return v.strip().upper()


class RefreshTokenRequest(BaseModel):
    """Refresh token rotation request."""

    refresh_token: str = Field(
        ...,
        min_length=10,
        description="Valid refresh JWT token",
    )


class RegisterOfficerRequest(BaseModel):
    """Register a new officer account. (Admin-only endpoint)."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Full name",
        examples=["Sub-Inspector Priya Sharma"],
    )
    badge_no: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Unique badge number",
        examples=["DL-042"],
    )
    pin: str = Field(
        ...,
        min_length=4,
        max_length=128,
        description="Login PIN / password",
    )
    role: OfficerRole = Field(
        default=OfficerRole.CONSTABLE,
        description="Officer role for RBAC",
    )
    station_id: uuid.UUID | None = Field(
        default=None,
        description="Station UUID (optional)",
    )

    @field_validator("badge_no")
    @classmethod
    def normalize_badge_no(cls, v: str) -> str:
        return v.strip().upper()


# ───────────────── Response Schemas ─────────────────


class OfficerProfile(BaseModel):
    """Officer profile returned in login/me responses."""

    id: uuid.UUID
    name: str
    badge_no: str
    role: OfficerRole
    station_id: uuid.UUID | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """Login response with token pair + officer profile."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    officer: OfficerProfile


class RefreshTokenResponse(BaseModel):
    """Response after token rotation."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
