"""
YUGI-AI — Auth Repository Interfaces (Ports)
===============================================

Abstract repository contracts for the auth domain.
Infrastructure provides the PostgreSQL implementations.

Dependency Rule:
    Domain defines → Infrastructure implements
"""

from __future__ import annotations

from abc import abstractmethod

from app.core.types import EntityId
from app.domain.auth.entities import AuditLog, Session, User
from app.domain.interfaces import BaseRepository

# =============================================================================
# User Repository
# =============================================================================


class UserRepository(BaseRepository[User]):
    """Repository interface for User entity CRUD and lookups.

    Extends BaseRepository with auth-specific query methods.
    All queries automatically filter out soft-deleted users (deleted_at IS NULL)
    unless include_deleted=True is passed.
    """

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Find a user by email address. Returns None if not found."""

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Find a user by username. Returns None if not found."""

    @abstractmethod
    async def get_by_identifier(self, identifier: str) -> User | None:
        """Find a user by email OR username.

        Auto-detects: if identifier contains '@', search by email; otherwise by username.
        Used for the login endpoint's dual-mode authentication.
        """

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if a user with this email exists (among non-deleted users)."""

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if a user with this username exists (among non-deleted users)."""


# =============================================================================
# Session Repository
# =============================================================================


class SessionRepository(BaseRepository[Session]):
    """Repository interface for Session entity management.

    Sessions are never physically deleted — they are revoked (is_revoked=True)
    or soft-deleted (deleted_at IS NOT NULL).
    """

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        """Find a session by its refresh token hash.

        Used during token refresh to validate the incoming token.
        Returns the session even if revoked (for theft detection).
        """

    @abstractmethod
    async def get_active_by_user(self, user_id: EntityId) -> list[Session]:
        """Get all active (non-revoked, non-expired) sessions for a user.

        Used for the "Active Sessions" UI.
        """

    @abstractmethod
    async def revoke_all_by_user(self, user_id: EntityId) -> int:
        """Revoke all sessions for a user.

        Used for:
        - Theft detection (suspicious token reuse)
        - "Logout all devices" feature
        - Password change (security best practice)

        Returns the number of sessions revoked.
        """

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Soft-delete all expired sessions.

        Housekeeping method — called by a scheduled background task.
        Returns the number of sessions cleaned up.
        """


# =============================================================================
# Audit Log Repository
# =============================================================================


class AuditLogRepository:
    """Repository interface for audit log entries.

    Append-only: audit logs are never updated or deleted.
    """

    @abstractmethod
    async def create(self, audit_log: AuditLog) -> AuditLog:
        """Persist a new audit log entry."""

    @abstractmethod
    async def get_by_user(
        self,
        user_id: EntityId,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get audit logs for a specific user, ordered by created_at DESC."""

    @abstractmethod
    async def get_by_event_type(
        self,
        event_type: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get audit logs by event type, ordered by created_at DESC."""
