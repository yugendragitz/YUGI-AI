"""
YUGI-AI — Global Exception Handler
=====================================

Catches all exceptions and maps them to structured JSON error responses.
Registered on the FastAPI application in the application factory.

Architecture (ADR-017):
    Domain Layer:       raise NotFoundException("User not found", code="USER_NOT_FOUND")
    Application Layer:  propagates (doesn't catch)
    Global Handler:     catches → maps to HTTP response with correlation ID

Response Format:
    {
        "error": {
            "code": "USER_NOT_FOUND",
            "message": "The requested user was not found.",
            "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
            "details": null
        }
    }

Security:
    - Stack traces are NEVER exposed in production responses
    - Stack traces ARE included in development responses for debugging
    - Full stack traces are always logged server-side with correlation ID
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.exceptions import AppException
from app.middleware.correlation_id import get_correlation_id

if TYPE_CHECKING:
    from app.core.config import AppSettings

logger = structlog.get_logger(__name__)


def _build_error_response(
    *,
    code: str,
    message: str,
    http_status: int,
    details: dict | list | None = None,
    correlation_id: str = "",
) -> JSONResponse:
    """Build a structured JSON error response.

    All error responses follow the same format for client consistency.
    """
    body: dict = {
        "error": {
            "code": code,
            "message": message,
            "correlation_id": correlation_id,
        }
    }
    if details is not None:
        body["error"]["details"] = details

    return JSONResponse(status_code=http_status, content=body)


# =============================================================================
# Exception Handlers
# =============================================================================


async def _handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    """Handle YUGI-AI domain/application exceptions.

    Maps AppException subclasses to structured error responses.
    Logs at appropriate level based on status code.
    """
    correlation_id = get_correlation_id()

    # Log — 4xx at warning level, 5xx at error level
    log_method = logger.warning if exc.http_status < 500 else logger.error
    log_method(
        "Application exception",
        error_code=exc.error_code,
        message=exc.message,
        http_status=exc.http_status,
        path=str(request.url.path),
        method=request.method,
        correlation_id=correlation_id,
    )

    return _build_error_response(
        code=exc.error_code,
        message=exc.message,
        http_status=exc.http_status,
        details=exc.details,
        correlation_id=correlation_id,
    )


async def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic request validation errors.

    Converts FastAPI's validation errors to our standard error format.
    Includes per-field error details.
    """
    correlation_id = get_correlation_id()

    # Extract field-level errors
    field_errors = []
    for error in exc.errors():
        field_errors.append(
            {
                "field": " → ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        "Request validation failed",
        path=str(request.url.path),
        method=request.method,
        error_count=len(field_errors),
        correlation_id=correlation_id,
    )

    return _build_error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        http_status=422,
        details=field_errors,
        correlation_id=correlation_id,
    )


async def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle Starlette/FastAPI HTTP exceptions (404, 405, etc.).

    Wraps framework-generated HTTP errors in our standard format.
    """
    correlation_id = get_correlation_id()

    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=str(exc.detail),
        path=str(request.url.path),
        method=request.method,
        correlation_id=correlation_id,
    )

    return _build_error_response(
        code="HTTP_ERROR",
        message=str(exc.detail) if exc.detail else "An HTTP error occurred.",
        http_status=exc.status_code,
        correlation_id=correlation_id,
    )


def _create_unhandled_exception_handler(settings: AppSettings):
    """Create an unhandled exception handler with settings context.

    Returns:
        Async exception handler that includes stack traces only in development.
    """

    async def _handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected/unhandled exceptions.

        SECURITY: Stack traces are never exposed in production.
        Full traceback is logged server-side for debugging.
        """
        correlation_id = get_correlation_id()

        # Always log the full traceback server-side
        logger.exception(
            "Unhandled exception",
            path=str(request.url.path),
            method=request.method,
            exception_type=type(exc).__name__,
            correlation_id=correlation_id,
        )

        # Include traceback in response only in development
        details = None
        if settings.is_development:
            import traceback

            details = {
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            }

        return _build_error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again later.",
            http_status=500,
            details=details,
            correlation_id=correlation_id,
        )

    return _handle_unhandled_exception


# =============================================================================
# Registration
# =============================================================================


def register_exception_handlers(app: FastAPI, settings: AppSettings) -> None:
    """Register all exception handlers on the FastAPI application.

    Must be called during application factory setup (in main.py).

    Args:
        app: FastAPI application instance.
        settings: Application settings (for environment-specific behavior).
    """
    app.add_exception_handler(AppException, _handle_app_exception)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _create_unhandled_exception_handler(settings))  # type: ignore[arg-type]
