from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding an active async SQLAlchemy database session."""
    async for session in get_async_session():
        yield session

