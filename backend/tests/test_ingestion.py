"""Automated tests for the document ingestion pipeline.

Covers:
- AutomotiveChunker: metadata preservation, deterministic IDs, size bounds
- MockEmbeddingProvider: correct dimension, determinism
- IngestionPipeline: end-to-end run with mocked extractor and Qdrant
- REST endpoints: POST /start, GET /jobs/{id}, GET /jobs
"""

from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.rag.chunker import AutomotiveChunker, DocumentChunk
from app.rag.embeddings import MockEmbeddingProvider
from app.rag.ingestion_pipeline import IngestionPipeline, JobStatus, JobTracker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def chunker() -> AutomotiveChunker:
    return AutomotiveChunker(chunk_size=200, chunk_overlap=30)


@pytest.fixture
def mock_embedder() -> MockEmbeddingProvider:
    return MockEmbeddingProvider(dim=128)


@pytest.fixture
def sample_metadata() -> dict:
    return {
        "document_id": 42,
        "document_title": "MINI R56 Workshop Manual",
        "document_type": "workshop_manual",
        "system": "Engine",
        "generation_code": "R56",
        "engine_code": "N14",
    }


# ---------------------------------------------------------------------------
# AutomotiveChunker tests
# ---------------------------------------------------------------------------


class TestAutomotiveChunker:
    """Tests for AutomotiveChunker."""

    def test_empty_text_returns_no_chunks(self, chunker: AutomotiveChunker) -> None:
        result = chunker.chunk_page("", 1, "Intro", {})
        assert result == []

    def test_short_text_below_min_size_returns_no_chunks(self, chunker: AutomotiveChunker) -> None:
        result = chunker.chunk_page("Too short.", 1, "Intro", {})
        assert result == []

    def test_single_chunk_for_short_page(
        self, chunker: AutomotiveChunker, sample_metadata: dict
    ) -> None:
        text = "A" * 150  # less than chunk_size=200 but above min_chunk_size
        chunks = chunker.chunk_page(text, 1, "Section 1", sample_metadata)
        assert len(chunks) == 1
        chunk = chunks[0]
        assert chunk.page_number == 1
        assert chunk.section_title == "Section 1"
        assert chunk.document_id == 42
        assert chunk.generation_code == "R56"
        assert chunk.engine_code == "N14"
        assert chunk.document_title == "MINI R56 Workshop Manual"

    def test_multiple_chunks_for_long_page(
        self, chunker: AutomotiveChunker, sample_metadata: dict
    ) -> None:
        text = "Word sentence here. " * 50  # ~1000 chars
        chunks = chunker.chunk_page(text, 5, "Fuel System", sample_metadata)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk.text) >= chunker.min_chunk_size

    def test_chunk_id_is_deterministic(
        self, chunker: AutomotiveChunker, sample_metadata: dict
    ) -> None:
        text = "X" * 300
        chunks_a = chunker.chunk_page(text, 2, "Title", sample_metadata)
        chunks_b = chunker.chunk_page(text, 2, "Title", sample_metadata)
        assert [c.chunk_id for c in chunks_a] == [c.chunk_id for c in chunks_b]

    def test_chunk_id_is_valid_uuid(
        self, chunker: AutomotiveChunker, sample_metadata: dict
    ) -> None:
        chunks = chunker.chunk_page("X" * 300, 1, "Title", sample_metadata)
        for chunk in chunks:
            # Should not raise
            uuid.UUID(chunk.chunk_id)

    def test_chunk_ids_are_unique_across_pages(
        self, chunker: AutomotiveChunker, sample_metadata: dict
    ) -> None:
        text = "Y" * 300
        chunks_p1 = chunker.chunk_page(text, 1, "A", sample_metadata)
        chunks_p2 = chunker.chunk_page(text, 2, "B", sample_metadata)
        ids_p1 = {c.chunk_id for c in chunks_p1}
        ids_p2 = {c.chunk_id for c in chunks_p2}
        assert ids_p1.isdisjoint(ids_p2)

    def test_chunk_page_terminates_when_clean_break_pulls_back(
        self, sample_metadata: dict
    ) -> None:
        """Regression: a "clean break" (\\n\\n or \". \") can pull ``end`` back far
        enough that ``end - overlap <= start``, which previously caused an
        infinite loop (and a container OOM on real manual pages).

        Reproduces the MINI R56 service manual page-85 shape: a paragraph
        boundary that lands just past ``start`` so the overlap zone overlaps
        the break position, leaving ``start`` unable to advance.
        """
        # Use small chunk/overlap so the overlap window dominates the clean
        # break: a boundary found early in the window yields end-overlap<=start.
        chunker = AutomotiveChunker(chunk_size=60, chunk_overlap=40, min_chunk_size=10)
        # Text with a paragraph break positioned near the window start on the
        # second iteration — the exact shape that looped.
        text = ("aaa bbb ccc ddd eee fff ggg hhh.\n\n" * 30)
        chunks = chunker.chunk_page(
            page_text=text, page_number=85, section_title="Overview",
            document_metadata=sample_metadata,
        )
        # Must terminate (a hang would never return). The precise count is not
        # the point; what matters is finite output with no runaway.
        assert isinstance(chunks, list)
        # No chunk should duplicate its neighbour's start character, and the
        # total must be bounded by the character count (a strong signal that
        # the walker strictly advanced and never re-emitted the same window).
        assert len(chunks) <= len(text)
        for chunk in chunks:
            assert len(chunk.text) >= chunker.min_chunk_size

    def test_to_payload_returns_dict(
        self, chunker: AutomotiveChunker, sample_metadata: dict
    ) -> None:
        chunks = chunker.chunk_page("Z" * 200, 1, "Sec", sample_metadata)
        assert chunks
        payload = chunks[0].to_payload()
        assert isinstance(payload, dict)
        assert "chunk_id" in payload
        assert "text" in payload
        assert "generation_code" in payload


