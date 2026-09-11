from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ServiceHealthInfo(BaseModel):
    """Detailed health status of an individual dependency."""

    status: str = Field(
        ...,
        description="Status of the dependency: 'connected' or 'disconnected'",
        examples=["connected"],
    )
    latency_ms: float = Field(
        ...,
        description="Network round-trip latency in milliseconds",
        examples=[2.45],
    )
    error: Optional[str] = Field(
        default=None,
        description="Error description if connection failed",
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional auxiliary metrics or metadata",
    )


class HealthCheckResponse(BaseModel):
    """System-wide operational health status payload."""

    status: str = Field(
        ...,
        description="Overall system status: 'healthy' or 'unhealthy'",
        examples=["healthy"],
    )
    project: str = Field(..., examples=["TorqueAI"])
    version: str = Field(..., examples=["0.1.0"])
    environment: str = Field(..., examples=["development"])
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the health check evaluation",
    )
    services: Dict[str, Any] = Field(
        ...,
        description="Dictionary mapping each service (database, vector_db) to its health info",
    )

