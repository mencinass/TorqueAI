"""On-demand PDF page thumbnails for source validation in the chat UI.

Renders a single PDF page to a PNG via poppler-utils ``pdftoppm`` (already a
runtime dependency), cached on disk so a page is rendered only once.  Page
numbers are validated against the PDF's true page count via ``pdfinfo``.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from app.core.logging import get_logger
from app.rag.pdf_extractor import PDFExtractor

logger = get_logger(__name__)

_THUMB_CACHE_DIR = Path(os.environ.get("THUMB_CACHE_DIR", "/app/.thumb_cache"))
_THUMB_DPI = int(os.environ.get("THUMB_DPI", "120"))
_RENDER_TIMEOUT_SECONDS = 30.0


def _cache_path(document_id: int, page_number: int) -> Path:
    return _THUMB_CACHE_DIR / f"doc_{document_id}_p_{page_number}.png"


class PageThumbnailService:
    """Render and cache a page thumbnail for a technical document."""

    async def render(self, document_id: int, page_number: int, pdf_path: str) -> Path:
        """Return a cached/rendered PNG path for the given page.

        Args:
            document_id: TechnicalDocument primary key (cache namespace only).
            page_number: 1-based page number.
            pdf_path: absolute or resolvable path to the PDF on disk.

        Raises:
            FileNotFoundError: if the PDF cannot be resolved.
            ValueError: if ``page_number`` is out of range.
            RuntimeError: if rendering fails.
        """
        if page_number < 1:
            raise ValueError("page_number must be >= 1")

        cached = _cache_path(document_id, page_number)
        if cached.is_file() and cached.stat().st_size > 0:
            return cached

        extractor = PDFExtractor(document_id=document_id, pdf_path=pdf_path)
        if not extractor.exists():
            raise FileNotFoundError(f"PDF not found for document {document_id}")

        total_pages = await asyncio.to_thread(extractor.get_total_pages)
        if page_number > total_pages:
            raise ValueError(
                f"page_number {page_number} out of range (1-{total_pages})"
            )

        _THUMB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        # Render to a temp file then atomically rename, so a concurrent reader
        # never sees a half-written PNG.
        tmp = cached.with_suffix(cached.suffix + ".tmp")
        await self._render_pdf_page(extractor.resolved_path, page_number, tmp)
        tmp.replace(cached)
        return cached

    async def _render_pdf_page(self, pdf_path: str, page_number: int, out: Path) -> None:
        """Run ``pdftoppm`` for a single page, writing PNG bytes to ``out``."""
        # pdftoppm -singlefile writes <prefix>.png; use a temp prefix then move.
        prefix = out.with_suffix("")  # /path/doc_1_p_3 (no .png)
        proc = await asyncio.create_subprocess_exec(
            "pdftoppm",
            "-f", str(page_number),
            "-l", str(page_number),
            "-r", str(_THUMB_DPI),
            "-png",
            "-singlefile",
            pdf_path,
            str(prefix),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=_RENDER_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError(f"thumbnail render timed out for page {page_number}")

        if proc.returncode != 0:
            err = stderr.decode(errors="replace").strip()[:200]
            raise RuntimeError(
                f"pdftoppm failed for page {page_number} (exit {proc.returncode}): {err}"
            )

        # pdftoppm wrote prefix.png; move it to the expected cache path.
        produced = Path(str(prefix) + ".png")
        if produced != out and produced.is_file():
            produced.replace(out)
        if not out.is_file() or out.stat().st_size == 0:
            raise RuntimeError(f"thumbnail not produced for page {page_number}")