import asyncio
import uuid
from app.db.session import async_session_factory
from app.models.officer import Officer
from app.types.enums import OfficerRole

async def seed():
    async with async_session_factory() as db:
        demo_uuid = uuid.UUID('00000000-0000-0000-0000-000000000000')
        res = await db.get(Officer, demo_uuid)
        if not res:
            print("Seeding demo officer...")
            officer = Officer(
                id=demo_uuid,
                name="Admin Officer (Demo)",
                badge_no="PN-2024-ADMIN",
                role=OfficerRole.ADMIN,
                password_hash="demo", # Not actually used in bypass but good for consistency
                is_active=True
            )
            db.add(officer)
            await db.commit()
            print("Demo officer seeded successfully.")
        else:
            print("Demo officer already exists.")

if __name__ == "__main__":
    asyncio.run(seed())
