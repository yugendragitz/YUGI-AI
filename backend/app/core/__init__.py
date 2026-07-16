"""
YUGI-AI — Core Package
=======================

Cross-cutting concerns shared across all layers.
This package has NO dependencies on domain, application, or infrastructure layers.

Exports:
    - AppSettings: Central configuration
    - AppException and subclasses: Exception hierarchy
    - get_logger: Structured logger factory
    - EntityId, JSON: Common type aliases
"""

from app.core.config import AppSettings
from app.core.constants import API_V1_PREFIX, CORRELATION_ID_HEADER, Environment
from app.core.exceptions import (
    AppException,
    ConflictException,
    ExternalServiceException,
    ForbiddenException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
    ValidationException,
)
from app.core.types import JSON, EntityId

__all__ = [
    # Config
    "AppSettings",
    # Constants
    "API_V1_PREFIX",
    "CORRELATION_ID_HEADER",
    "Environment",
    # Exceptions
    "AppException",
    "ConflictException",
    "ExternalServiceException",
    "ForbiddenException",
    "NotFoundException",
    "RateLimitException",
    "UnauthorizedException",
    "ValidationException",
    # Types
    "EntityId",
    "JSON",
]