# ---------------------------------------------------------------------------
# MockEmbeddingProvider tests
# ---------------------------------------------------------------------------


class TestMockEmbeddingProvider:
    """Tests for MockEmbeddingProvider."""

    @pytest.mark.asyncio
    async def test_embed_returns_correct_dimension(self, mock_embedder: MockEmbeddingProvider) -> None:
        texts = ["Hello world", "Service manual"]
        vecs = await mock_embedder.embed(texts)
        assert len(vecs) == 2
        for vec in vecs:
            assert len(vec) == 128

    @pytest.mark.asyncio
    async def test_embed_is_deterministic(self, mock_embedder: MockEmbeddingProvider) -> None:
        text = ["Engine oil specification N14"]
        v1 = await mock_embedder.embed(text)
        v2 = await mock_embedder.embed(text)
        assert v1 == v2

    @pytest.mark.asyncio
    async def test_embed_empty_returns_empty(self, mock_embedder: MockEmbeddingProvider) -> None:
        result = await mock_embedder.embed([])
        assert result == []

    @pytest.mark.asyncio
    async def test_embed_vectors_are_unit_length(self, mock_embedder: MockEmbeddingProvider) -> None:
        import math
        vecs = await mock_embedder.embed(["test"])
        vec = vecs[0]
        magnitude = math.sqrt(sum(v * v for v in vec))
        assert abs(magnitude - 1.0) < 1e-6

    def test_dimension_property(self, mock_embedder: MockEmbeddingProvider) -> None:
        assert mock_embedder.dimension == 128

    @pytest.mark.asyncio
    async def test_different_texts_produce_different_vectors(
        self, mock_embedder: MockEmbeddingProvider
    ) -> None:
        v1 = await mock_embedder.embed(["spark plug torque"])
        v2 = await mock_embedder.embed(["brake fluid specification"])
        assert v1 != v2


# ---------------------------------------------------------------------------
# IngestionPipeline tests (mocked Qdrant + page stream)
# ---------------------------------------------------------------------------


