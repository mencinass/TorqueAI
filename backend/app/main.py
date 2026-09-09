from contextlib import asynccontextmanager
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.api.v1.endpoints.health import health_check
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.logging import get_logger
from app.database.init_db import init_database
from app.database.session import engine
from app.services.auto_ingestion_service import ingest_local_documents
from app.rag.ingestion_pipeline import IngestionPipeline, JobTracker
from app.schemas.health import HealthCheckResponse
from app.services.qdrant_service import close_qdrant_client

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager handling startup and shutdown events."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    logger.info(f"Targeting Database Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    logger.info(f"Targeting Qdrant Host: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    # Initialize relational schema and seed initial vehicle catalog
    await init_database(engine)
    # Initialize in-memory ingestion job tracker and pipeline (shared via app.state)
    app.state.job_tracker = JobTracker()
    app.state.ingestion_pipeline = IngestionPipeline(tracker=app.state.job_tracker)
    app.state.auto_ingestion_task = asyncio.create_task(
        ingest_local_documents(app.state.job_tracker, app.state.ingestion_pipeline)
    )
    yield
    logger.info("Initiating graceful shutdown sequence...")
    app.state.auto_ingestion_task.cancel()
    await asyncio.gather(app.state.auto_ingestion_task, return_exceptions=True)
    # Dispose SQLAlchemy connection pool
    await engine.dispose()
    # Close Qdrant HTTP/gRPC client
    await close_qdrant_client()
    logger.info("Application shutdown complete.")


def create_application() -> FastAPI:
    """Factory creating and configuring the core FastAPI instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Automotive AI Agent - Specialized AI technical assistant "
            "for automotive diagnostics, service manual retrieval, and workshop procedures."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # Cross-Origin Resource Sharing (CORS) setup
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register domain exception handlers
    setup_exception_handlers(app)

    # Route /health available directly at root level for container probes
    app.add_api_route(
        "/health",
        health_check,
        methods=["GET"],
        response_model=HealthCheckResponse,
        tags=["System Health"],
        summary="Root Health Check Probe",
    )

    # Register API v1 versioned router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()

