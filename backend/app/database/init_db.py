from sqlalchemy.ext.asyncio import AsyncEngine
from app.core.logging import logger
from app.database.base import Base
from app.database.seed import seed_initial_data
from app.database.session import async_session_factory
# Ensure all models are imported so their metadata is registered on Base
import app.models  # noqa: F401


async def init_database(engine: AsyncEngine) -> None:
    """Create all relational tables and execute initial seed if empty."""
    try:
        logger.info("Initializing relational database schema...")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        logger.info("Relational schema verified and created.")

        async with async_session_factory() as session:
            await seed_initial_data(session)
    except Exception as exc:
        logger.warning(f"Database initialization deferred (database may still be starting): {exc}")

