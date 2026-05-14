"""
JWT authentication middleware — FastAPI dependency.

Usage in routes:
    @router.get("/protected")
    async def handler(officer: Officer = Depends(get_current_user)):
        ...

Extracts the JWT from the Authorization header, validates it,
verifies the Redis session (if available), and returns the Officer ORM object.
"""

import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.redis_db import get_redis
from app.models.officer import Officer
from app.repositories.OfficerRepository import OfficerRepository
from app.utils.jwt import decode_token
from app.types.enums import OfficerRole

logger = logging.getLogger("crimegpt.auth")

# Demo user UUID — matches the one in authService.py
_DEMO_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")

# Security scheme — extracts Bearer token from Authorization header
_bearer_scheme = HTTPBearer(auto_error=True)


@dataclass
class DemoOfficer:
    """Lightweight stand-in for Officer ORM model in demo mode.
    Duck-types the Officer interface without touching SQLAlchemy instrumentation."""
    id: uuid.UUID = field(default_factory=lambda: _DEMO_UUID)
    name: str = "Admin Officer (Demo)"
    badge_no: str = "PN-2024-ADMIN"
    role: OfficerRole = OfficerRole.ADMIN
    station_id: uuid.UUID | None = None
    password_hash: str = "demo"
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def _create_demo_officer() -> DemoOfficer:
    """Create a demo officer instance for demo mode (no DB needed)."""
    return DemoOfficer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis | None = Depends(get_redis),
) -> Officer:
    """
    FastAPI dependency — extracts and validates JWT, returns Officer ORM object.

    This is injected into every protected route.
    Raises 401 if token is invalid/expired/missing or session is revoked.
    """
    token = credentials.credentials

    # 1. Decode JWT
    try:
        payload = decode_token(token)
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Validate token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected access token",
        )

    # 3. Extract officer ID
    officer_id_str = payload.get("sub")
    if not officer_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )

    try:
        officer_id = uuid.UUID(officer_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid officer ID in token",
        )

    # --- DEMO BYPASS: Return mock officer without DB lookup ---
    if officer_id == _DEMO_UUID:
        logger.debug("Demo user bypass — returning mock Officer")
        return _create_demo_officer()

    # 4. Check Redis session (if Redis is available)
    if redis:
        try:
            session = await redis.get(f"session:{officer_id}")
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired or logged out — please log in again",
                )
        except HTTPException:
            raise
        except Exception:
            # Redis connection failed — skip session check
            logger.warning("Redis unavailable — skipping session check")

    # 5. Load officer from DB
    try:
        repo = OfficerRepository(db)
        officer = await repo.get_by_id(officer_id)
    except Exception as e:
        logger.error(f"DB error loading officer: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )

    if not officer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Officer not found",
        )

    if not officer.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated — contact station head",
        )

    return officer

