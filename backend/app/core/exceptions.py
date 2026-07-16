"""
YUGI-AI — Domain Exception Hierarchy
======================================

All application errors extend from AppException.
Domain layer raises these; the global exception handler maps them to HTTP responses.

Architecture (ADR-017):
    Domain Layer:       raise NotFoundException("User not found", code="USER_NOT_FOUND")
    Application Layer:  propagates (doesn't catch domain errors)
    Presentation Layer: global handler catches → structured JSON response

Each exception carries:
    - error_code: Machine-readable string (stable API contract)
    - message: Human-readable description
    - http_status: HTTP status code for the response
    - details: Optional additional context (field errors, constraints, etc.)

Usage:
    from app.core.exceptions import NotFoundException

    raise NotFoundException(
        message="User with this email does not exist.",
        error_code="USER_NOT_FOUND",
    )
"""

from typing import Any


class AppException(Exception):
    """Base exception for all YUGI-AI application errors.

    All domain, application, and infrastructure exceptions must extend this class.
    The global exception handler catches AppException subclasses and maps them
    to structured JSON error responses.

    Attributes:
        message: Human-readable error description.
        error_code: Machine-readable code for client-side error handling.
        http_status: HTTP status code to return.
        details: Additional error context (field errors, constraints, etc.).
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        error_code: str = "INTERNAL_ERROR",
        http_status: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception to a dictionary for JSON response."""
        payload: dict[str, Any] = {
            "code": self.error_code,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload


# =============================================================================
# 4xx Client Errors
# =============================================================================


class UnauthorizedException(AppException):
    """401 — Authentication required or credentials invalid.

    Raised when:
    - No token provided
    - Token expired
    - Token signature invalid
    """

    def __init__(
        self,
        message: str = "Authentication is required.",
        error_code: str = "UNAUTHORIZED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=401,
            details=details,
        )


class ForbiddenException(AppException):
    """403 — Authenticated but insufficient permissions.

    Raised when:
    - User tries to access another user's resource
    - User lacks required role/permission
    """

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        error_code: str = "FORBIDDEN",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=403,
            details=details,
        )


class NotFoundException(AppException):
    """404 — Requested resource does not exist.

    Raised when:
    - Entity not found by ID
    - Entity not found by unique constraint (email, username)
    """

    def __init__(
        self,
        message: str = "The requested resource was not found.",
        error_code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=404,
            details=details,
        )


class ConflictException(AppException):
    """409 — Resource already exists or state conflict.

    Raised when:
    - Duplicate email during registration
    - Concurrent modification detected (optimistic locking)
    """

    def __init__(
        self,
        message: str = "A resource with this identifier already exists.",
        error_code: str = "CONFLICT",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=409,
            details=details,
        )


class ValidationException(AppException):
    """422 — Business rule validation failure.

    Different from Pydantic's RequestValidationError (schema validation).
    This is for domain-level validation:
    - Password doesn't meet complexity requirements
    - Date range is invalid
    - Business constraint violated

    Attributes:
        field_errors: Per-field error messages.
    """

    def __init__(
        self,
        message: str = "Validation failed.",
        error_code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
        field_errors: dict[str, str] | None = None,
    ) -> None:
        combined_details = details or {}
        if field_errors:
            combined_details["field_errors"] = field_errors
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=422,
            details=combined_details or None,
        )


class RateLimitException(AppException):
    """429 — Too many requests.

    Raised when:
    - User exceeds per-endpoint rate limit
    - IP exceeds global rate limit
    """

    def __init__(
        self,
        message: str = "Too many requests. Please try again later.",
        error_code: str = "RATE_LIMIT_EXCEEDED",
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        combined_details = details or {}
        if retry_after is not None:
            combined_details["retry_after_seconds"] = retry_after
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=429,
            details=combined_details or None,
        )


# =============================================================================
# 5xx Server Errors
# =============================================================================


class ExternalServiceException(AppException):
    """502 — External service (AI provider, email, etc.) failed.

    Raised when:
    - OpenAI API returns an error
    - Redis connection failed
    - Any third-party integration fails

    Never exposes the external error details to the client.
    Full details are logged server-side with correlation ID.
    """

    def __init__(
        self,
        message: str = "An external service is temporarily unavailable.",
        error_code: str = "EXTERNAL_SERVICE_ERROR",
        service_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        combined_details = details or {}
        if service_name:
            combined_details["service"] = service_name
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=502,
            details=combined_details or None,
        )
