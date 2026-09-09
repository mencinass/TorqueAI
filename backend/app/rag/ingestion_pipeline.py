"""Ingestion pipeline orchestrator and in-memory job tracker.

The pipeline orchestrates the full flow::

    PDF → PDFExtractor → AutomotiveChunker → EmbeddingProvider → QdrantManager

:class:`JobTracker` holds job state in memory (no persistence).
:class:`IngestionPipeline` is the entry point for both the CLI and REST API.

Usage::

    tracker = JobTracker()
    pipeline = IngestionPipeline(tracker=tracker)

    job_id = tracker.create(document_id=1)
    await pipeline.run(job_id=job_id, document_id=1, max_pages=50)
    info = tracker.get(job_id)
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from app.core.logging import get_logger
from app.rag.chunker import AutomotiveChunker, DocumentChunk
from app.rag.embeddings import BaseEmbeddingProvider, get_embedding_provider
from app.rag.pdf_extractor import PDFExtractor
from app.rag.qdrant_manager import QdrantManager

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Job state
# ---------------------------------------------------------------------------


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class JobInfo:
    """Runtime state for a single ingestion job."""

    job_id: str
    document_id: int
    status: JobStatus = JobStatus.PENDING
    total_pages: int = 0
    pages_processed: int = 0
    chunks_created: int = 0
    points_upserted: int = 0
    error: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "document_id": self.document_id,
            "status": self.status.value,
            "total_pages": self.total_pages,
            "pages_processed": self.pages_processed,
            "chunks_created": self.chunks_created,
            "points_upserted": self.points_upserted,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


# ---------------------------------------------------------------------------
# Job tracker (in-memory singleton)
# ---------------------------------------------------------------------------


class JobTracker:
    """Thread-safe in-memory store for :class:`JobInfo` objects.

    Designed for a single-process FastAPI app.  If multiple workers are
    needed, replace with a Redis-backed implementation.
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, JobInfo] = {}
        self._lock = asyncio.Lock()

    async def create(self, document_id: int) -> str:
        """Create and store a new job, returning its job_id."""
        job_id = str(uuid.uuid4())
        async with self._lock:
            self._jobs[job_id] = JobInfo(job_id=job_id, document_id=document_id)
        logger.info("job_created", extra={"job_id": job_id, "document_id": document_id})
        return job_id

    async def get(self, job_id: str) -> Optional[JobInfo]:
        async with self._lock:
            return self._jobs.get(job_id)

    async def list_all(self) -> List[JobInfo]:
        async with self._lock:
            return list(self._jobs.values())

    async def _update(self, job_id: str, **kwargs) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for key, value in kwargs.items():
                setattr(job, key, value)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class IngestionPipeline:
    """Orchestrate the full PDF-to-Qdrant ingestion flow.

    Parameters
    ----------
    tracker:
        :class:`JobTracker` instance shared with the REST layer.
    embedding_provider:
        Override the default embedding provider (useful for tests).
    qdrant_manager:
        Override the default Qdrant manager (useful for tests).
    chunk_size:
        Target character count per chunk (passed to :class:`AutomotiveChunker`).
    chunk_overlap:
        Character overlap between consecutive chunks.
    embed_batch_size:
        How many chunks to embed in one provider call.
    upsert_batch_size:
        How many points per Qdrant upsert request.
    """

    def __init__(
        self,
        tracker: JobTracker,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        qdrant_manager: Optional[QdrantManager] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        embed_batch_size: int = 32,
        upsert_batch_size: int = 64,
    ) -> None:
        self._tracker = tracker
        self._embedder: BaseEmbeddingProvider = embedding_provider or get_embedding_provider()
        self._qdrant: QdrantManager = qdrant_manager or QdrantManager()
        self._chunker = AutomotiveChunker(chunk_size=chunk_size, overlap=chunk_overlap)
        self._embed_batch_size = embed_batch_size
        self._upsert_batch_size = upsert_batch_size
        # Serialize all runs so only one document is ingested at a time,
        # regardless of how many jobs are triggered concurrently.
        self._run_lock = asyncio.Lock()

    async def run(
        self,
        job_id: str,
        document_id: int,
        pdf_path: Optional[str] = None,
        max_pages: Optional[int] = None,
        document_metadata: Optional[dict] = None,
    ) -> JobInfo:
        """Execute the ingestion and update the job tracker throughout.

        Args:
            job_id: Pre-created job ID from :meth:`JobTracker.create`.
            document_id: Database ID of the :class:`TechnicalDocument`.
            pdf_path: Absolute or relative path to the PDF file.  If *None*,
                :class:`PDFExtractor` will attempt to auto-resolve.
            max_pages: Upper limit on pages to ingest (``None`` = all pages).
            document_metadata: Optional dict passed to the chunker as document
                context (``document_title``, ``document_type``, ``system``,
                ``generation_code``, ``engine_code``).

        Returns:
            The final :class:`JobInfo` with status ``done`` or ``failed``.
        """
        meta = document_metadata or {}
        meta.setdefault("document_id", document_id)

        if self._run_lock.locked():
            logger.info("ingestion_queued", extra={"job_id": job_id, "document_id": document_id})
        async with self._run_lock:
            return await self._run_locked(job_id, document_id, meta, pdf_path, max_pages)

    async def _run_locked(
        self,
        job_id: str,
        document_id: int,
        meta: dict,
        pdf_path: Optional[str],
        max_pages: Optional[int],
    ) -> JobInfo:
        await self._tracker._update(
            job_id,
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        try:
            await self._qdrant.ensure_collection()

            extractor = PDFExtractor(document_id=document_id, pdf_path=pdf_path)

            # Count total pages first (cheap)
            total_pages = await asyncio.to_thread(extractor.get_total_pages)
            await self._tracker._update(job_id, total_pages=total_pages)

            pending_chunks: List[DocumentChunk] = []
            pages_done = 0
            total_chunks = 0
            total_upserted = 0

            async for page in extractor.stream_pages(max_pages=max_pages):
                new_chunks = self._chunker.chunk_page(
                    page_text=page["text"],
                    page_number=page["page_number"],
                    section_title=page["section_title"],
                    document_metadata=meta,
                )
                pending_chunks.extend(new_chunks)
                total_chunks += len(new_chunks)
                pages_done += 1

                # Flush when we have a full embed batch
                if len(pending_chunks) >= self._embed_batch_size:
                    upserted = await self._flush_chunks(pending_chunks)
                    total_upserted += upserted
                    pending_chunks = []

                await self._tracker._update(
                    job_id,
                    pages_processed=pages_done,
                    chunks_created=total_chunks,
                    points_upserted=total_upserted,
                )

            # Flush remainder
            if pending_chunks:
                upserted = await self._flush_chunks(pending_chunks)
                total_upserted += upserted

            finished_at = datetime.now(timezone.utc).isoformat()
            await self._tracker._update(
                job_id,
                status=JobStatus.DONE,
                pages_processed=pages_done,
                chunks_created=total_chunks,
                points_upserted=total_upserted,
                finished_at=finished_at,
            )
            logger.info(
                "ingestion_complete",
                extra={
                    "job_id": job_id,
                    "document_id": document_id,
                    "pages": pages_done,
                    "chunks": total_chunks,
                    "points": total_upserted,
                },
            )

        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error(
                "ingestion_failed",
                extra={"job_id": job_id, "document_id": document_id, "error": error_msg},
            )
            await self._tracker._update(
                job_id,
                status=JobStatus.FAILED,
                error=error_msg,
                finished_at=datetime.now(timezone.utc).isoformat(),
            )

        return await self._tracker.get(job_id)  # type: ignore[return-value]

    async def _flush_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Embed a batch of chunks and upsert them to Qdrant.

        Returns total points upserted.
        """
        texts = [c.text for c in chunks]
        embeddings = await self._embedder.embed(texts)
        return await self._qdrant.batch_upsert_chunks(
            chunks,
            embeddings,
            batch_size=self._upsert_batch_size,
        )
