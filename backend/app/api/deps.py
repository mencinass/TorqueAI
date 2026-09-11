from typing import AsyncGenerator, Optional
from fastapi import Cookie, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_async_session
from app.services.auth_service import auth_service


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding an active async SQLAlchemy database session."""
    async for session in get_async_session():
        yield session


async def require_auth(session: Optional[str] = Cookie(default=None, alias="torqueai_session")) -> str:
    """Dependency enforcing an authenticated session via HttpOnly cookie.

    Returns the authenticated username, or raises HTTP 401.
    """
    username = auth_service.current_username(session)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Cookie"},
        )
    return username

