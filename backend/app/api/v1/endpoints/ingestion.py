"""REST endpoints for the document ingestion pipeline.

Routes:
    POST /api/v1/ingestion/start        — start a background ingestion job
    GET  /api/v1/ingestion/jobs/{id}    — poll job status
    GET  /api/v1/ingestion/jobs         — list all jobs

The :class:`JobTracker` and :class:`IngestionPipeline` instances are stored
on ``app.state`` so they are shared across requests without global variables.
They are initialised in ``main.py`` lifespan.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.document import TechnicalDocument

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic I/O schemas
# ---------------------------------------------------------------------------


class IngestionStartRequest(BaseModel):
    """Payload for starting a new ingestion job."""

    document_id: int = Field(..., gt=0, description="TechnicalDocument primary key.")
    pdf_path: Optional[str] = Field(
        None,
        description="Explicit path to PDF.  Auto-resolved from document_id if omitted.",
    )
    max_pages: Optional[int] = Field(
        None,
        gt=0,
        description="Upper page limit (None = all pages).",
    )
    chunk_size: int = Field(1000, gt=0, description="Target chunk size in chars.")
    chunk_overlap: int = Field(150, ge=0, description="Chunk overlap in chars.")
    document_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Extra metadata passed to the chunker: document_title, document_type, "
            "system, generation_code, engine_code."
        ),
    )


class IngestionStartResponse(BaseModel):
    """Returned immediately after a job is accepted."""

    job_id: str
    document_id: int
    status: str = "pending"
    message: str = "Ingestion job accepted."


class JobStatusResponse(BaseModel):
    """Full job status as returned by the tracker."""

    job_id: str
    document_id: int
    status: str
    total_pages: int
    pages_processed: int
    chunks_created: int
    points_upserted: int
    error: Optional[str]
    created_at: str
    started_at: Optional[str]
    finished_at: Optional[str]


# ---------------------------------------------------------------------------
# Background task helper
# ---------------------------------------------------------------------------


async def _run_ingestion(
    request: Request,
    job_id: str,
    document_id: int,
    pdf_path: Optional[str],
    max_pages: Optional[int],
    document_metadata: Optional[dict],
) -> None:
    """Fire-and-forget coroutine launched by FastAPI BackgroundTasks."""
    pipeline = request.app.state.ingestion_pipeline
    await pipeline.run(
        job_id=job_id,
        document_id=document_id,
        pdf_path=pdf_path,
        max_pages=max_pages,
        document_metadata=document_metadata,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/start",
    response_model=IngestionStartResponse,
    status_code=202,
    summary="Start a document ingestion job",
    description=(
        "Enqueues a background ingestion job for the specified TechnicalDocument. "
        "Returns immediately with a ``job_id`` that can be polled via ``GET /jobs/{job_id}``."
    ),
)
async def start_ingestion(
    payload: IngestionStartRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> IngestionStartResponse:
    tracker = request.app.state.job_tracker

    # Resolve document metadata from the catalog when the client omits it,
    # so chunks carry correct title/system/generation/engine like auto-ingestion.
    document_metadata = payload.document_metadata
    if document_metadata is None:
        result = await db.execute(
            select(TechnicalDocument).where(TechnicalDocument.id == payload.document_id)
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            raise HTTPException(
                status_code=404,
                detail=f"Technical document with ID {payload.document_id} not found",
            )
        document_metadata = {
            "document_id": doc.id,
            "document_title": doc.title,
            "document_type": doc.document_type,
            "system": doc.system,
            "generation_code": doc.generation.code if doc.generation else None,
            "engine_code": doc.engine.code if doc.engine else None,
        }

    job_id = await tracker.create(document_id=payload.document_id)

    background_tasks.add_task(
        _run_ingestion,
        request,
        job_id,
        payload.document_id,
        payload.pdf_path,
        payload.max_pages,
        document_metadata,
    )

    return IngestionStartResponse(
        job_id=job_id,
        document_id=payload.document_id,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get ingestion job status",
)
async def get_job(job_id: str, request: Request) -> JobStatusResponse:
    tracker = request.app.state.job_tracker
    job = await tracker.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found.")
    return JobStatusResponse(**job.to_dict())


@router.get(
    "/jobs",
    response_model=List[JobStatusResponse],
    summary="List all ingestion jobs",
)
async def list_jobs(request: Request) -> List[JobStatusResponse]:
    tracker = request.app.state.job_tracker
    jobs = await tracker.list_all()
    return [JobStatusResponse(**j.to_dict()) for j in jobs]
