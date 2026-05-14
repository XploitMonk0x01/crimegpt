"""
JWT token creation and verification.

Usage:
    from app.utils.jwt import create_access_token, create_refresh_token, decode_token

    token = create_access_token(data={"sub": str(officer.id), "role": officer.role})
    payload = decode_token(token)  # raises JWTError on invalid/expired
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import get_settings


def create_access_token(data: dict[str, Any]) -> str:
    """
    Create a short-lived access token (default: 8 hours).

    The `sub` field MUST contain the officer UUID as a string.
    """
    settings = get_settings()
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(hours=settings.auth.jwt_expiry_hours)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
        "type": "access",
    })

    return jwt.encode(
        to_encode,
        settings.auth.jwt_secret,
        algorithm=settings.auth.jwt_algorithm,
    )


def create_refresh_token(data: dict[str, Any]) -> str:
    """
    Create a long-lived refresh token (default: 7 days).

    Used for silent token rotation without re-login.
    """
    settings = get_settings()
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(days=settings.auth.refresh_token_expiry_days)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    })

    return jwt.encode(
        to_encode,
        settings.auth.jwt_secret,
        algorithm=settings.auth.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Raises:
        JWTError: if token is invalid, expired, or tampered with
    """
    settings = get_settings()
    return jwt.decode(
        token,
        settings.auth.jwt_secret,
        algorithms=[settings.auth.jwt_algorithm],
    )