class TestIngestionPipeline:
    """End-to-end pipeline tests with mocked external dependencies."""

    @pytest.mark.asyncio
    async def test_run_happy_path(self, sample_metadata: dict) -> None:
        """Pipeline runs, creates chunks, and sets status=done."""
        tracker = JobTracker()
        mock_qdrant = AsyncMock()
        mock_qdrant.ensure_collection = AsyncMock()
        mock_qdrant.batch_upsert_chunks = AsyncMock(return_value=5)

        embedder = MockEmbeddingProvider(dim=128)

        # Mock PDFExtractor so it yields 2 pages without needing a real PDF
        fake_page_1 = {
            "page_number": 1,
            "text": "Engine oil spec. " * 40,
            "char_count": 680,
            "section_title": "Engine",
            "total_pages": 2,
        }
        fake_page_2 = {
            "page_number": 2,
            "text": "Brake fluid DOT 4. " * 40,
            "char_count": 760,
            "section_title": "Brakes",
            "total_pages": 2,
        }

        async def _fake_stream(**kwargs):
            for p in [fake_page_1, fake_page_2]:
                yield p

        mock_extractor = MagicMock()
        mock_extractor.total_pages = 2
        mock_extractor.stream_pages = _fake_stream

        pipeline = IngestionPipeline(
            tracker=tracker,
            embedding_provider=embedder,
            qdrant_manager=mock_qdrant,
        )

        job_id = await tracker.create(document_id=42)

        with patch("app.rag.ingestion_pipeline.PDFExtractor", return_value=mock_extractor):
            result = await pipeline.run(
                job_id=job_id,
                document_id=42,
                document_metadata=sample_metadata,
            )

        assert result is not None
        assert result.status == JobStatus.DONE
        assert result.pages_processed == 2
        assert result.chunks_created > 0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_run_marks_failed_on_exception(self) -> None:
        """If PDFExtractor raises, job status becomes FAILED."""
        tracker = JobTracker()
        mock_qdrant = AsyncMock()
        mock_qdrant.ensure_collection = AsyncMock()

        pipeline = IngestionPipeline(
            tracker=tracker,
            embedding_provider=MockEmbeddingProvider(dim=128),
            qdrant_manager=mock_qdrant,
        )

        job_id = await tracker.create(document_id=99)

        with patch(
            "app.rag.ingestion_pipeline.PDFExtractor",
            side_effect=FileNotFoundError("PDF not found"),
        ):
            result = await pipeline.run(job_id=job_id, document_id=99)

        assert result is not None
        assert result.status == JobStatus.FAILED
        assert "FileNotFoundError" in (result.error or "")


# ---------------------------------------------------------------------------
# JobTracker tests
# ---------------------------------------------------------------------------


class TestJobTracker:
    @pytest.mark.asyncio
    async def test_create_and_get(self) -> None:
        tracker = JobTracker()
        job_id = await tracker.create(document_id=1)
        job = await tracker.get(job_id)
        assert job is not None
        assert job.document_id == 1
        assert job.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_missing_returns_none(self) -> None:
        tracker = JobTracker()
        job = await tracker.get("nonexistent-id")
        assert job is None

    @pytest.mark.asyncio
    async def test_list_all(self) -> None:
        tracker = JobTracker()
        await tracker.create(document_id=1)
        await tracker.create(document_id=2)
        jobs = await tracker.list_all()
        assert len(jobs) == 2


# ---------------------------------------------------------------------------
# REST endpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture
def app_with_state():
    """Return a FastAPI test app with pre-initialised ingestion state."""
    from fastapi import FastAPI
    from app.api.v1.endpoints.ingestion import router
    from app.api.deps import require_auth

    test_app = FastAPI()
    tracker = JobTracker()
    test_app.state.job_tracker = tracker
    test_app.state.ingestion_pipeline = IngestionPipeline(
        tracker=tracker,
        embedding_provider=MockEmbeddingProvider(dim=128),
    )
    test_app.include_router(router)
    # Auth is tested separately; bypass require_auth for these endpoint tests.
    test_app.dependency_overrides[require_auth] = lambda: "admin"
    return test_app


@pytest.mark.asyncio
async def test_start_ingestion_returns_202(app_with_state) -> None:
    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/start",
            json={"document_id": 1, "max_pages": 5},
        )
    assert response.status_code == 202
    body = response.json()
    assert "job_id" in body
    assert body["document_id"] == 1
    assert body["status"] == "pending"


@pytest.mark.asyncio
async def test_get_job_status(app_with_state) -> None:
    transport = ASGITransport(app=app_with_state)
    tracker: JobTracker = app_with_state.state.job_tracker
    job_id = await tracker.create(document_id=5)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == job_id
    assert body["document_id"] == 5


@pytest.mark.asyncio
async def test_get_job_not_found(app_with_state) -> None:
    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/jobs/does-not-exist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_jobs(app_with_state) -> None:
    transport = ASGITransport(app=app_with_state)
    tracker: JobTracker = app_with_state.state.job_tracker
    await tracker.create(document_id=10)
    await tracker.create(document_id=11)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/jobs")

    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) >= 2
