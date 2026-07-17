"""
YUGI-AI — Rate Limit Middleware
=================================

FastAPI middleware that applies rate limits to configured endpoint patterns.
Uses Redis sliding window when available, in-memory fallback otherwise.

Architecture:
    Request → RateLimitMiddleware → check RateLimiter → proceed or 429

Rate limit headers are set on every response:
    X-RateLimit-Remaining: 4
    X-RateLimit-Reset: 1721001234

On limit exceeded:
    HTTP 429 Too Many Requests
    Retry-After: 45
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.constants import (
    RATE_LIMIT_AUTH_ATTEMPTS,
    RATE_LIMIT_AUTH_WINDOW_SECONDS,
    RATE_LIMIT_REFRESH_ATTEMPTS,
    RATE_LIMIT_REFRESH_WINDOW_SECONDS,
    RATE_LIMIT_REMAINING_HEADER,
    RATE_LIMIT_RESET_HEADER,
)

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)

# Route patterns → rate limit configuration
_AUTH_RATE_LIMITS: dict[str, tuple[int, int]] = {
    "/api/v1/auth/register": (RATE_LIMIT_AUTH_ATTEMPTS, RATE_LIMIT_AUTH_WINDOW_SECONDS),
    "/api/v1/auth/login": (RATE_LIMIT_AUTH_ATTEMPTS, RATE_LIMIT_AUTH_WINDOW_SECONDS),
    "/api/v1/auth/refresh": (RATE_LIMIT_REFRESH_ATTEMPTS, RATE_LIMIT_REFRESH_WINDOW_SECONDS),
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Applies per-endpoint rate limiting based on client IP."""

    def __init__(self, app: object) -> None:
        super().__init__(app)  # type: ignore[arg-type]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Only rate-limit configured endpoints
        rate_config = _AUTH_RATE_LIMITS.get(path)
        if rate_config is None:
            return await call_next(request)

        limit, window = rate_config

        # Build rate limit key from client IP
        client_ip = self._get_client_ip(request)
        key = f"rate:{path.split('/')[-1]}:{client_ip}"

        # Fetch limiter dynamically
        from app.api.dependencies import container

        limiter = container.get_rate_limiter()
        result = await limiter.check(key, limit=limit, window_seconds=window)

        if not result.allowed:
            logger.warning(
                "Rate limit exceeded",
                path=path,
                client_ip=client_ip,
                retry_after=result.retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": (
                            f"Too many requests. Please try again in {result.retry_after} seconds."
                        ),
                        "details": {"retry_after_seconds": result.retry_after},
                    }
                },
                headers={
                    "Retry-After": str(result.retry_after),
                    RATE_LIMIT_REMAINING_HEADER: "0",
                    RATE_LIMIT_RESET_HEADER: str(result.reset_at),
                },
            )

        # Proceed with request — add rate limit headers to response
        response = await call_next(request)
        response.headers[RATE_LIMIT_REMAINING_HEADER] = str(result.remaining)
        response.headers[RATE_LIMIT_RESET_HEADER] = str(result.reset_at)
        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For behind a reverse proxy."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # Take the first IP (original client)
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
