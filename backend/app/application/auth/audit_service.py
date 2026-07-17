"""
YUGI-AI — Audit Service
=========================

Records authentication events to the audit_logs table.
Every auth operation calls this service to maintain a complete audit trail.

Audit logs are append-only and never modified or deleted.

Usage:
    from app.application.auth.audit_service import AuditService

    audit = AuditService(audit_repo=audit_repo)
    await audit.log_event(
        event_type=AuditEventType.LOGIN_SUCCESS,
        user_id=user.id,
        ip_address="192.168.1.1",
        metadata={"session_id": str(session.id)},
    )
"""

from __future__ import annotations

from typing import Any

from app.application.base import BaseService
from app.core.constants import AuditEventType
from app.core.types import EntityId
from app.domain.auth.entities import AuditLog
from app.domain.auth.repositories import AuditLogRepository
from app.middleware.correlation_id import get_correlation_id


class AuditService(BaseService):
    """Writes authentication audit events to persistent storage.

    Dependencies:
        - AuditLogRepository: Persists audit log entries.
    """

    def __init__(self, audit_repo: AuditLogRepository) -> None:
        super().__init__()
        self._audit_repo = audit_repo

    async def log_event(
        self,
        *,
        event_type: AuditEventType,
        user_id: EntityId | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Record an authentication audit event.

        This method never raises — audit failures are logged but don't
        break the user-facing operation.

        Args:
            event_type: The type of auth event.
            user_id: User who performed the action (None for failed login by unknown user).
            ip_address: Client IP address.
            user_agent: Client User-Agent header.
            metadata: Event-specific data (session_id, identifier, etc.).

        Returns:
            The created AuditLog entity.
        """
        correlation_id = get_correlation_id()

        audit_log = AuditLog(
            user_id=user_id,
            event_type=event_type.value,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
            correlation_id=correlation_id,
        )

        try:
            result = await self._audit_repo.create(audit_log)
            self._logger.info(
                "Audit event recorded",
                event_type=event_type.value,
                user_id=str(user_id) if user_id else None,
                correlation_id=correlation_id,
            )
            return result
        except Exception:
            # Audit failures must NEVER break the user flow
            self._logger.exception(
                "Failed to record audit event — continuing without audit",
                event_type=event_type.value,
                user_id=str(user_id) if user_id else None,
            )
            return audit_log
