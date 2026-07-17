"""
YUGI-AI — Rate Limiter
========================

Sliding window rate limiter using Redis INCR + EXPIRE.
Falls back to in-memory counters when Redis is unavailable.

Algorithm:
    Key: "rate:{endpoint}:{client_id}"
    On each request:
        1. INCR key → current count
        2. If count == 1 (first request in window): EXPIRE key = window_seconds
        3. If count > limit: reject with 429

Usage:
    from app.infrastructure.rate_limiter import RateLimiter, RateLimitResult

    limiter = RateLimiter(redis_client=redis.client)
    result = await limiter.check("login", ip_address, limit=5, window_seconds=900)
    if not result.allowed:
        raise RateLimitException(retry_after=result.retry_after)
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger(__name__)


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    """Whether the request is allowed."""

    remaining: int
    """Number of requests remaining in the current window."""

    reset_at: int
    """Unix timestamp when the window resets."""

    retry_after: int
    """Seconds until the next request will be allowed (0 if allowed)."""


# In-memory fallback storage
_memory_store: dict[str, list[float]] = defaultdict(list)


class RateLimiter:
    """Sliding window rate limiter with Redis primary and in-memory fallback.

    Redis mode: Atomic INCR + EXPIRE (distributed, multi-instance safe).
    Memory mode: Timestamp list per key (single-instance only).
    """

    def __init__(self, redis_client: Redis | None = None) -> None:
        self._redis = redis_client

    async def check(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Check if a request is within the rate limit.

        Args:
            key: Rate limit key (e.g., "rate:login:192.168.1.1").
            limit: Maximum allowed requests in the window.
            window_seconds: Duration of the rate limit window.

        Returns:
            RateLimitResult with allowed status, remaining count, and reset time.
        """
        if self._redis is not None:
            try:
                return await self._check_redis(key, limit=limit, window_seconds=window_seconds)
            except Exception:
                logger.warning("Redis rate limit check failed — falling back to in-memory")

        return self._check_memory(key, limit=limit, window_seconds=window_seconds)

    async def _check_redis(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Redis-based rate limit using INCR + EXPIRE."""
        assert self._redis is not None  # noqa: S101

        pipe = self._redis.pipeline(transaction=True)
        pipe.incr(key)
        pipe.ttl(key)
        count, ttl = await pipe.execute()

        # Set expiry on first request in the window
        if count == 1 or ttl == -1:
            await self._redis.expire(key, window_seconds)
            ttl = window_seconds

        remaining = max(0, limit - count)
        reset_at = int(time.time()) + max(0, ttl)
        allowed = count <= limit
        retry_after = 0 if allowed else max(0, ttl)

        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=retry_after,
        )

    @staticmethod
    def _check_memory(
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """In-memory rate limit using timestamp list (single-instance fallback)."""
        now = time.time()
        window_start = now - window_seconds

        # Clean expired entries
        _memory_store[key] = [ts for ts in _memory_store[key] if ts > window_start]

        count = len(_memory_store[key])
        remaining = max(0, limit - count - 1)  # -1 because we're about to add one
        reset_at = int(now) + window_seconds
        allowed = count < limit

        if allowed:
            _memory_store[key].append(now)
            remaining = max(0, limit - count - 1)
        else:
            # Find when the oldest entry in the window expires
            oldest = min(_memory_store[key]) if _memory_store[key] else now
            retry_after = int(oldest + window_seconds - now) + 1
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=int(oldest + window_seconds),
                retry_after=max(1, retry_after),
            )

        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=0,
        )
