"""
YUGI-AI — Auth Data Transfer Objects
=======================================

Pydantic models for auth service input/output.
These are NOT the API schemas (those are in api/v1/auth/schemas.py).

DTOs bridge the presentation layer and the application layer:
    API Schema (request) → DTO (service input) → Domain Entity
    → DTO (service output) → API Schema (response)

Usage:
    from app.application.auth.dtos import RegisterInput, AuthResult
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import UserRole
from app.core.types import EntityId


class RegisterInput(BaseModel):
    """Input DTO for user registration."""

    email: str
    username: str
    password: str
    display_name: str


class LoginInput(BaseModel):
    """Input DTO for user login.

    The 'identifier' field accepts either an email or a username.
    Auto-detection: if it contains '@', it's treated as an email.
    """

    identifier: str
    password: str


class DeviceInfo(BaseModel):
    """Device metadata captured during login/registration."""

    device_name: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class UserOutput(BaseModel):
    """Sanitized user data for API responses.

    NEVER includes password_hash or deleted_at.
    """

    id: EntityId
    email: str
    username: str
    display_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    avatar_seed: str
    avatar_style: str
    avatar_url: str | None
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResult(BaseModel):
    """Result returned from register/login/refresh operations."""

    access_token: str
    token_type: str = Field(default="bearer")
    user: UserOutput


class SessionOutput(BaseModel):
    """Session details for the "Active Sessions" UI."""

    id: EntityId
    device_name: str | None
    ip_address: str | None
    user_agent: str | None
    is_current: bool = False  # Set by the router based on the current session
    last_used_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
