"""
YUGI-AI — Auth Domain Events
===============================

Domain events published by the authentication module.
Consumed by subscribers (notifications, analytics, security monitoring).

Events are immutable (frozen=True) and carry contextual metadata.

Usage:
    from app.domain.auth.events import UserRegisteredEvent

    event = UserRegisteredEvent(user_id=str(user.id), email=user.email)
    await event_bus.publish(event.to_domain_event())
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.base import DomainEvent

# =============================================================================
# Event Factory Mixin
# =============================================================================


@dataclass(frozen=True)
class AuthEvent:
    """Base for auth-specific events. Provides conversion to DomainEvent."""

    correlation_id: str | None = None

    def to_domain_event(self) -> DomainEvent:
        """Convert to a generic DomainEvent for the EventBus."""
        # Build payload from all fields except correlation_id
        payload: dict[str, Any] = {}
        for f_name in self.__dataclass_fields__:
            if f_name == "correlation_id":
                continue
            value = getattr(self, f_name)
            if isinstance(value, datetime):
                payload[f_name] = value.isoformat()
            elif value is not None:
                if not isinstance(value, (str, int, float, bool, dict)):
                    payload[f_name] = str(value)
                else:
                    payload[f_name] = value

        return DomainEvent(
            event_type=f"auth.{self._event_name}",
            payload=payload,
            correlation_id=self.correlation_id,
        )

    @property
    def _event_name(self) -> str:
        """Derived event name from class. UserRegisteredEvent → user_registered."""
        name = self.__class__.__name__
        if name.endswith("Event"):
            name = name[:-5]
        # CamelCase → snake_case
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())
        return "".join(result)


# =============================================================================
# Auth Events
# =============================================================================


@dataclass(frozen=True)
class UserRegisteredEvent(AuthEvent):
    """Published after successful user registration."""

    user_id: str = ""
    email: str = ""
    username: str = ""


@dataclass(frozen=True)
class LoginSucceededEvent(AuthEvent):
    """Published after successful authentication."""

    user_id: str = ""
    identifier: str = ""  # email or username used to login
    session_id: str = ""
    ip_address: str | None = None


@dataclass(frozen=True)
class LoginFailedEvent(AuthEvent):
    """Published when authentication fails (wrong password or user not found)."""

    identifier: str = ""  # The email/username attempted
    reason: str = ""  # "invalid_credentials" or "user_not_found"
    ip_address: str | None = None


@dataclass(frozen=True)
class TokenRefreshedEvent(AuthEvent):
    """Published after successful token rotation."""

    user_id: str = ""
    session_id: str = ""


@dataclass(frozen=True)
class SuspiciousRefreshEvent(AuthEvent):
    """Published when a rotated (invalidated) refresh token is reused.

    This indicates potential token theft. All user sessions are revoked.
    """

    user_id: str = ""
    session_id: str = ""
    ip_address: str | None = None


@dataclass(frozen=True)
class UserLoggedOutEvent(AuthEvent):
    """Published after explicit logout."""

    user_id: str = ""
    session_id: str = ""


@dataclass(frozen=True)
class AllSessionsRevokedEvent(AuthEvent):
    """Published when all sessions for a user are revoked."""

    user_id: str = ""
    session_count: int = 0
    reason: str = ""  # "user_request", "theft_detected", "password_changed"


@dataclass(frozen=True)
class PasswordChangedEvent(AuthEvent):
    """Published after a successful password change."""

    user_id: str = ""
