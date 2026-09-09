"""CLI ingestion tool for the automotive RAG pipeline.

Run directly with::

    python -m app.rag.cli --document-id 1 --max-pages 20

Or use the helper script in ``run.ps1`` / ``Makefile``::

    ./run.ps1 ingest --document-id 1

The command starts an ingestion job synchronously (blocks until done) and
prints a progress summary to stdout.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.core.logging import get_logger
from app.rag.ingestion_pipeline import IngestionPipeline, JobStatus, JobTracker

logger = get_logger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.rag.cli",
        description="Ingest a technical PDF into the Qdrant vector database.",
    )
    parser.add_argument(
        "--document-id",
        type=int,
        required=True,
        help="ID of the TechnicalDocument record in PostgreSQL.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to ingest (default: all pages).",
    )
    parser.add_argument(
        "--pdf-path",
        type=str,
        default=None,
        help="Explicit path to the PDF file.  If omitted, auto-resolved from document_id.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Target chunk size in characters (default: 1000).",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=150,
        help="Overlap between consecutive chunks in characters (default: 150).",
    )
    return parser


async def _run(args: argparse.Namespace) -> int:
    """Execute the ingestion job and return an exit code."""
    tracker = JobTracker()
    pipeline = IngestionPipeline(
        tracker=tracker,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    job_id = await tracker.create(document_id=args.document_id)
    print(f"\n🚀 Ingestion started — job_id: {job_id}")
    print(f"   document_id : {args.document_id}")
    print(f"   max_pages   : {args.max_pages or 'all'}")
    print(f"   pdf_path    : {args.pdf_path or 'auto-resolved'}")
    print()

    job = await pipeline.run(
        job_id=job_id,
        document_id=args.document_id,
        pdf_path=args.pdf_path,
        max_pages=args.max_pages,
    )

    print("─" * 60)
    print(f"Status          : {job.status.value.upper()}")
    print(f"Pages processed : {job.pages_processed} / {job.total_pages}")
    print(f"Chunks created  : {job.chunks_created}")
    print(f"Points upserted : {job.points_upserted}")
    if job.error:
        print(f"Error           : {job.error}")
    print("─" * 60)

    if job.status == JobStatus.DONE:
        print("✅ Ingestion complete!")
        return 0
    else:
        print("❌ Ingestion failed — see error above.")
        return 1


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    sys.exit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
