"""
YUGI-AI — Application Factory
================================

Creates and configures the FastAPI application instance.
This is the single entry point for the entire backend.

Architecture:
    1. Load settings from environment
    2. Configure structured logging
    3. Create FastAPI app with OpenAPI metadata
    4. Register async lifespan (startup/shutdown)
    5. Add middleware stack (order matters)
    6. Register exception handlers
    7. Include versioned routers

Run:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Lifespan:
    Uses the modern async context manager pattern (@asynccontextmanager)
    instead of deprecated @app.on_event("startup") / @app.on_event("shutdown").
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.dependencies import container
from app.api.v1.health import set_start_time
from app.api.v1.router import v1_router
from app.core.config import get_settings
from app.core.constants import APP_CONTACT, APP_DESCRIPTION, APP_LICENSE, APP_NAME
from app.core.logging import setup_logging
from app.core.telemetry import setup_telemetry, shutdown_telemetry
from app.infrastructure.database import DatabaseManager
from app.infrastructure.rate_limiter import RateLimiter
from app.infrastructure.redis import RedisManager
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.rate_limiter import RateLimitMiddleware

logger = structlog.get_logger(__name__)


# =============================================================================
# Security Headers Middleware
# =============================================================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response.

    These headers protect against common web vulnerabilities:
    - XSS (X-Content-Type-Options, X-XSS-Protection)
    - Clickjacking (X-Frame-Options)
    - MIME sniffing (X-Content-Type-Options)
    - Information leakage (X-Powered-By removal, Server header)

    Note: HSTS and CSP are handled by NGINX in production (nginx.conf).
    These headers provide defense-in-depth at the application level.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Prevent information leakage
        response.headers["X-Powered-By"] = ""

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy — restrict browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(self), geolocation=(), payment=()"
        )

        return response  # type: ignore[no-any-return]


# =============================================================================
# Lifespan Context Manager
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Async lifespan manager for startup and shutdown events.

    Startup:
        1. Load and validate settings
        2. Configure structured logging
        3. Initialize database manager and verify connectivity
        4. Initialize DI container with singletons
        5. Setup OpenTelemetry (if enabled)
        6. Record start time for uptime tracking
        7. Log startup banner

    Shutdown:
        1. Shutdown OpenTelemetry (flush pending spans)
        2. Disconnect database (dispose connection pool)
        3. Log shutdown message
    """
    settings = get_settings()

    # ---- STARTUP ----

    # 1. Configure logging (must be first — everything after this can log)
    setup_logging(
        log_level=settings.log.level,
        log_format=settings.log.format,
    )

    logger.info(
        "=" * 60,
    )
    logger.info(
        f"  {APP_NAME} Backend — Starting",
        version=settings.app_version,
        environment=settings.environment.value,
    )
    logger.info(
        "=" * 60,
    )

    # 2. Initialize database
    db_manager = DatabaseManager(settings.database)
    try:
        await db_manager.connect()
        logger.info("  ✓ Database connected")
    except Exception:
        logger.error("  ✗ Database connection failed — application may not function correctly")
        # Don't crash on startup — health endpoints will report degraded status
        # This allows the container to stay alive for debugging

    # 3. Initialize Redis
    redis_manager = RedisManager(settings.redis)
    await redis_manager.connect()

    # 4. Initialize Rate Limiter
    rate_limiter = RateLimiter(redis_manager.client)

    # 5. Initialize DI container
    container.init(
        settings=settings,
        db_manager=db_manager,
        redis_manager=redis_manager,
        rate_limiter=rate_limiter,
    )
    logger.info("  ✓ DI container initialized")

    # 6. Setup OpenTelemetry (no-op if disabled)
    setup_telemetry(app, settings)

    # 7. Record start time
    set_start_time()

    logger.info(
        f"  {APP_NAME} is ready to serve requests",
        port=settings.backend_port,
        docs="/docs" if settings.show_docs else "disabled",
    )

    yield  # Application runs here

    # ---- SHUTDOWN ----

    logger.info(f"  {APP_NAME} Backend — Shutting down")

    # 1. Shutdown telemetry (flush pending spans)
    shutdown_telemetry()

    # 2. Disconnect database
    await db_manager.disconnect()
    logger.info("  ✓ Database disconnected")

    # 3. Disconnect Redis
    await redis_manager.disconnect()

    logger.info(f"  {APP_NAME} Backend — Shutdown complete")


# =============================================================================
# Application Factory
# =============================================================================


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Fully configured FastAPI instance ready to serve.
    """
    settings = get_settings()

    app = FastAPI(
        title=APP_NAME,
        description=APP_DESCRIPTION,
        version=settings.app_version,
        contact=APP_CONTACT,
        license_info=APP_LICENSE,
        docs_url="/docs" if settings.show_docs else None,
        redoc_url="/redoc" if settings.show_docs else None,
        openapi_url="/openapi.json" if settings.show_docs else None,
        lifespan=lifespan,
    )

    # ---- Middleware Stack ----
    # Order matters: outermost middleware wraps innermost.
    # Request flows: CORS → Security Headers → Correlation ID → Route Handler
    # Response flows in reverse.

    # 1. CORS — must be outermost to handle preflight OPTIONS requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )

    # 2. Security Headers
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. Correlation ID — generates/extracts request ID, binds to structlog
    app.add_middleware(CorrelationIdMiddleware)

    # 4. Rate Limiter — must run after Correlation ID so logs have request ID
    # Fetches rate_limiter from container lazily per request
    app.add_middleware(RateLimitMiddleware)

    # ---- Exception Handlers ----
    register_exception_handlers(app, settings)

    # ---- Routers ----
    app.include_router(v1_router)

    return app


# =============================================================================
# Application Instance
# =============================================================================
# Created at module level so uvicorn can import it directly:
#   uvicorn app.main:app
app = create_app()
