"""
Redis async client for session caching and rate limiting.

Provides:
    - Async Redis client singleton
    - `get_redis` dependency for FastAPI route injection
"""

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.config import get_settings

settings = get_settings()

redis_client = aioredis.from_url(
    settings.redis.url,
    decode_responses=True,
)


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    FastAPI dependency — yields the Redis async client.

    Usage in routes:
        @router.get("/")
        async def handler(redis: Redis = Depends(get_redis)):
            ...
    """
    yield redis_client


async def close_redis() -> None:
    """Close the Redis connection pool. Call on app shutdown."""
    await redis_client.aclose()
