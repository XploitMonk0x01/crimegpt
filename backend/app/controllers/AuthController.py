"""
Auth controller — coordinates auth request/response flow.

Controllers MUST NOT contain business logic.
They only: parse request → call service → return response.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.controllers import BaseController
from app.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    OfficerProfile,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterOfficerRequest,
)
from app.services.authService import AuthService

logger = logging.getLogger("crimegpt.controller.auth")


class AuthController(BaseController):
    """Handles auth-related HTTP operations."""

    def __init__(self, auth_service: AuthService):
        self._service = auth_service

    async def login(self, request: LoginRequest, http_request: Request) -> JSONResponse:
        """Handle login request."""
        try:
            client_ip = http_request.client.host if http_request.client else "unknown"
            result: LoginResponse = await self._service.login(request, ip_address=client_ip)
            return self.handle_success(
                data=result.model_dump(mode="json"),
                message="Login successful",
            )
        except Exception as e:
            if hasattr(e, "status_code"):
                raise  # Let HTTPExceptions propagate to global handler
            return self.handle_error(e, context="AuthController.login")

    async def refresh(self, request: RefreshTokenRequest) -> JSONResponse:
        """Handle token refresh request."""
        try:
            result: RefreshTokenResponse = await self._service.refresh_token(request)
            return self.handle_success(
                data=result.model_dump(mode="json"),
                message="Token refreshed",
            )
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return self.handle_error(e, context="AuthController.refresh")

    async def logout(self, officer_id) -> JSONResponse:
        """Handle logout request."""
        try:
            await self._service.logout(officer_id)
            return self.handle_success(message="Logged out successfully")
        except Exception as e:
            return self.handle_error(e, context="AuthController.logout")

    async def me(self, officer_id) -> JSONResponse:
        """Return current officer profile."""
        try:
            profile: OfficerProfile = await self._service.get_officer_by_id(officer_id)
            return self.handle_success(
                data=profile.model_dump(mode="json"),
                message="OK",
            )
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return self.handle_error(e, context="AuthController.me")

    async def register(self, request: RegisterOfficerRequest) -> JSONResponse:
        """Register a new officer (Admin only)."""
        try:
            profile: OfficerProfile = await self._service.register_officer(request)
            return self.handle_created(
                data=profile.model_dump(mode="json"),
                message="Officer registered successfully",
            )
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return self.handle_error(e, context="AuthController.register")
