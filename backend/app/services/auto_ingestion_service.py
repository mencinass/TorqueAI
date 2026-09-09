from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.database.session import async_session_factory
from app.models.document import TechnicalDocument
from app.rag.ingestion_pipeline import IngestionPipeline, JobStatus, JobTracker
from app.rag.qdrant_manager import QdrantManager

logger = get_logger(__name__)


async def ingest_local_documents(tracker: JobTracker, pipeline: IngestionPipeline) -> None:
    """Ingest seeded local manuals once when the vector collection is empty."""
    try:
        await _ingest_local_documents(tracker, pipeline)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("automatic_ingestion_failed")


async def _ingest_local_documents(tracker: JobTracker, pipeline: IngestionPipeline) -> None:
    if not settings.AUTO_INGEST_ENABLED:
        logger.info("automatic_ingestion_disabled")
        return

    qdrant = QdrantManager()
    await qdrant.ensure_collection()
    collection = await qdrant.collection_info()
    if collection["points_count"] > 0 and not settings.AUTO_INGEST_FORCE:
        logger.info(
            "automatic_ingestion_skipped",
            extra={"points_count": collection["points_count"]},
        )
        return

    async with async_session_factory() as session:
        result = await session.execute(
            select(TechnicalDocument).order_by(TechnicalDocument.id)
        )
        documents = list(result.scalars().all())

    logger.info("automatic_ingestion_started", extra={"documents": len(documents)})
    for document in documents:
        if not Path(document.file_path).is_file():
            logger.warning(
                "automatic_ingestion_file_missing",
                extra={"document_id": document.id, "file_path": document.file_path},
            )
            continue

        job_id = await tracker.create(document_id=document.id)
        metadata: dict[str, Any] = {
            "document_id": document.id,
            "document_title": document.title,
            "document_type": document.document_type,
            "system": document.system,
            "generation_code": document.generation.code if document.generation else None,
            "engine_code": document.engine.code if document.engine else None,
        }
        job = await pipeline.run(
            job_id=job_id,
            document_id=document.id,
            pdf_path=document.file_path,
            document_metadata=metadata,
        )
        if job.status == JobStatus.FAILED:
            logger.error(
                "automatic_ingestion_document_failed",
                extra={"document_id": document.id, "error": job.error},
            )
        else:
            logger.info(
                "automatic_ingestion_document_complete",
                extra={"document_id": document.id, "points": job.points_upserted},
            )
        await asyncio.sleep(0)

    logger.info("automatic_ingestion_finished")
