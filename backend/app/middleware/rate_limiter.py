"""
Redis-based rate limiter — FastAPI dependency factory.

Usage:
    @router.post("/login", dependencies=[Depends(rate_limit(max_requests=5, window_seconds=60))])
    async def login():
        ...

Implements a sliding window rate limiter using Redis INCR + EXPIRE.
Falls back to no rate limiting if Redis is unavailable (hackathon-safe).
"""

import logging

from fastapi import Depends, HTTPException, Request, status
import redis.asyncio as aioredis

from app.db.redis import get_redis

logger = logging.getLogger("crimegpt.ratelimit")


def rate_limit(max_requests: int = 30, window_seconds: int = 60):
    """
    Dependency factory — returns a FastAPI dependency that enforces rate limiting.

    Args:
        max_requests: Maximum number of requests per window
        window_seconds: Window duration in seconds
    """

    async def _rate_limiter(
        request: Request,
        redis: aioredis.Redis | None = Depends(get_redis),
    ) -> None:
        if not redis:
            # No Redis = no rate limiting (graceful degradation)
            return

        # Key based on client IP + route path
        client_ip = request.client.host if request.client else "unknown"
        key = f"rl:{client_ip}:{request.url.path}"

        try:
            # Increment request count
            current = await redis.incr(key)

            # Set TTL on first request
            if current == 1:
                await redis.expire(key, window_seconds)

            if current > max_requests:
                ttl = await redis.ttl(key)
                logger.warning(f"Rate limit exceeded: {client_ip} on {request.url.path}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
                    headers={"Retry-After": str(ttl)},
                )
        except HTTPException:
            raise
        except Exception as e:
            # Redis error — fail open (don't block requests because of Redis issues)
            logger.error(f"Rate limiter Redis error: {e}")

    return _rate_limiter
