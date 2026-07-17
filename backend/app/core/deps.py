"""
YUGI-AI — Auth Dependencies
==============================

FastAPI Depends()-compatible functions for authenticating and authorizing requests.

Architecture:
    These are the "gateway guards" — they run BEFORE the route handler and either:
    - Return the authenticated user (success)
    - Raise UnauthorizedException or ForbiddenException (failure)

Usage:
    from app.core.deps import get_current_user, require_role
    from app.core.constants import UserRole

    @router.get("/profile")
    async def get_profile(user: User = Depends(get_current_user)):
        return user

    @router.get("/admin/users")
    async def admin_list(user: User = Depends(require_role(UserRole.ADMIN))):
        return await user_repo.get_all()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from app.core.constants import UserRole
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import TokenPayload, decode_access_token

if TYPE_CHECKING:
    from app.domain.auth.entities import User

logger = structlog.get_logger(__name__)

# =============================================================================
# OAuth2 Scheme
# =============================================================================
# tokenUrl points to the login endpoint — used by Swagger UI's "Authorize" button.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,  # We handle missing token ourselves for better error messages
)


# =============================================================================
# Dependencies
# =============================================================================


async def get_token_payload(
    token: str | None = Depends(oauth2_scheme),
) -> TokenPayload:
    """Extract and validate the JWT from the Authorization header.

    Returns the decoded token payload. Does NOT load the user from the database.
    Use this when you only need the user ID/role without a full DB round-trip.

    Raises:
        UnauthorizedException: If no token is provided or token is invalid.
    """
    if token is None:
        raise UnauthorizedException(
            message="Authentication required. Provide a valid access token.",
            error_code="TOKEN_MISSING",
        )
    return decode_access_token(token)


async def get_current_user(
    request: Request,
    payload: TokenPayload = Depends(get_token_payload),
) -> User:
    """Load the full authenticated user from the database.

    Raises:
        UnauthorizedException: If user not found, inactive, or deleted.
    """
    from app.api.dependencies import container
    from app.infrastructure.auth.user_repository import PostgresUserRepository
    from uuid import UUID

    # Get a single use session from the container
    db_manager = container.get_db_manager()
    async for session in db_manager.session():
        user_repo = PostgresUserRepository(session)
        user = await user_repo.get_by_id(UUID(payload.sub))

    if user is None:
        logger.warning("Token valid but user not found", user_id=payload.sub)
        raise UnauthorizedException(
            message="User account not found.",
            error_code="USER_NOT_FOUND",
        )

    if user.is_deleted:
        logger.warning("Token valid but user is deleted", user_id=payload.sub)
        raise UnauthorizedException(
            message="User account has been deleted.",
            error_code="USER_DELETED",
        )

    if not user.is_active:
        logger.warning("Token valid but user is inactive", user_id=payload.sub)
        raise UnauthorizedException(
            message="User account is disabled. Contact support.",
            error_code="USER_INACTIVE",
        )

    return user


async def require_active_user(
    user: User = Depends(get_current_user),
) -> User:
    return user


def require_role(*allowed_roles: UserRole):
    async def _role_guard(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role not in allowed_roles:
            logger.warning(
                "Role authorization failed",
                user_id=str(user.id),
                user_role=user.role,
                required_roles=[r.value for r in allowed_roles],
            )
            raise ForbiddenException(
                message="You do not have the required role for this action.",
                error_code="INSUFFICIENT_ROLE",
                details={
                    "required_roles": [r.value for r in allowed_roles],
                },
            )
        return user

    return _role_guard
