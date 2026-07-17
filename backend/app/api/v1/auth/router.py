"""
YUGI-AI — Auth Router
========================

REST API endpoints for authentication and session management.
All auth endpoints are prefixed with /api/v1/auth/.

Endpoint Summary:
    POST /auth/register   — Create account + auto-login
    POST /auth/login      — Login with email or username
    POST /auth/refresh    — Rotate refresh token + new access token
    POST /auth/logout     — End current session
    POST /auth/logout-all — End all sessions
    GET  /auth/sessions   — List active sessions
    GET  /auth/me         — Get current user profile

Cookie Management:
    Refresh token is set/cleared as an httpOnly cookie.
    Never exposed in JSON response body.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Cookie, Depends, Request, Response

from app.api.dependencies import get_auth_service
from app.api.v1.auth.schemas import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    SessionListResponse,
    SessionResponse,
    UserResponse,
)
from app.application.auth.auth_service import AuthService
from app.application.auth.dtos import DeviceInfo, LoginInput, RegisterInput
from app.core.config import get_settings
from app.core.deps import get_current_user
from app.domain.auth.entities import User

logger = structlog.get_logger(__name__)

router = APIRouter()


# =============================================================================
# Helpers
# =============================================================================


def _extract_device_info(request: Request) -> DeviceInfo:
    """Extract device metadata from the incoming request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else None

    return DeviceInfo(
        device_name=None,  # Parsed from user-agent in a future module
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
    )


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Set the refresh token as an httpOnly cookie."""
    settings = get_settings()
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.environment != "development",  # HTTPS only in production
        samesite="lax",
        path="/api/v1/auth",
        max_age=settings.auth.refresh_token_expire_days * 86400,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear the refresh token cookie."""
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
    )


def _user_response(user_output) -> UserResponse:
    """Convert UserOutput DTO to API UserResponse."""
    return UserResponse(
        id=user_output.id,
        email=user_output.email,
        username=user_output.username,
        display_name=user_output.display_name,
        role=user_output.role,
        is_active=user_output.is_active,
        is_verified=user_output.is_verified,
        avatar_seed=user_output.avatar_seed,
        avatar_style=user_output.avatar_style,
        avatar_url=user_output.avatar_url,
        last_login_at=user_output.last_login_at,
        created_at=user_output.created_at,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=200,
    summary="Register a new user account",
    description="Creates a new user account and returns an access token with auto-login.",
)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    device_info = _extract_device_info(request)

    input_data = RegisterInput(
        email=body.email,
        username=body.username,
        password=body.password,
        display_name=body.display_name,
    )

    result, refresh_token = await auth_service.register(input_data, device_info)

    _set_refresh_cookie(response, refresh_token)

    return AuthResponse(
        access_token=result.access_token,
        user=_user_response(result.user),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=200,
    summary="Login with email or username",
    description="Authenticate with email or username and password. Returns access token.",
)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    device_info = _extract_device_info(request)

    input_data = LoginInput(
        identifier=body.identifier,
        password=body.password,
    )

    result, refresh_token = await auth_service.login(input_data, device_info)

    _set_refresh_cookie(response, refresh_token)

    return AuthResponse(
        access_token=result.access_token,
        user=_user_response(result.user),
    )


@router.post(
    "/refresh",
    response_model=AuthResponse,
    status_code=200,
    summary="Refresh access token",
    description="Exchange a valid refresh token (from cookie) for a new token pair.",
)
async def refresh(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    from app.core.exceptions import UnauthorizedException

    if not refresh_token:
        raise UnauthorizedException(
            message="No refresh token provided.",
            error_code="MISSING_REFRESH_TOKEN",
        )

    device_info = _extract_device_info(request)

    result, new_refresh_token = await auth_service.refresh_token(refresh_token, device_info)

    _set_refresh_cookie(response, new_refresh_token)

    return AuthResponse(
        access_token=result.access_token,
        user=_user_response(result.user),
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=200,
    summary="Logout current session",
    description="Revoke the current session and clear the refresh token cookie.",
)
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    device_info = _extract_device_info(request)

    await auth_service.logout(
        refresh_token_plaintext=refresh_token or "",
        user_id=user.id,
        device_info=device_info,
    )

    _clear_refresh_cookie(response)

    return MessageResponse(message="Successfully logged out.")


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    status_code=200,
    summary="Logout all sessions",
    description="Revoke all active sessions for the current user.",
)
async def logout_all(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    device_info = _extract_device_info(request)

    revoked = await auth_service.logout_all(user.id, device_info)

    _clear_refresh_cookie(response)

    return MessageResponse(
        message=f"All sessions revoked. {revoked} session(s) terminated.",
    )


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    status_code=200,
    summary="List active sessions",
    description="Get all active sessions for the current user.",
)
async def list_sessions(
    request: Request,
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> SessionListResponse:
    sessions = await auth_service.get_active_sessions(user.id)

    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s.id,
                device_name=s.device_name,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                last_used_at=s.last_used_at,
                created_at=s.created_at,
            )
            for s in sessions
        ],
        total=len(sessions),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=200,
    summary="Get current user profile",
    description="Returns the authenticated user's profile data.",
)
async def get_me(
    request: Request,
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    profile = await auth_service.get_current_user_profile(user.id)
    return _user_response(profile)
