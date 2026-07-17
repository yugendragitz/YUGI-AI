"""
YUGI-AI — Auth API Schemas
==============================

Pydantic request/response models for the auth REST API.
These are the HTTP layer contracts — separate from application DTOs.

Request schemas validate client input.
Response schemas serialize service output.
"""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.constants import MIN_PASSWORD_LENGTH, UserRole
from app.core.types import EntityId

# =============================================================================
# Request Schemas
# =============================================================================


class RegisterRequest(BaseModel):
    """Registration request body."""

    email: EmailStr = Field(
        ...,
        max_length=255,
        examples=["user@yugi.ai"],
        description="Valid email address.",
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        examples=["yugiuser"],
        description="Unique username (3-50 chars, lowercase alphanumeric + underscore).",
    )
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=128,
        examples=["MyStr0ngP@ssw0rd!"],
        description=f"Password ({MIN_PASSWORD_LENGTH}+ chars, upper/lower/digit/special).",
    )
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["Yugi User"],
        description="Display name (1-100 chars).",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Username must be lowercase alphanumeric + underscores only."""
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9_]+$", v):
            msg = "Username must contain only lowercase letters, digits, and underscores."
            raise ValueError(msg)
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.strip().lower()


class LoginRequest(BaseModel):
    """Login request body — accepts email or username."""

    identifier: str = Field(
        ...,
        min_length=3,
        max_length=255,
        examples=["user@yugi.ai", "yugiuser"],
        description="Email address or username.",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Account password.",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class UserResponse(BaseModel):
    """Public user representation — NEVER includes password_hash."""

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


class AuthResponse(BaseModel):
    """Authentication response — returned after register/login/refresh."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105
    user: UserResponse


class SessionResponse(BaseModel):
    """Active session details for the "Manage Sessions" UI."""

    id: EntityId
    device_name: str | None
    ip_address: str | None
    user_agent: str | None
    is_current: bool = False
    last_used_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    """List of active sessions."""

    sessions: list[SessionResponse]
    total: int


class MessageResponse(BaseModel):
    """Generic success message response."""

    message: str
    detail: str | None = None
