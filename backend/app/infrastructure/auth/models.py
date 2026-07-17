"""
YUGI-AI — Auth ORM Models
============================

SQLAlchemy 2.0 declarative models for the auth domain.
These map to PostgreSQL tables in the 'app' schema.

Model ↔ Entity mapping:
    UserModel    → User domain entity
    SessionModel → Session domain entity
    AuditLogModel → AuditLog domain entity
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base

# =============================================================================
# User Model
# =============================================================================


class UserModel(Base):
    """ORM model for the `app.users` table.

    Partial unique indexes on email/username ensure uniqueness
    only among non-deleted records (soft delete support).
    """

    __tablename__ = "users"

    # Identity
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="User email address (unique among active users)",
    )
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Unique username (3-50 chars, lowercase)",
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User display name",
    )

    # Authentication
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Argon2id password hash",
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="user",
        comment="User role: user, moderator, admin",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Account active status",
    )
    is_verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Email verified (Phase 2)",
    )

    # Avatar
    avatar_seed: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        comment="DiceBear avatar generation seed",
    )
    avatar_style: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="bottts",
        comment="DiceBear avatar style",
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
        comment="Custom avatar URL (Phase 2)",
    )

    # Metadata
    last_login_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        default=None,
        comment="Last successful login timestamp",
    )

    # Relationships
    sessions: Mapped[list[SessionModel]] = relationship(
        "SessionModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Indexes — partial unique indexes for soft delete support
    __table_args__ = (
        Index(
            "ix_users_email_active",
            "email",
            unique=True,
            postgresql_where=(Base.metadata.schema is not None),  # placeholder
        ),
        Index(
            "ix_users_username_active",
            "username",
            unique=True,
            postgresql_where=(Base.metadata.schema is not None),  # placeholder
        ),
        Index("ix_users_role", "role"),
    )


# Override table args with proper partial index expressions
# SQLAlchemy requires text() for WHERE clauses in Index

UserModel.__table_args__ = (  # type: ignore[assignment]
    Index(
        "ix_users_email_active",
        "email",
        unique=True,
        postgresql_where=text("deleted_at IS NULL"),
    ),
    Index(
        "ix_users_username_active",
        "username",
        unique=True,
        postgresql_where=text("deleted_at IS NULL"),
    ),
    Index("ix_users_role", "role"),
    {"schema": "app"},
)


# =============================================================================
# Session Model
# =============================================================================


class SessionModel(Base):
    """ORM model for the `app.sessions` table."""

    __tablename__ = "sessions"

    # Relationships
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app.users.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to users table",
    )

    # Token (SHA-256 hash — never plaintext)
    refresh_token_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="SHA-256 hash of the refresh token",
    )

    # Device info
    device_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Device description (e.g., Chrome on Windows)",
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP address (IPv4 or IPv6)",
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Client User-Agent header",
    )

    # Lifecycle
    is_revoked: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Whether this session has been revoked",
    )
    expires_at: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="Session expiration timestamp",
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        default=None,
        comment="Last time this session was used for refresh",
    )

    # Relationships
    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="sessions",
    )

    __table_args__ = (
        Index(
            "ix_sessions_token",
            "refresh_token_hash",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_sessions_user_id", "user_id"),
        Index(
            "ix_sessions_expires",
            "expires_at",
            postgresql_where=text("is_revoked = FALSE AND deleted_at IS NULL"),
        ),
        {"schema": "app"},
    )


# =============================================================================
# Audit Log Model
# =============================================================================


class AuditLogModel(Base):
    """ORM model for the `app.audit_logs` table.

    Append-only: audit logs are never updated or deleted.
    """

    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app.users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who performed the action (NULL for failed login)",
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Audit event type (e.g., LOGIN_SUCCESS)",
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP address",
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Client User-Agent header",
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=None,
        comment="Event-specific JSONB data",
    )
    correlation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Request correlation ID for tracing",
    )

    __table_args__ = (
        Index("ix_audit_user_id", "user_id", postgresql_where=text("user_id IS NOT NULL")),
        Index("ix_audit_event_type", "event_type"),
        Index("ix_audit_created_at", "created_at"),
        {"schema": "app"},
    )
