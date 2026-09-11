"""Tests for authentication (login/logout/session) and AI guardrails."""

from __future__ import annotations

import pytest
import httpx

from app.core import security
from app.agents.prompt import SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def test_password_hash_and_verify_roundtrip():
    stored = security.hash_password("s3cret")
    assert stored != "s3cret"
    assert security.verify_password("s3cret", stored) is True
    assert security.verify_password("wrong", stored) is False


def test_password_hash_is_salted():
    h1 = security.hash_password("same")
    h2 = security.hash_password("same")
    assert h1 != h2  # different salt each time
    assert security.verify_password("same", h1)
    assert security.verify_password("same", h2)


# ---------------------------------------------------------------------------
# Session tokens
# ---------------------------------------------------------------------------


def test_session_roundtrip_and_revoke():
    token = security.create_session("admin", ttl_seconds=60)
    assert security.validate_session(token, ttl_seconds=60) == "admin"
    security.revoke_session(token)
    assert security.validate_session(token, ttl_seconds=60) is None


def test_session_token_is_unpredictable():
    t1 = security.create_session("admin", ttl_seconds=60)
    t2 = security.create_session("admin", ttl_seconds=60)
    assert t1 != t2


# ---------------------------------------------------------------------------
# Login / logout endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_rejects_bad_credentials(async_client: httpx.AsyncClient):
    from app.core.config import settings
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": settings.ADMIN_USERNAME, "password": "definitely-wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_logout_flow(async_client: httpx.AsyncClient):
    from app.core.config import settings
    # Login sets a session cookie.
    login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD},
    )
    assert login.status_code == 200
    assert "torqueai_session" in async_client.cookies

    # /me returns authenticated with the cookie.
    me = await async_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["authenticated"] is True

    # Logout clears the session.
    logout = await async_client.post("/api/v1/auth/logout")
    assert logout.status_code == 200

    # Post-logout /me is rejected.
    me2 = await async_client.get("/api/v1/auth/me")
    assert me2.status_code == 401


@pytest.mark.asyncio
async def test_ingestion_requires_auth(async_client: httpx.AsyncClient):
    response = await async_client.get("/api/v1/ingestion/jobs")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# AI guardrails (prompt content)
# ---------------------------------------------------------------------------


def test_system_prompt_has_guardrails():
    prompt = SYSTEM_PROMPT.lower()
    assert "seguranca" in prompt or "segurança" in prompt
    assert "torque" in prompt
    assert "evidencia" in prompt or "evidência" in prompt
    assert "portugues" in prompt.lower() or "português" in prompt.lower()