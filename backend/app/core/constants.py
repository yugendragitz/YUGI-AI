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
# Security
# =============================================================================
BCRYPT_ROUNDS = 12
"""Number of bcrypt hashing rounds. 12 is ~250ms on modern hardware."""

MIN_PASSWORD_LENGTH = 8
"""Minimum password length enforced during registration."""

MAX_PASSWORD_LENGTH = 128
"""Maximum password length. Prevents bcrypt DoS (bcrypt truncates at 72 bytes)."""


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
