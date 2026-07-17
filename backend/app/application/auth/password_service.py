"""
YUGI-AI — Password Service
=============================

Argon2id password hashing and password policy enforcement.

Argon2id is the OWASP-recommended password hashing algorithm (2024):
- Memory-hard: resistant to GPU/ASIC brute force
- No length truncation (unlike bcrypt's 72-byte limit)
- Hybrid of Argon2i (side-channel resistant) and Argon2d (GPU resistant)

Password Policy:
- 12+ characters (exceeds NIST 800-63B minimum of 8)
- At least 1 uppercase, 1 lowercase, 1 digit, 1 special character
- All violations returned at once (not one at a time)

Usage:
    from app.application.auth.password_service import PasswordService

    svc = PasswordService()
    hashed = svc.hash_password("MyStr0ng!Pass")
    ok = svc.verify_password("MyStr0ng!Pass", hashed)
    violations = svc.validate_strength("weak")
"""

from __future__ import annotations

import re

from passlib.hash import argon2  # type: ignore[import-untyped]

from app.core.constants import (
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_TIME_COST,
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    PASSWORD_REQUIRE_DIGIT,
    PASSWORD_REQUIRE_LOWERCASE,
    PASSWORD_REQUIRE_SPECIAL,
    PASSWORD_REQUIRE_UPPERCASE,
)


class PasswordService:
    """Password hashing and policy enforcement using Argon2id.

    This is a stateless service — no constructor dependencies.
    Can be instantiated directly or via the DI container.
    """

    def __init__(self) -> None:
        """Configure Argon2id with OWASP-recommended parameters."""
        self._hasher = argon2.using(
            type="ID",  # Argon2id (hybrid)
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
        )

    def hash_password(self, plain_password: str) -> str:
        """Hash a password using Argon2id.

        Args:
            plain_password: The plaintext password.

        Returns:
            Argon2id hash string (includes algorithm parameters and salt).
        """
        return str(self._hasher.hash(plain_password))

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against an Argon2id hash.

        Uses constant-time comparison to prevent timing attacks.

        Args:
            plain_password: The plaintext password to verify.
            hashed_password: The stored Argon2id hash.

        Returns:
            True if the password matches, False otherwise.
        """
        try:
            return bool(self._hasher.verify(plain_password, hashed_password))
        except Exception:
            # Malformed hash string — treat as non-match
            return False

    @staticmethod
    def validate_strength(password: str) -> list[str]:
        """Validate password strength against the configured policy.

        Returns ALL violations at once so the user can fix everything
        in a single attempt, not one error at a time.

        Args:
            password: The plaintext password to validate.

        Returns:
            List of violation messages. Empty list = password passes all checks.
        """
        violations: list[str] = []

        # Length checks
        if len(password) < MIN_PASSWORD_LENGTH:
            violations.append(f"Must be at least {MIN_PASSWORD_LENGTH} characters long.")

        if len(password) > MAX_PASSWORD_LENGTH:
            violations.append(f"Must not exceed {MAX_PASSWORD_LENGTH} characters.")

        # Character class checks
        if PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            violations.append("Must contain at least one uppercase letter (A-Z).")

        if PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            violations.append("Must contain at least one lowercase letter (a-z).")

        if PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", password):
            violations.append("Must contain at least one digit (0-9).")

        if PASSWORD_REQUIRE_SPECIAL and not re.search(
            r"[!@#$%^&*()\-_=+\[\]{}|;:'\",.<>?/~`\\]", password
        ):
            violations.append("Must contain at least one special character.")

        return violations
