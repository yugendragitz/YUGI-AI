"""
YUGI-AI — PostgreSQL Session Repository
==========================================

Implements the SessionRepository interface for session management.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import EntityId
from app.domain.auth.entities import Session
from app.domain.auth.repositories import SessionRepository
from app.infrastructure.auth.models import SessionModel

logger = structlog.get_logger(__name__)


class PostgresSessionRepository(SessionRepository):
    """PostgreSQL implementation of SessionRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # =========================================================================
    # Base CRUD
    # =========================================================================

    async def get_by_id(self, entity_id: EntityId) -> Session | None:
        stmt = select(SessionModel).where(
            SessionModel.id == entity_id,
            SessionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        **filters: Any,
    ) -> list[Session]:
        stmt = (
            select(SessionModel)
            .where(SessionModel.deleted_at.is_(None))
            .offset(offset)
            .limit(limit)
            .order_by(SessionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: Session) -> Session:
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, entity: Session) -> Session:
        stmt = select(SessionModel).where(SessionModel.id == entity.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            msg = f"Session {entity.id} not found for update"
            raise ValueError(msg)

        model.refresh_token_hash = entity.refresh_token_hash
        model.device_name = entity.device_name
        model.ip_address = entity.ip_address
        model.user_agent = entity.user_agent
        model.is_revoked = entity.is_revoked
        model.expires_at = entity.expires_at
        model.last_used_at = entity.last_used_at
        model.updated_at = entity.updated_at
        model.deleted_at = entity.deleted_at

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, entity_id: EntityId) -> bool:
        stmt = select(SessionModel).where(
            SessionModel.id == entity_id,
            SessionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return False
        model.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def count(self, **filters: Any) -> int:
        stmt = (
            select(func.count()).select_from(SessionModel).where(SessionModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # =========================================================================
    # Auth-Specific Queries
    # =========================================================================

    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        """Find session by refresh token hash.

        Returns even revoked sessions (for theft detection).
        Only filters soft-deleted sessions.
        """
        stmt = select(SessionModel).where(
            SessionModel.refresh_token_hash == token_hash,
            SessionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_active_by_user(self, user_id: EntityId) -> list[Session]:
        """Get active (non-revoked, non-expired) sessions for a user."""
        now = datetime.now(UTC)
        stmt = (
            select(SessionModel)
            .where(
                SessionModel.user_id == user_id,
                SessionModel.is_revoked.is_(False),
                SessionModel.expires_at > now,
                SessionModel.deleted_at.is_(None),
            )
            .order_by(SessionModel.last_used_at.desc().nullslast())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def revoke_all_by_user(self, user_id: EntityId) -> int:
        """Revoke all active sessions for a user.

        Used for theft detection, logout-all, and password changes.
        Returns the number of sessions revoked.
        """
        now = datetime.now(UTC)
        stmt = (
            update(SessionModel)
            .where(
                SessionModel.user_id == user_id,
                SessionModel.is_revoked.is_(False),
                SessionModel.deleted_at.is_(None),
            )
            .values(is_revoked=True, updated_at=now)
        )
        result = await self._session.execute(stmt)
        revoked = result.rowcount  # type: ignore[attr-defined]
        await self._session.flush()

        logger.info(
            "Sessions revoked",
            user_id=str(user_id),
            count=revoked,
        )
        return int(revoked)

    async def cleanup_expired(self) -> int:
        """Soft-delete expired sessions (housekeeping)."""
        now = datetime.now(UTC)
        stmt = (
            update(SessionModel)
            .where(
                SessionModel.expires_at < now,
                SessionModel.deleted_at.is_(None),
            )
            .values(deleted_at=now)
        )
        result = await self._session.execute(stmt)
        cleaned = result.rowcount  # type: ignore[attr-defined]
        await self._session.flush()

        if cleaned > 0:
            logger.info("Expired sessions cleaned up", count=cleaned)
        return int(cleaned)

    # =========================================================================
    # Entity ↔ Model Mapping
    # =========================================================================

    @staticmethod
    def _to_entity(model: SessionModel) -> Session:
        return Session(
            id=model.id,
            user_id=model.user_id,
            refresh_token_hash=model.refresh_token_hash,
            device_name=model.device_name,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            is_revoked=model.is_revoked,
            expires_at=model.expires_at,
            last_used_at=model.last_used_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _to_model(entity: Session) -> SessionModel:
        return SessionModel(
            id=entity.id,
            user_id=entity.user_id,
            refresh_token_hash=entity.refresh_token_hash,
            device_name=entity.device_name,
            ip_address=entity.ip_address,
            user_agent=entity.user_agent,
            is_revoked=entity.is_revoked,
            expires_at=entity.expires_at,
            last_used_at=entity.last_used_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )
