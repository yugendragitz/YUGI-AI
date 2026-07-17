"""
YUGI-AI — PostgreSQL Audit Log Repository
============================================

Append-only repository for authentication audit events.
Audit logs are never updated or deleted.
"""

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import EntityId
from app.domain.auth.entities import AuditLog
from app.domain.auth.repositories import AuditLogRepository
from app.infrastructure.auth.models import AuditLogModel

logger = structlog.get_logger(__name__)


class PostgresAuditLogRepository(AuditLogRepository):
    """PostgreSQL implementation of AuditLogRepository.

    Append-only: only create() and read operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, audit_log: AuditLog) -> AuditLog:
        model = AuditLogModel(
            id=audit_log.id,
            user_id=audit_log.user_id,
            event_type=audit_log.event_type,
            ip_address=audit_log.ip_address,
            user_agent=audit_log.user_agent,
            metadata_=audit_log.metadata,
            correlation_id=audit_log.correlation_id,
            created_at=audit_log.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get_by_user(
        self,
        user_id: EntityId,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLogModel)
            .where(AuditLogModel.user_id == user_id)
            .order_by(AuditLogModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_event_type(
        self,
        event_type: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLogModel)
            .where(AuditLogModel.event_type == event_type)
            .order_by(AuditLogModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    @staticmethod
    def _to_entity(model: AuditLogModel) -> AuditLog:
        return AuditLog(
            id=model.id,
            user_id=model.user_id,
            event_type=model.event_type,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            metadata=model.metadata_ or {},
            correlation_id=model.correlation_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
