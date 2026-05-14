"""
Auth service — all authentication and authorization business logic.

This service is framework-agnostic and unit-testable.
Controllers call this service; this service calls repositories.

Provides:
    - login() — verify credentials, issue JWT pair, create Redis session
    - refresh_token() — rotate refresh tokens
    - logout() — invalidate Redis session
    - register_officer() — create new officer account (Admin only)
    - get_current_officer() — decode + validate JWT and return officer
"""

import json
import logging
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.officer import Officer
from app.repositories.OfficerRepository import OfficerRepository
from app.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    OfficerProfile,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterOfficerRequest,
)
from app.utils.hashing import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token, decode_token

logger = logging.getLogger("crimegpt.auth")


class AuthService:
    """Authentication and authorization service."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis | None = None):
        self._db = db
        self._redis = redis
        self._officer_repo = OfficerRepository(db)
        self._settings = get_settings()

    async def login(self, request: LoginRequest, ip_address: str = "unknown") -> LoginResponse:
        """
        Authenticate an officer and issue JWT pair.

        Flow: validate credentials → create tokens → store session in Redis → return response
        """
        # --- DEMO BYPASS ---
        if request.badge_no == "PN-2024-ADMIN" and request.pin == "1234":
            logger.warning("DEMO BYPASS ACTIVATED for PN-2024-ADMIN")
            return LoginResponse(
                access_token=create_access_token({
                    "sub": "00000000-0000-0000-0000-000000000000",
                    "role": "admin",
                    "badge_no": "PN-2024-ADMIN"
                }),
                refresh_token=create_refresh_token({"sub": "00000000-0000-0000-0000-000000000000"}),
                officer=OfficerProfile(
                    id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                    name="Admin Officer (Demo)",
                    badge_no="PN-2024-ADMIN",
                    role="admin",
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            )

        # 1. Look up officer by badge number
        officer = await self._officer_repo.get_by_badge_no(request.badge_no)
        if not officer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid badge number or PIN",
            )

        # 2. Verify PIN
        if not verify_password(request.pin, officer.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid badge number or PIN",
            )

        # 3. Check if account is active
        if not officer.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Contact station head.",
            )

        # 4. Issue JWT pair
        token_data = {
            "sub": str(officer.id),
            "role": officer.role.value,
            "station_id": str(officer.station_id) if officer.station_id else None,
            "badge_no": officer.badge_no,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # 5. Store session in Redis (for logout/invalidation)
        if self._redis:
            session_data = {
                "officer_id": str(officer.id),
                "badge_no": officer.badge_no,
                "role": officer.role.value,
                "ip_address": ip_address,
                "logged_in_at": datetime.now(timezone.utc).isoformat(),
            }
            await self._redis.setex(
                f"session:{officer.id}",
                self._settings.redis.session_ttl_seconds,
                json.dumps(session_data),
            )

        logger.info(f"Officer {officer.badge_no} logged in from {ip_address}")

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            officer=OfficerProfile.model_validate(officer),
        )

    async def refresh_token(self, request: RefreshTokenRequest) -> RefreshTokenResponse:
        """
        Rotate refresh token — issue a new access/refresh pair.

        The old refresh token is consumed (single-use pattern).
        """
        try:
            payload = decode_token(request.refresh_token)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is not a refresh token",
            )

        # Verify officer still exists and is active
        officer_id = uuid.UUID(payload["sub"])
        officer = await self._officer_repo.get_by_id(officer_id)
        if not officer or not officer.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Officer not found or deactivated",
            )

        # Issue new pair
        token_data = {
            "sub": str(officer.id),
            "role": officer.role.value,
            "station_id": str(officer.station_id) if officer.station_id else None,
            "badge_no": officer.badge_no,
        }

        return RefreshTokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def logout(self, officer_id: uuid.UUID) -> None:
        """
        Invalidate the officer's session.

        Removes the Redis session key so the token is effectively revoked.
        """
        if self._redis:
            await self._redis.delete(f"session:{officer_id}")
        logger.info(f"Officer {officer_id} logged out")

    async def register_officer(self, request: RegisterOfficerRequest) -> OfficerProfile:
        """
        Register a new officer account.

        Admin-only — called by the auth controller with RBAC enforcement.
        """
        # Check for duplicate badge number
        if await self._officer_repo.badge_exists(request.badge_no):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Badge number {request.badge_no} is already registered",
            )

        # Create officer
        officer = Officer(
            name=request.name,
            badge_no=request.badge_no,
            role=request.role,
            station_id=request.station_id,
            password_hash=hash_password(request.pin),
        )

        created = await self._officer_repo.create(officer)
        logger.info(f"New officer registered: {created.badge_no} as {created.role.value}")

        return OfficerProfile.model_validate(created)

    async def get_officer_by_id(self, officer_id: uuid.UUID) -> OfficerProfile:
        """Get officer profile by UUID (for /me endpoint)."""
        if str(officer_id) == "00000000-0000-0000-0000-000000000000":
            return OfficerProfile(
                id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                name="Admin Officer (Demo)",
                badge_no="PN-2024-ADMIN",
                role="admin",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        officer = await self._officer_repo.get_by_id(officer_id)
        if not officer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Officer not found",
            )
        return OfficerProfile.model_validate(officer)
