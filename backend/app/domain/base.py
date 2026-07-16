"""
YUGI-AI — Base Domain Classes
===============================

Foundation classes for all domain entities and events.

Design Principles:
    - Entities are identified by their ID (equality based on ID, not fields)
    - Entities are immutable value holders — mutation happens via service methods
    - Domain events capture "something that happened" for event-driven architecture
    - No framework dependencies — pure Python dataclasses

Usage:
    from app.domain.base import BaseEntity, DomainEvent

    @dataclass
    class User(BaseEntity):
        email: str
        username: str
        display_name: str
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.types import EntityId

# =============================================================================
# Base Entity
# =============================================================================


@dataclass
class BaseEntity:
    """Base class for all domain entities.

    Every entity in the system has:
    - A UUID primary key (generated if not provided)
    - Created/updated timestamps
    - Identity-based equality (two entities with the same ID are equal)

    Subclasses add domain-specific fields:
        @dataclass
        class User(BaseEntity):
            email: str
            username: str
    """

    id: EntityId = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = field(default=None)

    def __eq__(self, other: object) -> bool:
        """Two entities are equal if they have the same ID."""
        if not isinstance(other, BaseEntity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on entity ID for use in sets and dict keys."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Human-readable representation showing class name and ID."""
        return f"<{self.__class__.__name__} id={self.id}>"

    def touch(self) -> None:
        """Update the `updated_at` timestamp to now.

        Call this in service methods when modifying an entity.
        """
        self.updated_at = datetime.now(UTC)


# =============================================================================
# Domain Event
# =============================================================================


@dataclass(frozen=True)
class DomainEvent:
    """Base class for domain events.

    Domain events represent "something that happened" in the business domain.
    They are published via the EventBus and consumed by event handlers.

    Events are immutable (frozen=True) — once created, they cannot be modified.

    Attributes:
        event_type: Dot-separated event identifier (e.g., "user.created", "chat.message.sent")
        occurred_at: When the event happened (UTC)
        payload: Event-specific data (entity ID, changed fields, etc.)
        correlation_id: Links this event to the originating request

    Usage:
        user_created = DomainEvent(
            event_type="user.created",
            payload={"user_id": str(user.id), "email": user.email},
            correlation_id="550e8400-...",
        )
        await event_bus.publish(user_created)
    """

    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = field(default=None)

    @property
    def event_name(self) -> str:
        """Short name for logging — last segment of the event type.

        "user.created" → "created"
        """
        return self.event_type.rsplit(".", maxsplit=1)[-1]
