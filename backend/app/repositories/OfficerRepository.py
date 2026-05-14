"""
Officer repository — data access for officer accounts.

All officer-related database queries live here.
Never call SQLAlchemy directly from services or controllers.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.officer import Officer
from app.repositories.base import BaseRepository


class OfficerRepository(BaseRepository[Officer]):
    """Officer-specific data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(Officer, db)

    async def get_by_badge_no(self, badge_no: str) -> Officer | None:
        """Look up an officer by their unique badge number."""
        return await self.get_one(badge_no=badge_no.strip().upper())

    async def badge_exists(self, badge_no: str) -> bool:
        """Check if a badge number is already registered."""
        officer = await self.get_by_badge_no(badge_no)
        return officer is not None
