"""
RBAC (Role-Based Access Control) middleware — FastAPI dependency factory.

Usage in routes:
    @router.post("/admin-only", dependencies=[Depends(require_role(OfficerRole.ADMIN))])
    async def handler(officer: Officer = Depends(get_current_user)):
        ...

    @router.post("/inspector-up", dependencies=[Depends(require_role(OfficerRole.INSPECTOR, OfficerRole.STATION_HEAD, OfficerRole.ADMIN))])
    async def handler(officer: Officer = Depends(get_current_user)):
        ...
"""

import logging

from fastapi import Depends, HTTPException, status

from app.middleware.auth import get_current_user
from app.models.officer import Officer
from app.types.enums import OfficerRole

logger = logging.getLogger("crimegpt.rbac")


def require_role(*allowed_roles: OfficerRole):
    """
    Dependency factory — returns a FastAPI dependency that enforces role-based access.

    Usage:
        dependencies=[Depends(require_role(OfficerRole.ADMIN, OfficerRole.STATION_HEAD))]
    """

    async def _role_checker(
        officer: Officer = Depends(get_current_user),
    ) -> Officer:
        if officer.role not in allowed_roles:
            logger.warning(
                f"RBAC denied: {officer.badge_no} ({officer.role.value}) "
                f"tried to access endpoint requiring {[r.value for r in allowed_roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(r.value for r in allowed_roles)}",
            )
        return officer

    return _role_checker
