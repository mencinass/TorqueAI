from __future__ import annotations

import asyncio
import hashlib
import subprocess
from pathlib import Path
from typing import Any, List

from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.database.session import async_session_factory
from app.models.document import TechnicalDocument
from app.rag.ingestion_pipeline import IngestionPipeline, JobStatus, JobTracker
from app.rag.qdrant_manager import QdrantManager

logger = get_logger(__name__)

# Relative to the backend working directory (``/app`` in the container).
_GENERAL_DIR_CANDIDATES = [
    Path("service_guide/general"),
    Path("../service_guide/general"),
    Path("/app/service_guide/general"),
]

# First-pages text probe: scanned PDFs (image-only) yield no extractable text
# and would produce 0 chunks (same lesson as the MINI R53 manual).
_PROBE_PAGES = 3
_PROBE_MIN_CHARS = 50


def _resolve_general_dir() -> Path:
    for candidate in _GENERAL_DIR_CANDIDATES:
        if candidate.is_dir():
            return candidate
    return _GENERAL_DIR_CANDIDATES[0]


def _repo_relative_path(general_dir: Path, pdf_path: Path) -> str:
    """Return the repo-relative path (``service_guide/general/<file>.pdf``).

    The seed and the API store paths relative to the repository root (and the
    compose mounts ``./service_guide`` at ``/app/service_guide``), so we derive
    the relative path from the resolved directory rather than trusting the CWD.
    """
    try:
        relative = pdf_path.relative_to(general_dir)
    except ValueError:
        relative = Path(pdf_path.name)
    return f"service_guide/general/{relative.as_posix()}"


def _md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _probe_has_text_layer(path: Path) -> bool:
    """Return True when the first pages expose extractable text (pdftotext)."""
    try:
        result = subprocess.run(
            [
                "pdftotext",
                "-f", "1",
                "-l", str(_PROBE_PAGES),
                str(path),
                "-",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        # If poppler is unavailable, do not block registration.
        return True
    return len((result.stdout or "").strip()) >= _PROBE_MIN_CHARS


async def register_general_documents() -> List[TechnicalDocument]:
    """Idempotently register every unique general mechanics PDF.

    Files are deduplicated by content hash (MD5) before registration, so the
    same manual under two filenames is indexed only once.  PDFs without a
    text layer (scanned/image-only) are skipped with a warning: they would
    produce zero chunks in the vector collection.
    """
    general_dir = _resolve_general_dir()
    if not general_dir.is_dir():
        logger.warning("general_documents_dir_missing", extra={"dir": str(general_dir)})
        return []

    async with async_session_factory() as session:
        result = await session.execute(
            select(TechnicalDocument).where(
                TechnicalDocument.system == settings.GENERAL_MECHANICS_COLLECTION
            )
        )
        existing = {doc.file_path: doc for doc in result.scalars().all()}

        seen_hashes: set[str] = set()
        registered: List[TechnicalDocument] = []
        for pdf_path in sorted(general_dir.glob("*.pdf")):
            relative = _repo_relative_path(general_dir, pdf_path)

            if relative in existing:
                registered.append(existing[relative])
                continue

            file_hash = _md5_file(pdf_path)
            if file_hash in seen_hashes:
                logger.info(
                    "general_document_duplicate_skipped",
                    extra={"file": pdf_path.name},
                )
                continue
            seen_hashes.add(file_hash)

            if not _probe_has_text_layer(pdf_path):
                logger.warning(
                    "general_document_no_text_layer",
                    extra={"file": pdf_path.name},
                )
                continue

            document = TechnicalDocument(
                title=pdf_path.stem.replace("-", " ").replace("_", " ")[:255],
                file_path=relative,
                file_size_bytes=pdf_path.stat().st_size,
                document_type="general_mechanics",
                system=settings.GENERAL_MECHANICS_COLLECTION,
                language="pt",
            )
            session.add(document)
            existing[relative] = document
            registered.append(document)
            logger.info(
                "general_document_registered",
                extra={"file": pdf_path.name, "size_bytes": pdf_path.stat().st_size},
            )

        await session.commit()

    # Re-fetch committed rows so callers get populated primary keys.
    async with async_session_factory() as session:
        result = await session.execute(
            select(TechnicalDocument).where(
                TechnicalDocument.system == settings.GENERAL_MECHANICS_COLLECTION
            ).order_by(TechnicalDocument.id)
        )
        return list(result.scalars().all())


async def ingest_general_documents(tracker: JobTracker, pipeline: IngestionPipeline) -> None:
    """Ingest general mechanics PDFs once when the general collection is empty."""
    try:
        await _ingest_general_documents(tracker, pipeline)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("general_ingestion_failed")


async def _ingest_general_documents(tracker: JobTracker, pipeline: IngestionPipeline) -> None:
    if not settings.AUTO_INGEST_ENABLED:
        logger.info("general_ingestion_disabled")
        return

    qdrant = QdrantManager(collection=settings.GENERAL_MECHANICS_COLLECTION)
    await qdrant.ensure_collection()
    collection = await qdrant.collection_info()
    if collection["points_count"] > 0 and not settings.AUTO_INGEST_FORCE:
        logger.info(
            "general_ingestion_skipped",
            extra={"points_count": collection["points_count"]},
        )
        return

    documents = await register_general_documents()
    logger.info("general_ingestion_started", extra={"documents": len(documents)})

    for document in documents:
        if not Path(document.file_path).is_file():
            logger.warning(
                "general_ingestion_file_missing",
                extra={"document_id": document.id, "file_path": document.file_path},
            )
            continue

        job_id = await tracker.create(document_id=document.id)
        metadata: dict[str, Any] = {
            "document_id": document.id,
            "document_title": document.title,
            "document_type": document.document_type,
            "system": document.system,
            "generation_code": None,
            "engine_code": None,
        }
        job = await pipeline.run(
            job_id=job_id,
            document_id=document.id,
            pdf_path=document.file_path,
            document_metadata=metadata,
        )
        if job.status == JobStatus.FAILED:
            logger.error(
                "general_ingestion_document_failed",
                extra={"document_id": document.id, "error": job.error},
            )
        else:
            logger.info(
                "general_ingestion_document_complete",
                extra={"document_id": document.id, "points": job.points_upserted},
            )
        await asyncio.sleep(0)

    logger.info("general_ingestion_finished")
