"""
YUGI-AI — Auth Domain Entities
=================================

Pure Python dataclasses representing the core authentication domain objects.
These have NO dependency on SQLAlchemy, FastAPI, or any framework.

Entity ↔ ORM Model mapping happens in the infrastructure layer:
    Domain entity (User)  ←→  ORM model (UserModel)

Usage:
    from app.domain.auth.entities import User, Session, AuditLog

    user = User(email="user@yugi.ai", username="yugi", ...)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.constants import UserRole
from app.core.types import EntityId
from app.domain.base import BaseEntity

# =============================================================================
# User Entity
# =============================================================================


@dataclass
class User(BaseEntity):
    """Domain entity representing a user account.

    Fields:
        - Identity: email, username, display_name
        - Auth: password_hash, role, is_active, is_verified
        - Avatar: seed + style for DiceBear (Phase 1), avatar_url for custom (Phase 2)
        - Metadata: last_login_at, inherited created_at/updated_at/deleted_at
    """

    # Identity
    email: str = ""
    username: str = ""
    display_name: str = ""

    # Authentication
    password_hash: str = ""
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False  # Phase 2: email verification

    # Avatar (ADR-016: DiceBear in Phase 1)
    avatar_seed: str = field(default_factory=lambda: str(uuid.uuid4()))
    avatar_style: str = "bottts"
    avatar_url: str | None = None  # Phase 2: custom upload

    # Metadata
    last_login_at: datetime | None = None


# =============================================================================
# Session Entity
# =============================================================================


@dataclass
class Session(BaseEntity):
    """Domain entity representing an active authentication session.

    Each login creates a new Session. The refresh token (SHA-256 hash)
    is stored here. Token rotation creates a new hash and revokes the old one.

    Fields:
        - user_id: FK to User
        - refresh_token_hash: SHA-256 of the refresh token (never plaintext)
        - Device info: for "Active Sessions" UI
        - Lifecycle: is_revoked, expires_at, last_used_at
    """

    # Relationships
    user_id: EntityId = field(default_factory=uuid.uuid4)

    # Token (stored as SHA-256 hash — NEVER plaintext)
    refresh_token_hash: str = ""

    # Device info (for "Active Sessions" UI in Identity module)
    device_name: str | None = None  # e.g., "Chrome on Windows"
    ip_address: str | None = None  # IPv4 or IPv6
    user_agent: str | None = None

    # Lifecycle
    is_revoked: bool = False
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_used_at: datetime | None = None


# =============================================================================
# Audit Log Entity
# =============================================================================


@dataclass
class AuditLog(BaseEntity):
    """Domain entity representing an authentication audit trail entry.

    Append-only: audit logs are never updated or deleted.

    Fields:
        - user_id: The user who performed the action (nullable for failed login)
        - event_type: AuditEventType string (e.g., "LOGIN_SUCCESS")
        - ip_address, user_agent: Client info
        - metadata: Event-specific JSONB data
        - correlation_id: Links to the request that triggered this event
    """

    user_id: EntityId | None = None
    event_type: str = ""
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
