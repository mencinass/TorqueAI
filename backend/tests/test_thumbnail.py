"""Tests for the PDF page thumbnail service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.thumbnail_service import PageThumbnailService, _cache_path


@pytest.mark.asyncio
async def test_render_uses_cache_when_present(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "app.services.thumbnail_service._THUMB_CACHE_DIR", tmp_path
    )
    svc = PageThumbnailService()
    # Pre-seed the cache so render() returns without invoking pdftoppm.
    cached = _cache_path(document_id=1, page_number=42)
    cached.write_bytes(b"fake-png-bytes")

    result = await svc.render(document_id=1, page_number=42, pdf_path="/x.pdf")

    assert result == cached
    assert cached.read_bytes() == b"fake-png-bytes"


@pytest.mark.asyncio
async def test_render_rejects_out_of_range_page(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "app.services.thumbnail_service._THUMB_CACHE_DIR", tmp_path
    )
    svc = PageThumbnailService()

    with patch("app.services.thumbnail_service.PDFExtractor") as mock_cls:
        mock_extractor = MagicMock()
        mock_extractor.exists.return_value = True
        mock_extractor.get_total_pages.return_value = 10
        mock_cls.return_value = mock_extractor

        with pytest.raises(ValueError, match="out of range"):
            await svc.render(document_id=1, page_number=99, pdf_path="/x.pdf")


@pytest.mark.asyncio
async def test_render_rejects_missing_pdf(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "app.services.thumbnail_service._THUMB_CACHE_DIR", tmp_path
    )
    svc = PageThumbnailService()

    with patch("app.services.thumbnail_service.PDFExtractor") as mock_cls:
        mock_extractor = MagicMock()
        mock_extractor.exists.return_value = False
        mock_cls.return_value = mock_extractor

        with pytest.raises(FileNotFoundError):
            await svc.render(document_id=1, page_number=1, pdf_path="/missing.pdf")