import asyncio
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory, Base, engine
from app.models.officer import Officer
from app.utils.hashing import hash_password
from app.types.enums import OfficerRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crimegpt.seed")

async def seed_data():
    """Seed the database with a default officer account."""
    async with async_session_factory() as session:
        # Check if officer already exists
        from sqlalchemy import select
        result = await session.execute(select(Officer).where(Officer.badge_no == "PN-2024-ADMIN"))
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info("Admin officer already exists. Skipping seed.")
            return

        admin_officer = Officer(
            id=uuid.uuid4(),
            name="Admin Officer",
            badge_no="PN-2024-ADMIN",
            role=OfficerRole.ADMIN,
            password_hash=hash_password("1234"),
            is_active=True
        )
        
        session.add(admin_officer)
        await session.commit()
        logger.info("Successfully seeded default officer: PN-2024-ADMIN / 1234")

if __name__ == "__main__":
    asyncio.run(seed_data())
