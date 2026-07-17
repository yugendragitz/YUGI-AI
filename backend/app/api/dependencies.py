"""
YUGI-AI — Dependency Injection Container
==========================================

Centralized dependency management for the FastAPI application.

Architecture:
    Container class manages two categories of dependencies:

    1. SINGLETONS (app-scoped):
       Created once during lifespan startup, shared across all requests.
       - AppSettings, DatabaseManager, Redis client, Loggers

    2. REQUEST-SCOPED (per-request):
       Created fresh for each request via FastAPI Depends().
       - AsyncSession (database session with commit/rollback lifecycle)
       - Bound logger (with correlation ID from current request)

Design Decision:
    We use a custom Container class rather than a third-party DI library
    (like python-dependency-injector) because:
    - FastAPI's Depends() is the native DI mechanism
    - Container class provides centralization without framework overhead
    - Singletons are explicit, not magical
    - Easy to extend when new modules are added

Usage in routes:
    from app.api.dependencies import container

    @router.get("/users/{user_id}")
    async def get_user(
        session: AsyncSession = Depends(container.get_session),
        logger: BoundLogger = Depends(container.get_logger),
    ):
        ...

Usage in lifespan:
    container.init(settings=settings, db_manager=db_manager)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import structlog
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.audit_service import AuditService
from app.application.auth.auth_service import AuthService
from app.application.auth.password_service import PasswordService
from app.core.config import AppSettings
from app.infrastructure.auth.audit_repository import PostgresAuditLogRepository
from app.infrastructure.auth.session_repository import PostgresSessionRepository
from app.infrastructure.auth.user_repository import PostgresUserRepository
from app.infrastructure.database import DatabaseManager
from app.infrastructure.rate_limiter import RateLimiter
from app.infrastructure.redis import RedisManager


class _Container:
    """Dependency Injection container.

    Manages singleton and request-scoped dependencies for the FastAPI application.

    Lifecycle:
        1. Application startup (lifespan) → call init() with singletons
        2. Request processing → call get_session(), get_logger() via Depends()
        3. Application shutdown (lifespan) → resources cleaned up by lifespan
    """

    def __init__(self) -> None:
        self._settings: AppSettings | None = None
        self._db_manager: DatabaseManager | None = None
        self._redis_manager: RedisManager | None = None
        self._rate_limiter: RateLimiter | None = None
        self._initialized: bool = False

    def init(
        self,
        *,
        settings: AppSettings,
        db_manager: DatabaseManager,
        redis_manager: RedisManager,
        rate_limiter: RateLimiter,
    ) -> None:
        """Initialize the container with singleton dependencies.

        Called once during application lifespan startup.

        Args:
            settings: Validated application settings.
            db_manager: Connected database manager.
            redis_manager: Connected Redis manager.
            rate_limiter: Configured rate limiter.
        """
        self._settings = settings
        self._db_manager = db_manager
        self._redis_manager = redis_manager
        self._rate_limiter = rate_limiter
        self._initialized = True

    def _check_initialized(self) -> None:
        """Guard against accessing dependencies before initialization."""
        if not self._initialized:
            msg = (
                "Container not initialized. "
                "Call container.init() during application lifespan startup."
            )
            raise RuntimeError(msg)

    # =========================================================================
    # Singleton Dependencies (app-scoped)
    # =========================================================================

    def get_settings(self) -> AppSettings:
        """Get the application settings singleton.

        Returns:
            Validated AppSettings instance.
        """
        self._check_initialized()
        assert self._settings is not None  # noqa: S101
        return self._settings

    def get_db_manager(self) -> DatabaseManager:
        """Get the database manager singleton.

        Returns:
            Connected DatabaseManager instance.
        """
        self._check_initialized()
        assert self._db_manager is not None  # noqa: S101
        return self._db_manager

    def get_redis_manager(self) -> RedisManager:
        """Get the Redis manager singleton."""
        self._check_initialized()
        assert self._redis_manager is not None  # noqa: S101
        return self._redis_manager

    def get_rate_limiter(self) -> RateLimiter:
        """Get the rate limiter singleton."""
        self._check_initialized()
        assert self._rate_limiter is not None  # noqa: S101
        return self._rate_limiter

    # =========================================================================
    # Request-Scoped Dependencies (per-request via Depends)
    # =========================================================================

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield a request-scoped database session.

        The session is automatically committed on success and rolled back
        on exception. Used via FastAPI Depends():

            @router.get("/users")
            async def list_users(
                session: AsyncSession = Depends(container.get_session),
            ):
                ...
        """
        self._check_initialized()
        assert self._db_manager is not None  # noqa: S101
        async for session in self._db_manager.session():
            yield session

    async def get_logger(self) -> structlog.stdlib.BoundLogger:
        """Get a request-scoped logger with correlation ID.

        The logger automatically includes the correlation_id bound
        by the CorrelationIdMiddleware via structlog contextvars.

        Returns:
            BoundLogger with request context.
        """
        return structlog.get_logger("api")


# =============================================================================
# Module-level Singleton
# =============================================================================
# Single container instance shared across the application.
# Initialized in main.py lifespan, accessed in route handlers via Depends().

container = _Container()


# =============================================================================
# Standalone Dependencies (FastAPI Depends)
# =============================================================================


async def get_auth_service(
    session: AsyncSession = Depends(container.get_session),
) -> AuthService:
    """Dependency that provides a fully configured AuthService."""
    user_repo = PostgresUserRepository(session)
    session_repo = PostgresSessionRepository(session)
    audit_repo = PostgresAuditLogRepository(session)

    password_svc = PasswordService()
    audit_svc = AuditService(audit_repo)

    return AuthService(
        user_repo=user_repo,
        session_repo=session_repo,
        password_svc=password_svc,
        audit_svc=audit_svc,
    )
