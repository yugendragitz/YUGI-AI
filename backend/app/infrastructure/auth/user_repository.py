"""
YUGI-AI — PostgreSQL User Repository
=======================================

Implements the UserRepository interface for PostgreSQL via async SQLAlchemy.
All queries automatically filter soft-deleted records (deleted_at IS NULL).
"""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole
from app.core.types import EntityId
from app.domain.auth.entities import User
from app.domain.auth.repositories import UserRepository
from app.infrastructure.auth.models import UserModel

logger = structlog.get_logger(__name__)


class PostgresUserRepository(UserRepository):
    """PostgreSQL implementation of UserRepository.

    Every query applies `WHERE deleted_at IS NULL` by default
    to support soft deletes transparently.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # =========================================================================
    # Base CRUD
    # =========================================================================

    async def get_by_id(self, entity_id: EntityId) -> User | None:
        stmt = select(UserModel).where(
            UserModel.id == entity_id,
            UserModel.deleted_at.is_(None),
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
    ) -> list[User]:
        stmt = (
            select(UserModel)
            .where(UserModel.deleted_at.is_(None))
            .offset(offset)
            .limit(limit)
            .order_by(UserModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: User) -> User:
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, entity: User) -> User:
        stmt = select(UserModel).where(UserModel.id == entity.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            msg = f"User {entity.id} not found for update"
            raise ValueError(msg)

        # Update fields
        model.email = entity.email
        model.username = entity.username
        model.display_name = entity.display_name
        model.password_hash = entity.password_hash
        model.role = entity.role.value if isinstance(entity.role, UserRole) else entity.role
        model.is_active = entity.is_active
        model.is_verified = entity.is_verified
        model.avatar_seed = entity.avatar_seed
        model.avatar_style = entity.avatar_style
        model.avatar_url = entity.avatar_url
        model.last_login_at = entity.last_login_at
        model.updated_at = entity.updated_at
        model.deleted_at = entity.deleted_at

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, entity_id: EntityId) -> bool:
        """Soft delete — sets deleted_at instead of removing the row."""
        stmt = select(UserModel).where(
            UserModel.id == entity_id,
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return False

        from datetime import UTC, datetime

        model.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(UserModel).where(UserModel.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # =========================================================================
    # Auth-Specific Queries
    # =========================================================================

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(
            UserModel.email == email.lower().strip(),
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(
            UserModel.username == username.strip(),
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_identifier(self, identifier: str) -> User | None:
        """Find user by email or username.

        Auto-detects: '@' in identifier → email, otherwise → username.
        """
        if "@" in identifier:
            return await self.get_by_email(identifier)
        return await self.get_by_username(identifier)

    async def exists_by_email(self, email: str) -> bool:
        stmt = (
            select(func.count())
            .select_from(UserModel)
            .where(
                UserModel.email == email.lower().strip(),
                UserModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def exists_by_username(self, username: str) -> bool:
        stmt = (
            select(func.count())
            .select_from(UserModel)
            .where(
                UserModel.username == username.strip(),
                UserModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    # =========================================================================
    # Entity ↔ Model Mapping
    # =========================================================================

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            username=model.username,
            display_name=model.display_name,
            password_hash=model.password_hash,
            role=UserRole(model.role) if model.role else UserRole.USER,
            is_active=model.is_active,
            is_verified=model.is_verified,
            avatar_seed=model.avatar_seed,
            avatar_style=model.avatar_style,
            avatar_url=model.avatar_url,
            last_login_at=model.last_login_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _to_model(entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=entity.email.lower().strip(),
            username=entity.username.strip(),
            display_name=entity.display_name.strip(),
            password_hash=entity.password_hash,
            role=entity.role.value if isinstance(entity.role, UserRole) else entity.role,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
            avatar_seed=entity.avatar_seed,
            avatar_style=entity.avatar_style,
            avatar_url=entity.avatar_url,
            last_login_at=entity.last_login_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )
