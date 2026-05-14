import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import Base, engine

# Import all models so Base knows about them
from app.models.officer import Officer
from app.models.fir import FIR
from app.models.evidence import Evidence
from app.models.case_link import CaseLink

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crimegpt.init_db")

async def init_db():
    async with engine.begin() as conn:
        logger.info("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
