"""
YUGI-AI — Security Utilities
==============================

JWT token management, refresh token generation, cryptographic hashing,
and Fernet encryption for BYOK API keys.

Architecture:
    - JWT (python-jose): Access token creation and verification with role claims.
    - SHA-256: Refresh token hashing for database storage (never store plaintext).
    - Fernet (cryptography): Symmetric encryption for user API keys (ADR-005).
    - secrets: Cryptographically secure random token generation.

Usage:
    from app.core.security import create_access_token, decode_access_token

    token = create_access_token(user_id=user.id, email=user.email, role=user.role)
    payload = decode_access_token(token)
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt  # type: ignore[import-untyped]
from pydantic import BaseModel

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


# =============================================================================
# Token Payload Schema
# =============================================================================


class TokenPayload(BaseModel):
    """Decoded JWT access token payload.

    Validated after decoding to ensure all expected claims are present.
    """

    sub: str  # User ID (UUID string)
    email: str
    role: str  # UserRole value
    type: str  # "access"
    jti: str  # Unique token ID
    exp: int  # Expiration timestamp
    iat: int  # Issued-at timestamp


# =============================================================================
# JWT Access Token
# =============================================================================


def create_access_token(
    *,
    user_id: str,
    email: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        user_id: User's UUID string (becomes the 'sub' claim).
        email: User's email address.
        role: User's role (e.g., "user", "admin").
        expires_delta: Custom expiration. Defaults to settings.auth.access_token_expire_minutes.

    Returns:
        Signed JWT string.
    """
    settings = get_settings()
    now = datetime.now(UTC)

    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.auth.access_token_expire_minutes)

    claims: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "role": role,
        "type": "access",
        "jti": secrets.token_hex(16),  # Unique token ID
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }

    return str(
        jwt.encode(
            claims,
            settings.auth.secret_key,
            algorithm=settings.auth.jwt_algorithm,
        )
    )


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT string from the Authorization header.

    Returns:
        Validated TokenPayload with user info and claims.

    Raises:
        UnauthorizedException: If the token is invalid, expired, or malformed.
    """
    from app.core.exceptions import UnauthorizedException

    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.auth.secret_key,
            algorithms=[settings.auth.jwt_algorithm],
        )
    except JWTError as exc:
        logger.warning("JWT decode failed", error=str(exc))
        raise UnauthorizedException(
            message="Invalid or expired access token.",
            error_code="INVALID_TOKEN",
        ) from exc

    # Verify token type
    if payload.get("type") != "access":
        raise UnauthorizedException(
            message="Invalid token type.",
            error_code="INVALID_TOKEN_TYPE",
        )

    try:
        return TokenPayload(**payload)
    except Exception as exc:
        logger.warning("JWT payload validation failed", error=str(exc))
        raise UnauthorizedException(
            message="Malformed token payload.",
            error_code="MALFORMED_TOKEN",
        ) from exc


# =============================================================================
# Refresh Token
# =============================================================================


def generate_refresh_token() -> str:
    """Generate a cryptographically secure refresh token.

    Returns a 128-character hex string (64 bytes of entropy).
    This is the plaintext token sent to the client in an httpOnly cookie.
    Store only the SHA-256 hash in the database.

    Returns:
        128-character hex string.
    """
    return secrets.token_hex(64)


def hash_token(token: str) -> str:
    """Hash a token using SHA-256 for database storage.

    The plaintext refresh token is NEVER stored in the database.
    Only the hash is persisted, and lookup is done by hashing the
    incoming token and comparing.

    Args:
        token: Plaintext token string.

    Returns:
        64-character hex digest of SHA-256 hash.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# =============================================================================
# Fernet Encryption (BYOK API Keys — ADR-005)
# =============================================================================


def _get_fernet() -> Fernet:
    """Get a Fernet instance using the configured encryption key.

    The encryption key must be a valid Fernet key (URL-safe base64-encoded 32 bytes).
    Generate one with:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """
    settings = get_settings()
    return Fernet(settings.auth.encryption_key.encode("utf-8"))


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext value using Fernet symmetric encryption.

    Used for storing user API keys (BYOK) at rest.

    Args:
        plaintext: The value to encrypt (e.g., OpenAI API key).

    Returns:
        Encrypted ciphertext as a UTF-8 string.
    """
    fernet = _get_fernet()
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted value.

    Args:
        ciphertext: The encrypted value.

    Returns:
        Original plaintext string.

    Raises:
        AppException: If decryption fails (wrong key, tampered data).
    """
    from app.core.exceptions import AppException

    fernet = _get_fernet()
    try:
        return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        logger.error("Fernet decryption failed — possible key rotation or data tampering")
        raise AppException(
            message="Failed to decrypt value. Encryption key may have changed.",
            error_code="DECRYPTION_FAILED",
            http_status=500,
        ) from exc
