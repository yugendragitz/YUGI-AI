"""
YUGI-AI — Database Infrastructure
====================================

Async SQLAlchemy engine and session management.

Architecture:
    - DatabaseManager: Creates and manages async engines (multi-database ready)
    - Base: Declarative ORM base class with common columns
    - get_session: Async generator for request-scoped sessions via DI

Multi-Database Design:
    Primary engine is created from AppSettings.database.
    Additional engines (read replica, analytics) can be registered by name:

        db_manager.register_engine("read_replica", replica_settings)
        session = db_manager.get_session("read_replica")

Usage:
    from app.infrastructure.database import DatabaseManager, Base

    # In lifespan:
    db_manager = DatabaseManager(settings.database)
    await db_manager.connect()

    # In dependency injection:
    async def get_session():
        async with db_manager.session() as session:
            yield session

    # In shutdown:
    await db_manager.disconnect()
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import MetaData, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import DatabaseSettings

logger = structlog.get_logger(__name__)


# =============================================================================
# Naming Convention for Constraints
# =============================================================================
# Consistent naming makes Alembic auto-generate cleaner migrations
# and simplifies debugging constraint violations.
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION, schema="app")


# =============================================================================
# Declarative Base
# =============================================================================


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    Provides:
    - UUID primary key (auto-generated)
    - created_at timestamp (auto-set)
    - updated_at timestamp (auto-updated)
    - Consistent naming convention for constraints
    - Schema prefix ("app") matching init-db.sh

    Usage:
        class UserModel(Base):
            __tablename__ = "users"

            email: Mapped[str] = mapped_column(unique=True, index=True)
            username: Mapped[str] = mapped_column(unique=True, index=True)
    """

    metadata = metadata

    # Common columns inherited by all models
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique entity identifier (UUID v4)",
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        comment="Record creation timestamp (UTC)",
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        default=None,
        onupdate=lambda: datetime.now(UTC),
        comment="Last update timestamp (UTC)",
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"


# =============================================================================
# Database Manager
# =============================================================================


class DatabaseManager:
    """Manages async SQLAlchemy engines and sessions.

    Supports multiple named engines for multi-database architecture:
    - "primary": Main application database (default)
    - Future: "read_replica", "analytics", etc.

    Lifecycle:
        1. __init__: Store config (no connection yet)
        2. connect(): Create engine, verify connectivity
        3. session(): Yield request-scoped AsyncSession
        4. disconnect(): Dispose engine pool
    """

    def __init__(self, settings: DatabaseSettings) -> None:
        """Initialize with database settings. Does NOT connect yet.

        Args:
            settings: Primary database connection configuration.
        """
        self._settings = settings
        self._engines: dict[str, AsyncEngine] = {}
        self._session_factories: dict[str, async_sessionmaker[AsyncSession]] = {}

    async def connect(self, engine_name: str = "primary") -> None:
        """Create an async engine and verify connectivity.

        Args:
            engine_name: Name for this engine (default: "primary").

        Raises:
            ConnectionError: If the database is unreachable.
        """
        settings = self._settings

        engine = create_async_engine(
            settings.async_url,
            pool_size=settings.pool_max_size,
            max_overflow=settings.pool_max_size,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=settings.pool_recycle,
            echo=settings.echo,
        )

        # Register engine event listener for connection debugging
        if settings.echo:

            @event.listens_for(engine.sync_engine, "connect")
            def _on_connect(dbapi_conn: Any, _rec: Any) -> None:
                logger.debug("New database connection established", engine=engine_name)

        # Verify connectivity
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: None)
            logger.info(
                "Database connection established",
                engine=engine_name,
                host=settings.host,
                port=settings.port,
                database=settings.name,
                pool_size=settings.pool_max_size,
            )
        except Exception as exc:
            logger.error(
                "Database connection failed",
                engine=engine_name,
                host=settings.host,
                port=settings.port,
                error=str(exc),
            )
            raise

        # Store engine and session factory
        self._engines[engine_name] = engine
        self._session_factories[engine_name] = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Prevent lazy loading after commit
        )

    async def disconnect(self, engine_name: str | None = None) -> None:
        """Dispose engine connection pool(s).

        Args:
            engine_name: Specific engine to disconnect. None = disconnect all.
        """
        if engine_name:
            engine = self._engines.pop(engine_name, None)
            if engine:
                await engine.dispose()
                self._session_factories.pop(engine_name, None)
                logger.info("Database engine disposed", engine=engine_name)
        else:
            for name, engine in self._engines.items():
                await engine.dispose()
                logger.info("Database engine disposed", engine=name)
            self._engines.clear()
            self._session_factories.clear()

    async def session(self, engine_name: str = "primary") -> AsyncGenerator[AsyncSession, None]:
        """Yield a request-scoped async session.

        Used as an async generator in FastAPI dependency injection:
            async def get_session(db: DatabaseManager = Depends(get_db_manager)):
                async with db.session() as session:
                    yield session

        Args:
            engine_name: Which engine to use (default: "primary").

        Yields:
            AsyncSession bound to the requested engine.
        """
        factory = self._session_factories.get(engine_name)
        if not factory:
            msg = f"No database engine registered with name '{engine_name}'"
            raise RuntimeError(msg)

        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def get_engine(self, engine_name: str = "primary") -> AsyncEngine:
        """Get a registered engine by name.

        Useful for Alembic migrations and health checks.

        Raises:
            RuntimeError: If no engine is registered with the given name.
        """
        engine = self._engines.get(engine_name)
        if not engine:
            msg = f"No database engine registered with name '{engine_name}'"
            raise RuntimeError(msg)
        return engine

    @property
    def is_connected(self) -> bool:
        """Check if the primary engine is available."""
        return "primary" in self._engines

    async def check_connectivity(self, engine_name: str = "primary") -> bool:
        """Verify database connectivity for health checks.

        Returns:
            True if the database responds to a simple query.
        """
        try:
            engine = self.get_engine(engine_name)
            async with engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: None)
            return True
        except Exception as exc:
            logger.warning(
                "Database health check failed",
                engine=engine_name,
                error=str(exc),
            )
            return False
