"""
YUGI-AI — Authentication Service
===================================

Core authentication use case orchestrator.
Coordinates: UserRepository, SessionRepository, PasswordService, AuditService.

All business rules for registration, login, token refresh, logout are here.
This service has NO knowledge of HTTP (no Request, Response, cookies).

Usage:
    auth_service = AuthService(
        user_repo=user_repo,
        session_repo=session_repo,
        password_svc=password_svc,
        audit_svc=audit_svc,
    )
    result = await auth_service.register(input, device_info)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from app.application.auth.audit_service import AuditService
from app.application.auth.dtos import (
    AuthResult,
    DeviceInfo,
    LoginInput,
    RegisterInput,
    SessionOutput,
    UserOutput,
)
from app.application.auth.password_service import PasswordService
from app.application.base import BaseService
from app.core.config import get_settings
from app.core.constants import AuditEventType, UserRole
from app.core.exceptions import (
    ConflictException,
    UnauthorizedException,
    ValidationException,
)
from app.core.security import create_access_token, generate_refresh_token, hash_token
from app.core.types import EntityId
from app.domain.auth.entities import Session, User
from app.domain.auth.repositories import SessionRepository, UserRepository


class AuthService(BaseService):
    """Authentication use case orchestrator.

    Responsibilities:
    - Register: validate input, check uniqueness, hash password, create user + session
    - Login: find user by identifier, verify password, create session
    - Refresh: validate refresh token, rotate, detect theft
    - Logout: revoke session
    - Logout All: revoke all sessions for a user
    """

    def __init__(
        self,
        *,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        password_svc: PasswordService,
        audit_svc: AuditService,
    ) -> None:
        super().__init__()
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._password_svc = password_svc
        self._audit_svc = audit_svc

    # =========================================================================
    # Register
    # =========================================================================

    async def register(
        self,
        input_data: RegisterInput,
        device_info: DeviceInfo,
    ) -> tuple[AuthResult, str]:
        """Register a new user account.

        Args:
            input_data: Registration form data (email, username, password, display_name).
            device_info: Client device information.

        Returns:
            Tuple of (AuthResult, refresh_token_plaintext).
            The refresh token must be set as an httpOnly cookie by the router.

        Raises:
            ValidationException: Password doesn't meet strength requirements.
            ConflictException: Email or username already taken.
        """
        await self._log_operation("register", email=input_data.email)

        # 1. Validate password strength
        violations = self._password_svc.validate_strength(input_data.password)
        if violations:
            raise ValidationException(
                message="Password does not meet requirements.",
                error_code="WEAK_PASSWORD",
                details={"violations": violations},
            )

        # 2. Check uniqueness
        if await self._user_repo.exists_by_email(input_data.email):
            raise ConflictException(
                message="An account with this email already exists.",
                error_code="EMAIL_EXISTS",
            )
        if await self._user_repo.exists_by_username(input_data.username):
            raise ConflictException(
                message="This username is already taken.",
                error_code="USERNAME_EXISTS",
            )

        # 3. Create user entity
        user = User(
            email=input_data.email.lower().strip(),
            username=input_data.username.strip(),
            display_name=input_data.display_name.strip(),
            password_hash=self._password_svc.hash_password(input_data.password),
            role=UserRole.USER,
            avatar_seed=str(uuid.uuid4()),
        )
        user = await self._user_repo.create(user)

        # 4. Create session + tokens
        refresh_token, auth_result = await self._create_session(user, device_info)

        # 5. Audit
        await self._audit_svc.log_event(
            event_type=AuditEventType.USER_REGISTERED,
            user_id=user.id,
            ip_address=device_info.ip_address,
            user_agent=device_info.user_agent,
            metadata={"email": user.email, "username": user.username},
        )

        self._logger.info("User registered", user_id=str(user.id), email=user.email)
        return auth_result, refresh_token

    # =========================================================================
    # Login
    # =========================================================================

    async def login(
        self,
        input_data: LoginInput,
        device_info: DeviceInfo,
    ) -> tuple[AuthResult, str]:
        """Authenticate a user by email or username.

        Args:
            input_data: Login credentials (identifier + password).
            device_info: Client device information.

        Returns:
            Tuple of (AuthResult, refresh_token_plaintext).

        Raises:
            UnauthorizedException: Invalid credentials (same error for wrong
                email/username AND wrong password to prevent enumeration).
        """
        await self._log_operation("login", identifier=input_data.identifier)

        # 1. Find user by email or username
        user = await self._user_repo.get_by_identifier(input_data.identifier)

        if user is None:
            # Audit failed login — unknown user
            await self._audit_svc.log_event(
                event_type=AuditEventType.LOGIN_FAILED,
                ip_address=device_info.ip_address,
                user_agent=device_info.user_agent,
                metadata={
                    "identifier": input_data.identifier,
                    "reason": "user_not_found",
                },
            )
            # Same error message to prevent user enumeration
            raise UnauthorizedException(
                message="Invalid email/username or password.",
                error_code="INVALID_CREDENTIALS",
            )

        # 2. Verify password
        if not self._password_svc.verify_password(input_data.password, user.password_hash):
            await self._audit_svc.log_event(
                event_type=AuditEventType.LOGIN_FAILED,
                user_id=user.id,
                ip_address=device_info.ip_address,
                user_agent=device_info.user_agent,
                metadata={
                    "identifier": input_data.identifier,
                    "reason": "invalid_password",
                },
            )
            raise UnauthorizedException(
                message="Invalid email/username or password.",
                error_code="INVALID_CREDENTIALS",
            )

        # 3. Check account status
        if not user.is_active:
            raise UnauthorizedException(
                message="Account is disabled. Contact support.",
                error_code="ACCOUNT_DISABLED",
            )

        # 4. Create session + tokens
        refresh_token, auth_result = await self._create_session(user, device_info)

        # 5. Update last login
        user.last_login_at = datetime.now(UTC)
        user.touch()
        await self._user_repo.update(user)

        # 6. Audit
        await self._audit_svc.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id=user.id,
            ip_address=device_info.ip_address,
            user_agent=device_info.user_agent,
            metadata={
                "identifier": input_data.identifier,
                "session_id": str(auth_result.user.id),  # Will be fixed below
            },
        )

        self._logger.info("User logged in", user_id=str(user.id))
        return auth_result, refresh_token

    # =========================================================================
    # Token Refresh
    # =========================================================================

    async def refresh_token(
        self,
        refresh_token_plaintext: str,
        device_info: DeviceInfo,
    ) -> tuple[AuthResult, str]:
        """Rotate the refresh token and issue a new access token.

        Security:
        - The old refresh token is invalidated (hash replaced).
        - If a revoked session's token is reused → theft detected → revoke ALL sessions.

        Args:
            refresh_token_plaintext: The plaintext refresh token from the httpOnly cookie.
            device_info: Client device information.

        Returns:
            Tuple of (AuthResult, new_refresh_token_plaintext).

        Raises:
            UnauthorizedException: Token invalid, session revoked/expired, or theft detected.
        """
        token_hash = hash_token(refresh_token_plaintext)
        session = await self._session_repo.get_by_token_hash(token_hash)

        if session is None:
            raise UnauthorizedException(
                message="Invalid refresh token.",
                error_code="INVALID_REFRESH_TOKEN",
            )

        # THEFT DETECTION: If session is revoked, the token was already rotated.
        # Someone is using an old token → revoke ALL sessions for safety.
        if session.is_revoked:
            self._logger.critical(
                "Refresh token reuse detected — possible theft!",
                session_id=str(session.id),
                user_id=str(session.user_id),
            )
            revoked_count = await self._session_repo.revoke_all_by_user(session.user_id)

            await self._audit_svc.log_event(
                event_type=AuditEventType.SUSPICIOUS_REFRESH,
                user_id=session.user_id,
                ip_address=device_info.ip_address,
                user_agent=device_info.user_agent,
                metadata={
                    "session_id": str(session.id),
                    "revoked_sessions": revoked_count,
                },
            )

            raise UnauthorizedException(
                message="Security alert: session compromised. All sessions revoked.",
                error_code="TOKEN_THEFT_DETECTED",
            )

        # Check expiry
        if session.expires_at < datetime.now(UTC):
            raise UnauthorizedException(
                message="Refresh token has expired. Please login again.",
                error_code="REFRESH_TOKEN_EXPIRED",
            )

        # Load user
        user = await self._user_repo.get_by_id(session.user_id)
        if user is None or not user.is_active or user.is_deleted:
            raise UnauthorizedException(
                message="User account not found or inactive.",
                error_code="USER_UNAVAILABLE",
            )

        # ROTATE: Generate new refresh token
        new_refresh_token = generate_refresh_token()
        new_hash = hash_token(new_refresh_token)

        # Revoke old session (mark as revoked, don't delete)
        session.is_revoked = True
        session.touch()
        await self._session_repo.update(session)

        # Create new session with new token hash
        settings = get_settings()
        new_session = Session(
            user_id=user.id,
            refresh_token_hash=new_hash,
            device_name=device_info.device_name or session.device_name,
            ip_address=device_info.ip_address or session.ip_address,
            user_agent=device_info.user_agent or session.user_agent,
            expires_at=datetime.now(UTC) + timedelta(days=settings.auth.refresh_token_expire_days),
            last_used_at=datetime.now(UTC),
        )
        await self._session_repo.create(new_session)

        # Generate new access token
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role.value if isinstance(user.role, UserRole) else user.role,
        )

        # Audit
        await self._audit_svc.log_event(
            event_type=AuditEventType.TOKEN_REFRESHED,
            user_id=user.id,
            ip_address=device_info.ip_address,
            metadata={"session_id": str(new_session.id)},
        )

        auth_result = AuthResult(
            access_token=access_token,
            user=self._to_user_output(user),
        )
        return auth_result, new_refresh_token

    # =========================================================================
    # Logout
    # =========================================================================

    async def logout(
        self,
        refresh_token_plaintext: str,
        user_id: EntityId,
        device_info: DeviceInfo,
    ) -> None:
        """End the current session by revoking the refresh token.

        Args:
            refresh_token_plaintext: The refresh token from the cookie.
            user_id: The authenticated user's ID.
            device_info: Client device information.
        """
        if refresh_token_plaintext:
            token_hash = hash_token(refresh_token_plaintext)
            session = await self._session_repo.get_by_token_hash(token_hash)
            if session and session.user_id == user_id:
                session.is_revoked = True
                session.touch()
                await self._session_repo.update(session)

                await self._audit_svc.log_event(
                    event_type=AuditEventType.USER_LOGGED_OUT,
                    user_id=user_id,
                    ip_address=device_info.ip_address,
                    metadata={"session_id": str(session.id)},
                )

        self._logger.info("User logged out", user_id=str(user_id))

    async def logout_all(
        self,
        user_id: EntityId,
        device_info: DeviceInfo,
        reason: str = "user_request",
    ) -> int:
        """Revoke all sessions for a user.

        Used for:
        - "Logout all devices" feature
        - Theft detection response
        - Post-password-change security

        Returns:
            Number of sessions revoked.
        """
        revoked = await self._session_repo.revoke_all_by_user(user_id)

        await self._audit_svc.log_event(
            event_type=AuditEventType.ALL_SESSIONS_REVOKED,
            user_id=user_id,
            ip_address=device_info.ip_address,
            metadata={"session_count": revoked, "reason": reason},
        )

        self._logger.info(
            "All sessions revoked",
            user_id=str(user_id),
            count=revoked,
            reason=reason,
        )
        return revoked

    # =========================================================================
    # Session Management
    # =========================================================================

    async def get_active_sessions(self, user_id: EntityId) -> list[SessionOutput]:
        """Get all active sessions for a user.

        Returns sanitized session data for the "Active Sessions" UI.
        """
        sessions = await self._session_repo.get_active_by_user(user_id)
        return [
            SessionOutput(
                id=s.id,
                device_name=s.device_name,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                last_used_at=s.last_used_at,
                created_at=s.created_at,
            )
            for s in sessions
        ]

    async def get_current_user_profile(self, user_id: EntityId) -> UserOutput:
        """Get the current user's profile.

        Returns sanitized user data (no password_hash, no deleted_at).

        Raises:
            UnauthorizedException: If user not found or deleted.
        """
        user = await self._user_repo.get_by_id(user_id)
        if user is None or user.is_deleted:
            raise UnauthorizedException(
                message="User account not found.",
                error_code="USER_NOT_FOUND",
            )
        return self._to_user_output(user)

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _create_session(
        self,
        user: User,
        device_info: DeviceInfo,
    ) -> tuple[str, AuthResult]:
        """Create a new session with refresh token and access token.

        Returns:
            Tuple of (refresh_token_plaintext, AuthResult).
        """
        settings = get_settings()

        # Generate tokens
        refresh_token = generate_refresh_token()
        token_hash = hash_token(refresh_token)

        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role.value if isinstance(user.role, UserRole) else user.role,
        )

        # Create session entity
        session = Session(
            user_id=user.id,
            refresh_token_hash=token_hash,
            device_name=device_info.device_name,
            ip_address=device_info.ip_address,
            user_agent=device_info.user_agent,
            expires_at=datetime.now(UTC) + timedelta(days=settings.auth.refresh_token_expire_days),
            last_used_at=datetime.now(UTC),
        )
        await self._session_repo.create(session)

        auth_result = AuthResult(
            access_token=access_token,
            user=self._to_user_output(user),
        )
        return refresh_token, auth_result

    @staticmethod
    def _to_user_output(user: User) -> UserOutput:
        """Convert a User domain entity to a sanitized UserOutput DTO."""
        return UserOutput(
            id=user.id,
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            role=user.role if isinstance(user.role, UserRole) else UserRole(user.role),
            is_active=user.is_active,
            is_verified=user.is_verified,
            avatar_seed=user.avatar_seed,
            avatar_style=user.avatar_style,
            avatar_url=user.avatar_url,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
