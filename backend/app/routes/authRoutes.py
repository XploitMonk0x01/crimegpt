"""
Auth routes — FastAPI router for authentication endpoints.

Routes contain ZERO business logic. They only:
    1. Declare the HTTP method, path, and dependencies
    2. Parse the request body (via Pydantic type hints)
    3. Call the controller method
    4. Return the controller's response

Endpoints:
    POST /login       — authenticate and receive JWT pair
    POST /refresh     — rotate refresh token
    POST /logout      — invalidate session
    GET  /me          — get current officer profile
    POST /register    — register new officer (Admin only)
"""

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.AuthController import AuthController
from app.db.session import get_db
from app.db.redis import get_redis
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_role
from app.middleware.rate_limiter import rate_limit
from app.models.officer import Officer
from app.schemas.auth_schema import LoginRequest, RefreshTokenRequest, RegisterOfficerRequest
from app.services.authService import AuthService
from app.types.enums import OfficerRole

router = APIRouter()


def _get_auth_controller(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis | None = Depends(get_redis),
) -> AuthController:
    """Factory — creates AuthController with injected dependencies."""
    service = AuthService(db, redis)
    return AuthController(service)


@router.post(
    "/login",
    summary="Officer Login",
    description="Authenticate with badge number and PIN. Returns JWT access + refresh tokens.",
    dependencies=[Depends(rate_limit(max_requests=5, window_seconds=60))],
)
async def login(
    body: LoginRequest,
    request: Request,
    controller: AuthController = Depends(_get_auth_controller),
):
    return await controller.login(body, request)


@router.post(
    "/refresh",
    summary="Refresh Token",
    description="Exchange a valid refresh token for a new access + refresh token pair.",
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))],
)
async def refresh_token(
    body: RefreshTokenRequest,
    controller: AuthController = Depends(_get_auth_controller),
):
    return await controller.refresh(body)


@router.post(
    "/logout",
    summary="Logout",
    description="Invalidate the current session. Requires authentication.",
)
async def logout(
    officer: Officer = Depends(get_current_user),
    controller: AuthController = Depends(_get_auth_controller),
):
    return await controller.logout(officer.id)


@router.get(
    "/me",
    summary="Current Officer Profile",
    description="Get the authenticated officer's profile.",
)
async def me(
    officer: Officer = Depends(get_current_user),
    controller: AuthController = Depends(_get_auth_controller),
):
    return await controller.me(officer.id)


@router.post(
    "/register",
    summary="Register Officer",
    description="Register a new officer account. Admin only.",
    dependencies=[Depends(require_role(OfficerRole.ADMIN, OfficerRole.STATION_HEAD))],
)
async def register_officer(
    body: RegisterOfficerRequest,
    controller: AuthController = Depends(_get_auth_controller),
):
    return await controller.register(body)
