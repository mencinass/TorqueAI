import time
from typing import Any, Dict
from sqlalchemy import text
from app.core.logging import logger
from app.database.session import engine


async def check_database_health() -> Dict[str, Any]:
    """Test PostgreSQL database connectivity and measure response latency."""
    start_time = time.perf_counter()
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            scalar = result.scalar()
            if scalar != 1:
                raise ValueError(f"Unexpected query result: {scalar}")

        latency_ms = (time.perf_counter() - start_time) * 1000
        return {
            "status": "connected",
            "latency_ms": round(latency_ms, 2),
            "database": engine.url.database,
        }
    except Exception as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"PostgreSQL health check failed: {exc}")
        return {
            "status": "disconnected",
            "latency_ms": round(latency_ms, 2),
            "error": str(exc),
        }

