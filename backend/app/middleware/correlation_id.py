"""
YUGI-AI — Correlation ID Middleware
=====================================

Generates or extracts a unique correlation ID for every request.
Enables end-to-end request tracing across logs, error responses,
AI provider calls, and WebSocket messages (ADR-023).

Flow:
    1. Check incoming request for X-Correlation-ID header
    2. If present → use it (client-provided tracing, e.g., mobile app)
    3. If absent → generate UUID4
    4. Store in Python context var (async-safe, per-request isolation)
    5. Bind to structlog context → every log entry includes correlation_id
    6. Attach to response as X-Correlation-ID header

Context Var:
    The correlation ID is stored in a contextvars.ContextVar, which is
    automatically isolated per async task. This means concurrent requests
    never share correlation IDs, even under asyncio.

Usage (in downstream code):
    from app.middleware.correlation_id import get_correlation_id

    cid = get_correlation_id()  # Returns current request's correlation ID
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.constants import CORRELATION_ID_HEADER

# =============================================================================
# Context Variable — async-safe, per-request isolation
# =============================================================================
_correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Get the correlation ID for the current request.

    Returns an empty string if called outside a request context
    (e.g., during startup or in background tasks).
    """
    return _correlation_id_ctx.get()


# =============================================================================
# Middleware
# =============================================================================


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that manages request correlation IDs.

    Processing:
    1. Extract or generate correlation ID
    2. Set context variable (available via get_correlation_id())
    3. Bind to structlog (appears in all log entries)
    4. Add to response headers (returned to client)
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Extract from request header or generate new
        correlation_id = request.headers.get(
            CORRELATION_ID_HEADER,
            str(uuid.uuid4()),
        )

        # Store in context var (async-safe per-request isolation)
        token = _correlation_id_ctx.set(correlation_id)

        # Bind to structlog — every log call in this request scope
        # will automatically include correlation_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        try:
            response = await call_next(request)

            # Attach correlation ID to response headers
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            return response
        finally:
            # Reset context var to prevent leaks between requests
            _correlation_id_ctx.reset(token)
            structlog.contextvars.clear_contextvars()
