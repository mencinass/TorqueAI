"""Security primitives: password hashing and opaque session tokens.

Uses only the Python standard library (``hashlib``, ``hmac``, ``secrets``) so
no third-party auth dependency is required.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

_PBKDF2_ITERATIONS = 200_000
_SALT_BYTES = 16
_HASH_BYTES = 32

# In-memory session store: token_hash -> (username, expires_at_epoch)
# Kept in memory by design (same trade-off as the ingestion JobTracker).
_sessions: Dict[str, tuple[str, float]] = {}

# Simple brute-force backoff: username -> (fail_count, locked_until_epoch)
_failures: Dict[str, tuple[int, float]] = {}


# ---------------------------------------------------------------------------
# Password hashing (PBKDF2-HMAC-SHA256)
# ---------------------------------------------------------------------------


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """Return a salted PBKDF2 hash as ``iterations$salt_hex$hash_hex``."""
    salt = salt or secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS, dklen=_HASH_BYTES
    )
    return f"{_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time compare of ``password`` against a stored PBKDF2 hash."""
    try:
        iterations, salt_hex, hash_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, int(iterations), dklen=len(expected)
    )
    return hmac.compare_digest(digest, expected)


# ---------------------------------------------------------------------------
# Opaque session tokens
# ---------------------------------------------------------------------------


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(username: str, ttl_seconds: int) -> str:
    """Create a session, store its hash, and return the raw token."""
    token = secrets.token_urlsafe(32)
    expires = time.time() + ttl_seconds
    _sessions[_hash_token(token)] = (username, expires)
    logger.info("session_created", extra={"username": username, "ttl": ttl_seconds})
    return token


def validate_session(token: Optional[str], ttl_seconds: int) -> Optional[str]:
    """Return the username if ``token`` maps to a live, unexpired session."""
    if not token:
        return None
    key = _hash_token(token)
    entry = _sessions.get(key)
    if entry is None:
        return None
    username, expires = entry
    if time.time() > expires:
        _sessions.pop(key, None)
        return None
    # Sliding renewal: refresh expiry on activity.
    _sessions[key] = (username, time.time() + ttl_seconds)
    return username


def revoke_session(token: Optional[str]) -> None:
    if token:
        _sessions.pop(_hash_token(token), None)
        logger.info("session_revoked")


# ---------------------------------------------------------------------------
# Brute-force backoff on login
# ---------------------------------------------------------------------------


def is_locked(username: str) -> bool:
    entry = _failures.get(username)
    if entry is None:
        return False
    _, locked_until = entry
    if time.time() > locked_until:
        _failures.pop(username, None)
        return False
    return True


def record_failure(username: str, lockout_seconds: int, max_attempts: int) -> None:
    count, _ = _failures.get(username, (0, 0.0))
    count += 1
    locked_until = 0.0
    if count >= max_attempts:
        locked_until = time.time() + lockout_seconds
    _failures[username] = (count, locked_until)
    logger.warning("login_failure", extra={"username": username, "count": count})


def reset_failures(username: str) -> None:
    _failures.pop(username, None)