import time
from typing import Any, Dict
from qdrant_client import AsyncQdrantClient
from app.core.config import settings
from app.core.logging import logger

_qdrant_client: AsyncQdrantClient | None = None


def get_qdrant_client() -> AsyncQdrantClient:
    """Retrieve or initialize singleton instance of AsyncQdrantClient."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY,
            timeout=5.0,
        )
    return _qdrant_client


async def close_qdrant_client() -> None:
    """Close active Qdrant client connections on shutdown."""
    global _qdrant_client
    if _qdrant_client is not None:
        try:
            await _qdrant_client.close()
        except Exception as exc:
            logger.warning(f"Error closing Qdrant client: {exc}")
        finally:
            _qdrant_client = None


async def check_qdrant_health() -> Dict[str, Any]:
    """Test Qdrant vector database connectivity and measure response latency."""
    start_time = time.perf_counter()
    try:
        client = get_qdrant_client()
        collections_response = await client.get_collections()
        latency_ms = (time.perf_counter() - start_time) * 1000
        return {
            "status": "connected",
            "latency_ms": round(latency_ms, 2),
            "collections_count": len(collections_response.collections),
        }
    except Exception as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"Qdrant health check failed: {exc}")
        return {
            "status": "disconnected",
            "latency_ms": round(latency_ms, 2),
            "error": str(exc),
        }

