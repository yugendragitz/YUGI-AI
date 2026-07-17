"""
YUGI-AI — Health & Monitoring Endpoints
==========================================

Three health endpoints following Kubernetes and AWS ALB conventions:

    GET /api/v1/health       — Full health check with version, uptime, and dependency status
    GET /api/v1/health/ready — Readiness probe: can we serve traffic? (checks DB + Redis)
    GET /api/v1/health/live  — Liveness probe: is the process alive? (lightweight, instant)

Kubernetes Usage:
    livenessProbe:
        httpGet:
            path: /api/v1/health/live
            port: 8000
        initialDelaySeconds: 10
        periodSeconds: 15

    readinessProbe:
        httpGet:
            path: /api/v1/health/ready
            port: 8000
        initialDelaySeconds: 5
        periodSeconds: 10

AWS ALB Usage:
    Target Group health check path: /api/v1/health/live
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.dependencies import container
from app.infrastructure.database import DatabaseManager
from app.infrastructure.redis import RedisManager

logger = structlog.get_logger(__name__)

router = APIRouter()

# =============================================================================
# Track application start time for uptime calculation
# =============================================================================
_app_start_time: datetime | None = None


def set_start_time() -> None:
    """Record application start time. Called once during lifespan."""
    global _app_start_time  # noqa: PLW0603
    _app_start_time = datetime.now(UTC)


def _get_uptime_seconds() -> float:
    """Calculate application uptime in seconds."""
    if _app_start_time is None:
        return 0.0
    return (datetime.now(UTC) - _app_start_time).total_seconds()


# =============================================================================
# Response Schemas
# =============================================================================


class HealthResponse(BaseModel):
    """Full health check response."""

    status: str = Field(description="Overall health status")
    version: str = Field(description="Application version")
    environment: str = Field(description="Current environment")
    uptime_seconds: float = Field(description="Seconds since application start")
    timestamp: datetime = Field(description="Current server time (UTC)")
    checks: dict[str, str] = Field(description="Individual dependency check results")


class ReadinessResponse(BaseModel):
    """Readiness probe response."""

    status: str = Field(description="Readiness status: 'ready' or 'not_ready'")
    checks: dict[str, str] = Field(description="Individual dependency check results")


class LivenessResponse(BaseModel):
    """Liveness probe response."""

    status: str = Field(description="Liveness status: 'alive'")


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns application health status, version, uptime, and dependency checks.",
)
async def health_check(
    db_manager: DatabaseManager = Depends(container.get_db_manager),
) -> HealthResponse:
    """Full health check endpoint.

    Checks all critical dependencies and returns comprehensive status.
    Suitable for monitoring dashboards and alerting systems.
    """
    settings = container.get_settings()

    # Check database
    db_ok = await db_manager.check_connectivity()
    db_status = "connected" if db_ok else "disconnected"

    # Check redis
    redis_manager: RedisManager = container.get_redis_manager()
    redis_ok = await redis_manager.check_connectivity()
    redis_status = "connected" if redis_ok else "disconnected"

    # Determine overall status
    overall = "healthy" if (db_ok and redis_ok) else "degraded"

    return HealthResponse(
        status=overall,
        version=settings.app_version,
        environment=settings.environment.value,
        uptime_seconds=round(_get_uptime_seconds(), 2),
        timestamp=datetime.now(UTC),
        checks={
            "database": db_status,
            "redis": redis_status,
        },
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description=(
        "Kubernetes/ALB readiness probe. Returns 200 if the application "
        "can serve traffic (all dependencies available). Returns 503 if "
        "any critical dependency is unavailable."
    ),
)
async def readiness_probe(
    db_manager: DatabaseManager = Depends(container.get_db_manager),
) -> JSONResponse:
    """Readiness probe — can we serve traffic?

    Checks:
    - Database connectivity (PostgreSQL)
    - Cache connectivity (Redis) — when implemented

    Returns 503 Service Unavailable if any check fails.
    Kubernetes will stop routing traffic to this pod.
    """
    db_ok = await db_manager.check_connectivity()
    db_status = "connected" if db_ok else "disconnected"

    redis_manager: RedisManager = container.get_redis_manager()
    redis_ok = await redis_manager.check_connectivity()
    redis_status = "connected" if redis_ok else "disconnected"

    all_healthy = db_ok and redis_ok
    response_status = "ready" if all_healthy else "not_ready"
    http_status = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    if not all_healthy:
        logger.warning(
            "Readiness probe failed",
            database=db_status,
            redis=redis_status,
        )

    return JSONResponse(
        status_code=http_status,
        content={
            "status": response_status,
            "checks": {
                "database": db_status,
                "redis": redis_status,
            },
        },
    )


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness Probe",
    description=(
        "Kubernetes/ALB liveness probe. Returns 200 if the process is alive. "
        "Does NOT check dependencies — only verifies the process can respond."
    ),
)
async def liveness_probe() -> LivenessResponse:
    """Liveness probe — is the process alive?

    Lightweight check that always returns 200 if the process is running.
    Does NOT check database/Redis — those are readiness concerns.

    If this fails, Kubernetes will restart the pod.
    """
    return LivenessResponse(status="alive")
