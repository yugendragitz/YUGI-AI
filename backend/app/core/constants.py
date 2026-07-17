"""
YUGI-AI — Application Constants
================================

All magic strings, numbers, and configuration constants live here.
No module should contain hardcoded values that belong in this file.

Usage:
    from app.core.constants import API_V1_PREFIX, CORRELATION_ID_HEADER
"""

from enum import StrEnum


# =============================================================================
# Environment
# =============================================================================
class Environment(StrEnum):
    """Application environment identifiers.

    Used by AppSettings to determine runtime behavior:
    - DEVELOPMENT: verbose logging, debug endpoints, relaxed CORS
    - STAGING: production-like with debug logging
    - PRODUCTION: strict security, JSON logging, no debug
    - TESTING: in-memory databases, mocked externals
    """

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


# =============================================================================
# API Versioning
# =============================================================================
API_V1_PREFIX = "/api/v1"
"""URL prefix for API version 1. All v1 routers are mounted under this path."""


# =============================================================================
# HTTP Headers
# =============================================================================
CORRELATION_ID_HEADER = "X-Correlation-ID"
"""Header name for request correlation ID. Used for end-to-end tracing."""

RATE_LIMIT_REMAINING_HEADER = "X-RateLimit-Remaining"
"""Header indicating remaining requests in the current rate limit window."""

RATE_LIMIT_RESET_HEADER = "X-RateLimit-Reset"
"""Header indicating when the rate limit window resets (Unix timestamp)."""


# =============================================================================
# Pagination
# =============================================================================
DEFAULT_PAGE_SIZE = 20
"""Default number of items returned in paginated responses."""

MAX_PAGE_SIZE = 100
"""Maximum number of items a client can request per page."""

MIN_PAGE_SIZE = 1
"""Minimum number of items per page."""


# =============================================================================
# Password Hashing (Argon2id — OWASP recommended)
# =============================================================================
ARGON2_TIME_COST = 3
"""Number of iterations. OWASP minimum: 1. We use 3 for stronger protection."""

ARGON2_MEMORY_COST = 65536
"""Memory in KiB (64 MB). OWASP minimum: 47104 KiB (46 MiB)."""

ARGON2_PARALLELISM = 4
"""Number of parallel threads. Matches typical server CPU core count."""


# =============================================================================
# Password Policy
# =============================================================================
MIN_PASSWORD_LENGTH = 12
"""Minimum password length. Exceeds NIST 800-63B minimum (8)."""

MAX_PASSWORD_LENGTH = 128
"""Maximum password length. Argon2 handles any length (no truncation)."""

PASSWORD_REQUIRE_UPPERCASE = True
"""Require at least one uppercase letter (A-Z)."""

PASSWORD_REQUIRE_LOWERCASE = True
"""Require at least one lowercase letter (a-z)."""

PASSWORD_REQUIRE_DIGIT = True
"""Require at least one digit (0-9)."""

PASSWORD_REQUIRE_SPECIAL = True
"""Require at least one special character."""

PASSWORD_SPECIAL_CHARS = r"!@#$%^&*()_+\-=\[\]{}|;:'\",.<>?/~`"  # noqa: S105
"""Allowed special characters for password validation."""


# =============================================================================
# Rate Limiting
# =============================================================================
RATE_LIMIT_AUTH_ATTEMPTS = 5
"""Maximum login/register attempts per window."""

RATE_LIMIT_AUTH_WINDOW_SECONDS = 900
"""Rate limit window for auth endpoints (15 minutes)."""

RATE_LIMIT_REFRESH_ATTEMPTS = 10
"""Maximum token refresh attempts per window."""

RATE_LIMIT_REFRESH_WINDOW_SECONDS = 60
"""Rate limit window for refresh endpoint (1 minute)."""

RATE_LIMIT_API_REQUESTS = 100
"""Maximum authenticated API requests per window."""

RATE_LIMIT_API_WINDOW_SECONDS = 60
"""Rate limit window for general API (1 minute)."""


# =============================================================================
# User Roles (RBAC)
# =============================================================================
class UserRole(StrEnum):
    """User roles for role-based access control.

    Phase 1: All users get USER role. Admin created via CLI/migration.
    Future: Admin panel for role management.
    """

    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


# =============================================================================
# Audit Event Types
# =============================================================================
class AuditEventType(StrEnum):
    """Authentication audit event identifiers.

    Every auth action is logged to the audit_logs table with one of these types.
    """

    USER_REGISTERED = "USER_REGISTERED"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    TOKEN_REFRESHED = "TOKEN_REFRESHED"  # noqa: S105
    SUSPICIOUS_REFRESH = "SUSPICIOUS_REFRESH"
    USER_LOGGED_OUT = "USER_LOGGED_OUT"
    ALL_SESSIONS_REVOKED = "ALL_SESSIONS_REVOKED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"  # noqa: S105


# =============================================================================
# Cache Key Prefixes
# =============================================================================
CACHE_PREFIX_SESSION = "session:"
CACHE_PREFIX_RATE_LIMIT = "rate_limit:"
CACHE_PREFIX_USER = "user:"
CACHE_PREFIX_SETTINGS = "settings:"


# =============================================================================
# Application Metadata
# =============================================================================
APP_NAME = "YUGI-AI"
APP_DESCRIPTION = "The AI Operating System — Intelligent, modular, extensible."
APP_CONTACT = {
    "name": "YUGI-AI Team",
    "url": "https://github.com/yugendragitz/YUGI-AI",
}
APP_LICENSE = {
    "name": "MIT",
    "url": "https://opensource.org/licenses/MIT",
}
