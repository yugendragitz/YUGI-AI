"""
YUGI-AI — Domain Interfaces (Ports)
=====================================

Abstract base classes that define what the domain layer NEEDS from infrastructure.
Infrastructure layer PROVIDES the implementations (adapters).

This is the "Ports" in Ports & Adapters (Hexagonal Architecture):
    Port:    BaseRepository[T]           ← defined here
    Adapter: PostgresUserRepository      ← implemented in infrastructure/

Dependency Rule:
    Domain defines interfaces → Infrastructure implements them
    Domain NEVER imports from infrastructure

Usage:
    from app.domain.interfaces import BaseRepository

    class UserRepository(BaseRepository[User]):
        # Inherits: get_by_id, get_all, create, update, delete
        async def get_by_email(self, email: str) -> User | None: ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.core.types import EntityId
from app.domain.base import DomainEvent

# =============================================================================
# Repository Interface
# =============================================================================


class BaseRepository[T](ABC):
    """Abstract base repository defining standard CRUD operations.

    Every entity repository inherits from this and may add
    domain-specific query methods.

    Type Parameter:
        T: The domain entity type this repository manages.

    Example:
        class UserRepository(BaseRepository[User]):
            async def get_by_email(self, email: str) -> User | None: ...
            async def get_by_username(self, username: str) -> User | None: ...
    """

    @abstractmethod
    async def get_by_id(self, entity_id: EntityId) -> T | None:
        """Retrieve an entity by its unique ID.

        Returns None if the entity does not exist.
        """

    @abstractmethod
    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        **filters: Any,
    ) -> list[T]:
        """Retrieve a paginated list of entities with optional filters.

        Args:
            offset: Number of records to skip.
            limit: Maximum number of records to return.
            **filters: Domain-specific filter criteria.
        """

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Persist a new entity. Returns the created entity with generated fields."""

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity. Returns the updated entity."""

    @abstractmethod
    async def delete(self, entity_id: EntityId) -> bool:
        """Delete an entity by ID. Returns True if deleted, False if not found."""

    @abstractmethod
    async def count(self, **filters: Any) -> int:
        """Count entities matching the given filters."""


# =============================================================================
# Cache Interface
# =============================================================================


class CacheService(ABC):
    """Abstract cache interface.

    Implemented by Redis in infrastructure. Can be swapped for
    in-memory cache during testing.

    Keys should use prefixes from app.core.constants (e.g., "session:", "user:").
    """

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Get a cached value by key. Returns None if not found or expired."""

    @abstractmethod
    async def set(
        self,
        key: str,
        value: str,
        *,
        expire_seconds: int | None = None,
    ) -> None:
        """Set a cached value with optional TTL.

        Args:
            key: Cache key.
            value: Value to cache (serialized to string).
            expire_seconds: Time-to-live in seconds. None = no expiration.
        """

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a cached value. Returns True if the key existed."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""

    @abstractmethod
    async def expire(self, key: str, seconds: int) -> bool:
        """Set or update the TTL on an existing key.

        Returns True if the timeout was set, False if the key doesn't exist.
        """

    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increment a counter. Returns the new value.

        Creates the key with value `amount` if it doesn't exist.
        Used for rate limiting counters.
        """


# =============================================================================
# Event Bus Interface
# =============================================================================


class EventBus(ABC):
    """Abstract event bus for publishing and subscribing to domain events.

    Phase 1: Redis Pub/Sub implementation.
    Future: Kafka, RabbitMQ, or AWS SNS/SQS.

    Events decouple modules — a notification module subscribes to
    "user.created" without importing from the auth module.
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all subscribers.

        Args:
            event: The domain event to publish.
        """

    @abstractmethod
    async def subscribe(
        self,
        event_type: str,
        handler: Any,
    ) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Event type pattern (e.g., "user.created", "chat.*").
            handler: Async callable invoked when a matching event is published.
        """
