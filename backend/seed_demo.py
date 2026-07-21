"""
Seed all 3 demo officers for the CrimeGPT demo.

Roles and credentials:
    Admin Officer  — badge: PN-2024-ADMIN  pin: 1234  (OfficerRole.ADMIN)
    SHO Officer    — badge: PN-2024-SHO    pin: 5678  (OfficerRole.STATION_HEAD)
    IO Officer     — badge: PN-2024-IO     pin: 5678  (OfficerRole.INSPECTOR)

Run:
    cd backend && ./venv/bin/python seed_demo.py
"""

import asyncio
import uuid

from app.db.session import async_session_factory
from app.models.officer import Officer
from app.types.enums import OfficerRole
from app.utils.hashing import hash_password


DEMO_OFFICERS = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000000"),
        "name": "Admin Officer (Demo)",
        "badge_no": "PN-2024-ADMIN",
        "role": OfficerRole.ADMIN,
        "pin": "1234",
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "name": "SHO Officer (Demo)",
        "badge_no": "PN-2024-SHO",
        "role": OfficerRole.STATION_HEAD,
        "pin": "5678",
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "name": "IO Officer (Demo)",
        "badge_no": "PN-2024-IO",
        "role": OfficerRole.INSPECTOR,
        "pin": "5678",
    },
]


async def seed():
    async with async_session_factory() as db:
        for spec in DEMO_OFFICERS:
            existing = await db.get(Officer, spec["id"])
            if not existing:
                print(f"Seeding demo officer: {spec['badge_no']} ({spec['role'].value})...")
                officer = Officer(
                    id=spec["id"],
                    name=spec["name"],
                    badge_no=spec["badge_no"],
                    role=spec["role"],
                    password_hash=hash_password(spec["pin"]),
                    is_active=True,
                )
                db.add(officer)
                print(f"  ✓ {spec['badge_no']} seeded.")
            else:
                # Update role in case it changed (useful for re-seeding after schema changes)
                if existing.role != spec["role"]:
                    existing.role = spec["role"]
                    print(f"  ↻ {spec['badge_no']} role updated to {spec['role'].value}.")
                else:
                    print(f"  — {spec['badge_no']} already exists, skipping.")

        await db.commit()
        print("Demo officer seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
