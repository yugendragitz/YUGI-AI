"""
YUGI-AI — Redis Infrastructure
=================================

Async Redis client manager. Mirrors the DatabaseManager pattern from Module 2.

Roles:
    - Rate limiting counters (sliding window)
    - Session cache (future)
    - Pub/Sub event bus (future)
    - General cache (future)

Usage:
    from app.infrastructure.redis import RedisManager

    redis_mgr = RedisManager(settings.redis)
    await redis_mgr.connect()
    client = redis_mgr.client
    await client.set("key", "value", ex=60)
    await redis_mgr.disconnect()
"""

from __future__ import annotations

import structlog
from redis.asyncio import Redis, from_url

from app.core.config import RedisSettings

logger = structlog.get_logger(__name__)


class RedisManager:
    """Manages async Redis connections.

    Lifecycle:
        1. __init__: Store config (no connection yet)
        2. connect(): Create Redis client, verify connectivity
        3. client: Property to access the client
        4. disconnect(): Close connection pool
    """

    def __init__(self, settings: RedisSettings) -> None:
        self._settings = settings
        self._client: Redis | None = None

    async def connect(self) -> None:
        """Create Redis client and verify connectivity.

        Does NOT raise on failure — the application can start without Redis.
        Rate limiter falls back to in-memory mode.
        """
        try:
            self._client = from_url(
                self._settings.url,
                max_connections=self._settings.pool_max_size,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Verify connectivity
            await self._client.ping()
            logger.info(
                "Redis connection established",
                host=self._settings.host,
                port=self._settings.port,
                db=self._settings.db,
            )
        except Exception as exc:
            logger.warning(
                "Redis connection failed — rate limiting will use in-memory fallback",
                host=self._settings.host,
                port=self._settings.port,
                error=str(exc),
            )
            self._client = None

    async def disconnect(self) -> None:
        """Close Redis connection pool."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Redis connection closed")

    @property
    def client(self) -> Redis | None:
        """Get the Redis client. Returns None if not connected."""
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if Redis is available."""
        return self._client is not None

    async def check_connectivity(self) -> bool:
        """Health check — ping Redis.

        Returns:
            True if Redis responds to ping.
        """
        if self._client is None:
            return False
        try:
            return bool(await self._client.ping())
        except Exception:
            return False
