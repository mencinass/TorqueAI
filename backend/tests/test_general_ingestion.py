"""Tests for the general mechanics RAG layer (registration + ingestion).

Covers:
- register_general_documents: dedup by MD5, text-layer probe, idempotency
- ingest_general_documents: AUTO_INGEST gating and empty-collection skip
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.ingestion_pipeline import JobTracker
from app.services import general_ingestion_service as gis


class _FakeSessionFactory:
    """Session factory whose sessions accumulate committed rows across calls."""

    def __init__(self):
        self.store: list = []
        self.sessions: list[_FakeSession] = []

    def __call__(self):
        session = _FakeSession(existing_rows=list(self.store))
        session._store = self.store
        self.sessions.append(session)
        return session


class _FakeSession:
    """Minimal async session capturing added TechnicalDocument rows."""

    def __init__(self, existing_rows=None):
        self.added = []
        self.committed = 0
        self._store: list = existing_rows or []
        self._existing = existing_rows or []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, stmt):
        rows = list(self._existing) + list(self.added)
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: rows))

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed += 1
        self._store.extend(self.added)


def _make_pdf(tmp_path: Path, name: str, content: bytes) -> Path:
    target = tmp_path / "general"
    target.mkdir(parents=True, exist_ok=True)
    pdf = target / name
    pdf.write_bytes(content)
    return pdf


class TestRegisterGeneralDocuments:
    @pytest.mark.asyncio
    async def test_deduplicates_identical_content(self, tmp_path, monkeypatch):
        _make_pdf(tmp_path, "manual-a.pdf", b"SAME-CONTENT")
        _make_pdf(tmp_path, "manual-b.pdf", b"DIFFERENT-CONTENT")
        _make_pdf(tmp_path, "manual-a-copy.pdf", b"SAME-CONTENT")
        monkeypatch.setattr(gis, "_resolve_general_dir", lambda: tmp_path / "general")
        monkeypatch.setattr(gis, "_probe_has_text_layer", lambda p: True)
        factory = _FakeSessionFactory()
        with patch("app.services.general_ingestion_service.async_session_factory", factory):
            documents = await gis.register_general_documents()
        files = [Path(d.file_path).name for d in documents]
        # Exactly one of the two identical files survives (the first
        # encountered by sorted() order), plus the unique file.
        survivors = {f for f in files if f.startswith("manual-a")}
        assert len(survivors) == 1
        assert "manual-b.pdf" in files

    @pytest.mark.asyncio
    async def test_skips_scanned_pdfs_without_text_layer(self, tmp_path, monkeypatch):
        _make_pdf(tmp_path, "real-text.pdf", b"TEXT")
        _make_pdf(tmp_path, "scanned-only.pdf", b"IMAGE")
        monkeypatch.setattr(gis, "_resolve_general_dir", lambda: tmp_path / "general")
        monkeypatch.setattr(
            gis,
            "_probe_has_text_layer",
            lambda p: p.name == "real-text.pdf",
        )
        factory = _FakeSessionFactory()
        with patch("app.services.general_ingestion_service.async_session_factory", factory):
            documents = await gis.register_general_documents()
        files = [Path(d.file_path).name for d in documents]
        assert files == ["real-text.pdf"]

    @pytest.mark.asyncio
    async def test_is_idempotent_for_already_registered_paths(self, tmp_path, monkeypatch):
        pdf = _make_pdf(tmp_path, "already-there.pdf", b"CONTENT")
        monkeypatch.setattr(gis, "_resolve_general_dir", lambda: tmp_path / "general")
        monkeypatch.setattr(gis, "_probe_has_text_layer", lambda p: True)
        existing = SimpleNamespace(
            id=1,
            file_path=f"service_guide/general/{pdf.name}",
            title="already there",
            document_type="general_mechanics",
            system="general_mechanics",
        )
        factory = _FakeSessionFactory()
        factory.store.append(existing)
        with patch("app.services.general_ingestion_service.async_session_factory", factory):
            documents = await gis.register_general_documents()
        assert factory.sessions[0].added == []
        assert documents == [existing]

    @pytest.mark.asyncio
    async def test_registers_relative_service_guide_path(self, tmp_path, monkeypatch):
        _make_pdf(tmp_path, "doc.pdf", b"CONTENT")
        monkeypatch.setattr(gis, "_resolve_general_dir", lambda: tmp_path / "general")
        monkeypatch.setattr(gis, "_probe_has_text_layer", lambda p: True)
        factory = _FakeSessionFactory()
        with patch("app.services.general_ingestion_service.async_session_factory", factory):
            await gis.register_general_documents()
        assert factory.sessions[0].added[0].file_path == "service_guide/general/doc.pdf"
        assert factory.sessions[0].added[0].document_type == "general_mechanics"


class TestIngestGeneralDocuments:
    @pytest.mark.asyncio
    async def test_disabled_when_auto_ingest_off(self, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "AUTO_INGEST_ENABLED", False, raising=False)
        qdrant = AsyncMock()
        with patch("app.services.general_ingestion_service.QdrantManager", return_value=qdrant):
            await gis.ingest_general_documents(JobTracker(), MagicMock())
        qdrant.ensure_collection.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_when_collection_not_empty(self, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "AUTO_INGEST_ENABLED", True, raising=False)
        qdrant = AsyncMock()
        qdrant.collection_info = AsyncMock(
            return_value={"points_count": 500, "status": "green", "dim": 1024}
        )
        with patch("app.services.general_ingestion_service.QdrantManager", return_value=qdrant):
            with patch.object(gis, "register_general_documents", AsyncMock()) as register:
                await gis.ingest_general_documents(JobTracker(), MagicMock())
        register.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ingests_when_collection_empty(self, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "AUTO_INGEST_ENABLED", True, raising=False)
        qdrant = AsyncMock()
        qdrant.collection_info = AsyncMock(
            return_value={"points_count": 0, "status": "green", "dim": 1024}
        )
        document = SimpleNamespace(
            id=900,
            title="A Biblia do Carro",
            file_path="service_guide/general/A-B-blia-do-Carro-Paulo-G.-Costa.pdf",
            document_type="general_mechanics",
            system="general_mechanics",
        )
        pipeline = AsyncMock()
        with patch("app.services.general_ingestion_service.QdrantManager", return_value=qdrant):
            with patch.object(
                gis, "register_general_documents", AsyncMock(return_value=[document])
            ):
                with patch("pathlib.Path.is_file", lambda self: True):
                    await gis.ingest_general_documents(JobTracker(), pipeline)
        pipeline.run.assert_awaited_once()
        job_doc_id = pipeline.run.await_args.kwargs["document_id"]
        assert job_doc_id == 900
