"""Authentication service: credential check, session lifecycle, and login guards."""

from __future__ import annotations

import hmac
from typing import Optional

from app.core.config import settings
from app.core import security


class AuthService:
    """Single-admin authentication backed by env-configured credentials."""

    def __init__(self) -> None:
        # Hash the configured password once at startup so plaintext is not
        # retained in memory beyond ingestion of the settings value.
        self._password_hash = security.hash_password(settings.ADMIN_PASSWORD)

    def login(self, username: str, password: str) -> Optional[str]:
        """Return a session token on success, or None if rejected.

        Enforces brute-force lockout per username.
        """
        username = (username or "").strip()
        if not username:
            return None
        if security.is_locked(username):
            return None

        user_ok = hmac.compare_digest(username, settings.ADMIN_USERNAME)
        pass_ok = security.verify_password(password or "", self._password_hash)
        if not (user_ok and pass_ok):
            security.record_failure(
                username,
                settings.LOGIN_LOCKOUT_SECONDS,
                settings.LOGIN_MAX_ATTEMPTS,
            )
            return None

        security.reset_failures(username)
        return security.create_session(username, settings.SESSION_TTL_SECONDS)

    def logout(self, token: Optional[str]) -> None:
        security.revoke_session(token)

    def current_username(self, token: Optional[str]) -> Optional[str]:
        return security.validate_session(token, settings.SESSION_TTL_SECONDS)


# Shared instance used by both the auth endpoint and the require_auth dependency.
auth_service = AuthService()