from datetime import datetime, timezone
from unittest.mock import patch
import pytest
import httpx
from app.models.vehicle import Brand, Engine, Generation, Model, Vehicle
from app.schemas.vehicle import VehicleDetailResponse


@pytest.mark.asyncio
async def test_list_brands_empty_and_populated(async_client: httpx.AsyncClient):
    """Test GET /api/v1/vehicles/brands returns list of brands."""
    now = datetime.now(timezone.utc)
    mock_brands = [
        Brand(id=1, name="MINI", country="United Kingdom", created_at=now, updated_at=now),
        Brand(id=2, name="Fiat", country="Italy", created_at=now, updated_at=now),
    ]

    with patch("app.services.vehicle_service.VehicleService.get_brands", return_value=mock_brands):
        response = await async_client.get("/api/v1/vehicles/brands")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "MINI"
        assert data[1]["name"] == "Fiat"


@pytest.mark.asyncio
async def test_create_brand(async_client: httpx.AsyncClient):
    """Test POST /api/v1/vehicles/brands creates a brand."""
    now = datetime.now(timezone.utc)
    created_brand = Brand(id=3, name="BMW", country="Germany", created_at=now, updated_at=now)

    with patch("app.services.vehicle_service.VehicleService.create_brand", return_value=created_brand):
        response = await async_client.post(
            "/api/v1/vehicles/brands",
            json={"name": "BMW", "country": "Germany"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 3
        assert data["name"] == "BMW"


@pytest.mark.asyncio
async def test_get_vehicle_detail_found(async_client: httpx.AsyncClient):
    """Test GET /api/v1/vehicles/{id} returns rich vehicle context."""
    mock_detail = VehicleDetailResponse(
        id=1,
        brand="MINI",
        model="Cooper",
        generation="R56",
        generation_name="Second Generation (Hatchback)",
        year_start=2007,
        year_end=2013,
        engine_code="N16",
        displacement_l=1.6,
        fuel_type="petrol",
        power_hp=120,
        transmission="Manual 6-speed",
        trim_level="Cooper",
    )

    with patch("app.services.vehicle_service.VehicleService.get_vehicle_detail", return_value=mock_detail):
        response = await async_client.get("/api/v1/vehicles/1")
        assert response.status_code == 200
        data = response.json()
        assert data["brand"] == "MINI"
        assert data["generation"] == "R56"
        assert data["engine_code"] == "N16"


@pytest.mark.asyncio
async def test_get_vehicle_detail_not_found(async_client: httpx.AsyncClient):
    """Test GET /api/v1/vehicles/{id} returns 404 when ID does not exist."""
    with patch("app.services.vehicle_service.VehicleService.get_vehicle_detail", return_value=None):
        response = await async_client.get("/api/v1/vehicles/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_picker_options(async_client: httpx.AsyncClient):
    """Test GET /api/v1/vehicles/picker returns generations and systems."""
    mock_opts = {
        "generations": [
            {"code": "R56", "name": "Second Generation", "brand": "MINI", "model": "Cooper"},
            {"code": "EJ", "name": "Sixth Generation", "brand": "Honda", "model": "Civic"},
        ],
        "systems": ["engine", "general"],
    }
    with patch("app.services.vehicle_service.VehicleService.get_picker_options", return_value=mock_opts):
        response = await async_client.get("/api/v1/vehicles/picker")
        assert response.status_code == 200
        data = response.json()
        assert len(data["generations"]) == 2
        assert data["generations"][1]["code"] == "EJ"
        assert "engine" in data["systems"]

