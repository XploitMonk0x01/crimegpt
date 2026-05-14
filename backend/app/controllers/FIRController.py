"""
FIR controller — coordinates FIR request/response flow.

Controllers MUST NOT contain business logic.
"""

import logging
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from app.controllers import BaseController
from app.models.officer import Officer
from app.schemas.fir_schema import (
    FIRApproveRejectRequest,
    FIREditRequest,
    FIRGenerateRequest,
    FIRSubmitRequest,
)
from app.services.firService import FIRService
from app.types.enums import FIRStatus

logger = logging.getLogger("crimegpt.controller.fir")


class FIRController(BaseController):
    """Handles FIR-related HTTP operations."""

    def __init__(self, fir_service: FIRService):
        self._service = fir_service

    async def generate_draft(self, request: FIRGenerateRequest, officer: Officer) -> JSONResponse:
        try:
            result = await self._service.generate_draft(request, officer)
            return self.handle_success(data=result.model_dump(mode="json"), message="FIR draft generated")
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return self.handle_error(e, context="FIRController.generate_draft")

    async def submit(self, request: FIRSubmitRequest, officer: Officer, http_request: Request) -> JSONResponse:
        try:
            ip = http_request.client.host if http_request.client else "unknown"
            result = await self._service.submit_fir(request, officer, ip)
            return self.handle_created(data=result.model_dump(mode="json"), message="FIR submitted")
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return self.handle_error(e, context="FIRController.submit")

    async def edit(self, fir_id: uuid.UUID, request: FIREditRequest, officer: Officer) -> JSONResponse:
        try:
            result = await self._service.edit_fir(fir_id, request, officer)
            return self.handle_success(data=result.model_dump(mode="json"), message="FIR updated")
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return self.handle_error(e, context="FIRController.edit")

    async def approve_reject(self, fir_id: uuid.UUID, request: FIRApproveRejectRequest, officer: Officer) -> JSONResponse:
        try:
            result = await self._service.approve_reject(fir_id, request, officer)
            action_word = "approved" if request.action == "approve" else "rejected"
            return self.handle_success(data=result.model_dump(mode="json"), message=f"FIR {action_word}")
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return self.handle_error(e, context="FIRController.approve_reject")

    async def get_fir(self, fir_id: uuid.UUID, officer: Officer) -> JSONResponse:
        try:
            result = await self._service.get_fir(fir_id, officer)
            return self.handle_success(data=result.model_dump(mode="json"))
        except Exception as e:
            if hasattr(e, "status_code"):
                raise
            return self.handle_error(e, context="FIRController.get_fir")

    async def list_firs(self, officer: Officer, status_filter: FIRStatus | None, page: int, page_size: int) -> JSONResponse:
        try:
            firs, total = await self._service.list_firs(officer, status_filter=status_filter, page=page, page_size=page_size)
            data = [f.model_dump(mode="json") for f in firs]
            return self.handle_paginated(data=data, page=page, page_size=page_size, total_items=total)
        except Exception as e:
            return self.handle_error(e, context="FIRController.list_firs")
