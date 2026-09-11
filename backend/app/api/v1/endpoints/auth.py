"""Authentication endpoints: login, logout, current user, and the login page."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.api.deps import require_auth
from app.core.config import settings
from app.services.auth_service import auth_service

router = APIRouter()

SESSION_COOKIE = "torqueai_session"


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page() -> HTMLResponse:
    """Serve the browser login page."""
    return HTMLResponse(_LOGIN_PAGE)


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(payload: LoginRequest, response: Response) -> dict:
    token = auth_service.login(payload.username, payload.password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
        )
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=settings.SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=not settings.DEBUG,
        path="/",
    )
    return {"status": "ok", "username": payload.username}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> dict:
    auth_service.logout(session)
    response.delete_cookie(key=SESSION_COOKIE, path="/")
    return {"status": "ok"}


@router.get("/me")
async def me(username: str = Depends(require_auth)) -> dict:
    return {"authenticated": True, "username": username}


_LOGIN_PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TorqueAI — Entrar</title>
  <style>
    :root { --bg:#0e1216; --panel:#1a2229; --line:#2a3540; --ink:#e8edf1; --muted:#8fa1af; --accent:#f5a623; }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center; color:var(--ink); background:radial-gradient(1200px 600px at 80% -10%, #1b2730 0%, var(--bg) 55%); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
    .card { width:min(380px, 92vw); background:var(--panel); border:1px solid var(--line); border-radius:14px; box-shadow:0 18px 44px rgba(0,0,0,.4); padding:32px 28px; }
    .brand { display:flex; align-items:center; gap:10px; margin-bottom:20px; }
    .brand h1 { margin:0; font-size:22px; }
    .brand h1 span { color:var(--accent); }
    .brand p { margin:2px 0 0; font-size:12px; color:var(--muted); }
    label { display:block; font-size:11px; text-transform:uppercase; letter-spacing:.8px; color:var(--muted); margin:14px 0 6px; font-weight:600; }
    input { width:100%; background:var(--bg); border:1px solid var(--line); color:var(--ink); border-radius:8px; padding:11px 13px; font:inherit; }
    input:focus { outline:none; border-color:var(--accent); }
    button { width:100%; margin-top:22px; border:0; cursor:pointer; background:var(--accent); color:#17120a; font-weight:700; border-radius:10px; padding:13px; font:inherit; }
    button:hover { background:#e08914; }
    .err { color:#e0553d; font-size:13px; margin-top:14px; text-align:center; display:none; }
    .err.show { display:block; }
  </style>
</head>
<body>
  <div class="card">
    <div class="brand"><div><h1>Torque<span>AI</span></h1><p>Assistente de oficina — acesso restrito</p></div></div>
    <form id="form">
      <label for="username">Usuário</label>
      <input id="username" name="username" autocomplete="username" required>
      <label for="password">Senha</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required>
      <button type="submit">Entrar</button>
      <div class="err" id="err">Credenciais inválidas.</div>
    </form>
  </div>
<script>
const form = document.querySelector('#form');
form.addEventListener('submit', async ev => {
  ev.preventDefault();
  const err = document.querySelector('#err');
  err.classList.remove('show');
  const username = document.querySelector('#username').value.trim();
  const password = document.querySelector('#password').value;
  const res = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  if (res.ok) {
    window.location.href = '/api/v1/chat/';
  } else {
    err.classList.add('show');
  }
});
</script>
</body></html>"""


# --- Convenience: set/clear helpers reused by the auth flow ---


def session_cookie_options() -> dict:
    return {
        "key": SESSION_COOKIE,
        "httponly": True,
        "samesite": "lax",
        "secure": not settings.DEBUG,
        "path": "/",
    }