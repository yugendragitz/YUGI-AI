"""
YUGI-AI — API v1 Router Aggregator
=====================================

Collects all feature routers and mounts them under /api/v1/.
Single registration point for the application factory.

Adding a new feature module:
    1. Create app/api/v1/my_feature.py with a FastAPI APIRouter
    2. Import and include it here:
        from app.api.v1.my_feature import router as my_feature_router
        v1_router.include_router(my_feature_router, prefix="/my-feature", tags=["My Feature"])
    3. That's it. The main.py application factory picks it up automatically.

Current routes:
    /api/v1/health      — Health check
    /api/v1/health/ready — Readiness probe
    /api/v1/health/live  — Liveness probe
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.core.constants import API_V1_PREFIX

# =============================================================================
# V1 Router — aggregates all feature routers
# =============================================================================
v1_router = APIRouter(prefix=API_V1_PREFIX)

# ---------------------------------------------------------------------------
# Health & Monitoring
# ---------------------------------------------------------------------------
v1_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health & Monitoring"],
)

# ---------------------------------------------------------------------------
# Future Module Routers (uncomment as modules are implemented)
# ---------------------------------------------------------------------------
# from app.api.v1.auth import router as auth_router
# v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# from app.api.v1.console import router as console_router
# v1_router.include_router(console_router, prefix="/console", tags=["AI Console"])

# from app.api.v1.identity import router as identity_router
# v1_router.include_router(identity_router, prefix="/identity", tags=["Identity"])

# from app.api.v1.system_core import router as system_core_router
# v1_router.include_router(system_core_router, prefix="/system-core", tags=["System Core"])

# from app.api.v1.events import router as events_router
# v1_router.include_router(events_router, prefix="/events", tags=["Event Center"])
