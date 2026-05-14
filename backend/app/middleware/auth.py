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

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.redis import get_redis
from app.models.officer import Officer
from app.repositories.OfficerRepository import OfficerRepository
from app.utils.jwt import decode_token

logger = logging.getLogger("crimegpt.auth")

# Security scheme — extracts Bearer token from Authorization header
_bearer_scheme = HTTPBearer(auto_error=True)


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

    # 4. Check Redis session (if Redis is available)
    if redis:
        session = await redis.get(f"session:{officer_id}")
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or logged out — please log in again",
            )

    # 5. Load officer from DB
    repo = OfficerRepository(db)
    officer = await repo.get_by_id(officer_id)

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
