import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
from app.core.config import settings
from app.schemas.health import HealthCheckResponse
from app.services.db_service import check_database_health
from app.services.qdrant_service import check_qdrant_health

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Comprehensive Health Check",
    description="Inspects real-time operational connectivity to PostgreSQL and Qdrant vector database.",
)
async def health_check(response: Response) -> HealthCheckResponse:
    """Execute concurrent health checks against all connected infrastructure dependencies."""
    # Execute health checks in parallel
    db_health, qdrant_health = await asyncio.gather(
        check_database_health(),
        check_qdrant_health(),
        return_exceptions=False,
    )

    is_db_ok = db_health.get("status") == "connected"
    is_qdrant_ok = qdrant_health.get("status") == "connected"
    is_healthy = is_db_ok and is_qdrant_ok

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthCheckResponse(
        status="healthy" if is_healthy else "unhealthy",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
        services={
            "database": db_health,
            "vector_db": qdrant_health,
        },
    )

