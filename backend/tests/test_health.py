from unittest.mock import patch
import pytest
import httpx


@pytest.mark.asyncio
async def test_health_check_healthy(async_client: httpx.AsyncClient):
    """Verify health check returns HTTP 200 when database and Qdrant are operational."""
    mock_db = {"status": "connected", "latency_ms": 1.25, "database": "automotive_db"}
    mock_qdrant = {"status": "connected", "latency_ms": 2.10, "collections_count": 0}

    with patch("app.api.v1.endpoints.health.check_database_health", return_value=mock_db), \
         patch("app.api.v1.endpoints.health.check_qdrant_health", return_value=mock_qdrant):

        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["project"] == "Automotive AI Agent"
        assert data["services"]["database"]["status"] == "connected"
        assert data["services"]["vector_db"]["status"] == "connected"


@pytest.mark.asyncio
async def test_health_check_database_failure(async_client: httpx.AsyncClient):
    """Verify health check returns HTTP 503 when the relational database is unreachable."""
    mock_db = {"status": "disconnected", "latency_ms": 50.0, "error": "Connection refused"}
    mock_qdrant = {"status": "connected", "latency_ms": 1.5, "collections_count": 0}

    with patch("app.api.v1.endpoints.health.check_database_health", return_value=mock_db), \
         patch("app.api.v1.endpoints.health.check_qdrant_health", return_value=mock_qdrant):

        response = await async_client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["database"]["status"] == "disconnected"
        assert data["services"]["vector_db"]["status"] == "connected"


@pytest.mark.asyncio
async def test_health_check_qdrant_failure(async_client: httpx.AsyncClient):
    """Verify health check returns HTTP 503 when Qdrant vector database is unreachable."""
    mock_db = {"status": "connected", "latency_ms": 1.1, "database": "automotive_db"}
    mock_qdrant = {"status": "disconnected", "latency_ms": 100.0, "error": "Timeout connecting to Qdrant"}

    with patch("app.api.v1.endpoints.health.check_database_health", return_value=mock_db), \
         patch("app.api.v1.endpoints.health.check_qdrant_health", return_value=mock_qdrant):

        response = await async_client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["database"]["status"] == "connected"
        assert data["services"]["vector_db"]["status"] == "disconnected"


@pytest.mark.asyncio
async def test_v1_health_parity(async_client: httpx.AsyncClient):
    """Verify that /api/v1/health and /health provide the exact same contract."""
    mock_db = {"status": "connected", "latency_ms": 0.8, "database": "automotive_db"}
    mock_qdrant = {"status": "connected", "latency_ms": 0.9, "collections_count": 1}

    with patch("app.api.v1.endpoints.health.check_database_health", return_value=mock_db), \
         patch("app.api.v1.endpoints.health.check_qdrant_health", return_value=mock_qdrant):

        res_root = await async_client.get("/health")
        res_v1 = await async_client.get("/api/v1/health")

        assert res_root.status_code == res_v1.status_code == 200
        assert res_root.json()["status"] == res_v1.json()["status"] == "healthy"

