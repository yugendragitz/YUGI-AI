"""
YUGI-AI — Base Application Service
====================================

Base class for all application-layer services (use cases).

Design:
    - Each service receives its dependencies via constructor injection
    - The base class provides a bound structlog logger
    - Services orchestrate domain entities and repository calls
    - Services do NOT handle HTTP concerns (status codes, headers, serialization)

Usage:
    class AuthService(BaseService):
        def __init__(self, user_repo: UserRepository, cache: CacheService) -> None:
            super().__init__()
            self._user_repo = user_repo
            self._cache = cache

        async def register(self, email: str, password: str) -> User:
            existing = await self._user_repo.get_by_email(email)
            if existing:
                raise ConflictException("Email already registered", code="EMAIL_EXISTS")
            ...
"""

from __future__ import annotations

import structlog


class BaseService:
    """Base class for application-layer services.

    Provides:
    - A bound structlog logger with the service class name
    - A consistent pattern for constructor-injected dependencies

    All service methods should be async and operate on domain entities,
    not ORM models or HTTP request objects.
    """

    def __init__(self) -> None:
        # Logger bound with the concrete service class name
        # e.g., AuthService logs will have logger="AuthService"
        self._logger: structlog.stdlib.BoundLogger = structlog.get_logger(self.__class__.__name__)

    async def _log_operation(
        self,
        operation: str,
        **context: object,
    ) -> None:
        """Log the start of a service operation with context.

        Provides consistent operation logging across all services.

        Args:
            operation: Name of the operation (e.g., "register_user", "create_chat")
            **context: Additional context to bind to the log entry.
        """
        self._logger.info(
            "Service operation started",
            operation=operation,
            **context,
        )
