from datetime import datetime, timezone
from unittest.mock import patch
import pytest
import httpx
from app.schemas.document import DocumentResponse


@pytest.mark.asyncio
async def test_list_documents_with_generation_filter(async_client: httpx.AsyncClient):
    """Test GET /api/v1/documents returns documents filtered by generation."""
    now = datetime.now(timezone.utc)
    mock_docs = [
        DocumentResponse(
            id=1,
            title="MINI Cooper R56 Service Manual (2007-2013)",
            file_path="service_guide/MINI_R56/mini_R56_service.pdf",
            file_size_bytes=588153153,
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=1,
            engine_id=1,
            generation_code="R56",
            engine_code="N16",
            created_at=now,
            updated_at=now,
        )
    ]

    with patch("app.services.document_service.DocumentService.get_documents", return_value=mock_docs):
        response = await async_client.get("/api/v1/documents?generation=R56")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["generation_code"] == "R56"
        assert "MINI Cooper R56" in data[0]["title"]


@pytest.mark.asyncio
async def test_get_document_by_id_not_found(async_client: httpx.AsyncClient):
    """Test GET /api/v1/documents/{id} returns 404 when ID does not exist."""
    with patch("app.services.document_service.DocumentService.get_document_by_id", return_value=None):
        response = await async_client.get("/api/v1/documents/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

