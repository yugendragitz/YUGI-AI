"""initial_auth

Revision ID: 12796c36debe
Revises:
Create Date: 2026-07-17 09:23:41.527054

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "12796c36debe"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Users Table ---
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("avatar_seed", sa.String(length=100), nullable=False),
        sa.Column("avatar_style", sa.String(length=50), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        schema="app",
    )
    op.create_index(
        "ix_users_email_active",
        "users",
        ["email"],
        unique=True,
        schema="app",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_users_role", "users", ["role"], unique=False, schema="app")
    op.create_index(
        "ix_users_username_active",
        "users",
        ["username"],
        unique=True,
        schema="app",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # --- Sessions Table ---
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=128), nullable=False),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app.users.id"],
            name=op.f("fk_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        schema="app",
    )
    op.create_index(
        "ix_sessions_expires",
        "sessions",
        ["expires_at"],
        unique=False,
        schema="app",
        postgresql_where=sa.text("is_revoked = FALSE AND deleted_at IS NULL"),
    )
    op.create_index(
        "ix_sessions_token",
        "sessions",
        ["refresh_token_hash"],
        unique=True,
        schema="app",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"], unique=False, schema="app")

    # --- Audit Logs Table ---
    from sqlalchemy.dialects import postgresql

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("correlation_id", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app.users.id"],
            name=op.f("fk_audit_logs_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
        schema="app",
    )
    op.create_index("ix_audit_created_at", "audit_logs", ["created_at"], unique=False, schema="app")
    op.create_index("ix_audit_event_type", "audit_logs", ["event_type"], unique=False, schema="app")
    op.create_index(
        "ix_audit_user_id",
        "audit_logs",
        ["user_id"],
        unique=False,
        schema="app",
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )


def downgrade() -> None:
    # --- Audit Logs ---
    op.drop_index(
        "ix_audit_user_id",
        table_name="audit_logs",
        schema="app",
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )
    op.drop_index("ix_audit_event_type", table_name="audit_logs", schema="app")
    op.drop_index("ix_audit_created_at", table_name="audit_logs", schema="app")
    op.drop_table("audit_logs", schema="app")

    # --- Sessions ---
    op.drop_index("ix_sessions_user_id", table_name="sessions", schema="app")
    op.drop_index(
        "ix_sessions_token",
        table_name="sessions",
        schema="app",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_index(
        "ix_sessions_expires",
        table_name="sessions",
        schema="app",
        postgresql_where=sa.text("is_revoked = FALSE AND deleted_at IS NULL"),
    )
    op.drop_table("sessions", schema="app")

    # --- Users ---
    op.drop_index(
        "ix_users_username_active",
        table_name="users",
        schema="app",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_index("ix_users_role", table_name="users", schema="app")
    op.drop_index(
        "ix_users_email_active",
        table_name="users",
        schema="app",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_table("users", schema="app")
