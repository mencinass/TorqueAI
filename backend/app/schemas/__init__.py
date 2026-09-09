"""Pydantic validation schemas."""

from app.schemas.document import DocumentCreate, DocumentResponse
from app.schemas.health import HealthCheckResponse, ServiceHealthInfo
from app.schemas.vehicle import (
    BrandCreate,
    BrandResponse,
    EngineCreate,
    EngineResponse,
    GenerationCreate,
    GenerationResponse,
    ModelCreate,
    ModelResponse,
    VehicleCreate,
    VehicleDetailResponse,
    VehicleResponse,
)

__all__ = [
    "HealthCheckResponse",
    "ServiceHealthInfo",
    "BrandCreate",
    "BrandResponse",
    "ModelCreate",
    "ModelResponse",
    "GenerationCreate",
    "GenerationResponse",
    "EngineCreate",
    "EngineResponse",
    "VehicleCreate",
    "VehicleResponse",
    "VehicleDetailResponse",
    "DocumentCreate",
    "DocumentResponse",
]
