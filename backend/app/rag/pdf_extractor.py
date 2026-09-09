import os
import asyncio
from typing import AsyncGenerator, Dict, Optional
import pypdf
from app.core.logging import logger

PAGE_EXTRACT_TIMEOUT_SECONDS = 30.0


class PDFExtractor:
    """Memory-efficient streaming PDF page extractor in 100% Pure Python."""

    def __init__(
        self,
        file_path: Optional[str] = None,
        document_id: Optional[int] = None,
        pdf_path: Optional[str] = None,
    ):
        resolved_input = pdf_path or file_path
        if not resolved_input:
            raise ValueError(f"A PDF path is required for document {document_id}")
        self.raw_path = resolved_input
        self.resolved_path = self._resolve_path(resolved_input)

    @property
    def total_pages(self) -> int:
        return self.get_total_pages()

    @staticmethod
    def _resolve_path(path: str) -> str:
        """Resolve file path across typical working directory locations."""
        candidates = [
            path,
            os.path.join("..", path),
            os.path.join(os.getcwd(), path),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), path),
        ]
        for c in candidates:
            if os.path.exists(c) and os.path.isfile(c):
                return os.path.abspath(c)
        return path

    def exists(self) -> bool:
        return os.path.exists(self.resolved_path) and os.path.isfile(self.resolved_path)

    def get_total_pages(self) -> int:
        """Read page count without loading the entire document body into memory."""
        if not self.exists():
            raise FileNotFoundError(f"PDF file not found at: {self.resolved_path}")
        with open(self.resolved_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            return len(reader.pages)

    async def stream_pages(
        self,
        start_page: int = 1,
        max_pages: Optional[int] = None,
    ) -> AsyncGenerator[Dict[str, any], None]:
        """Stream pages sequentially to prevent high memory consumption on 500MB+ PDFs."""
        if not self.exists():
            raise FileNotFoundError(f"PDF file not found at: {self.resolved_path}")

        logger.info(f"Streaming PDF extraction: {self.resolved_path} (from page {start_page})")

        with open(self.resolved_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            total_pages = len(reader.pages)
            end_page = total_pages
            if max_pages is not None:
                end_page = min(total_pages, start_page + max_pages - 1)

            def _extract_page_text(idx: int) -> str:
                """Run on a worker thread: page lookup + text extraction both do
                blocking, synchronous parsing work that can stall the event loop
                on large or malformed PDFs."""
                return reader.pages[idx].extract_text() or ""

            for page_idx in range(start_page - 1, end_page):
                page_num = page_idx + 1
                try:
                    text = await asyncio.wait_for(
                        asyncio.to_thread(_extract_page_text, page_idx),
                        timeout=PAGE_EXTRACT_TIMEOUT_SECONDS,
                    )
                    cleaned_text = text.strip()

                    # Extract the first non-empty line as a section/chapter title candidate
                    lines = [line.strip() for line in cleaned_text.splitlines() if line.strip()]
                    section_candidate = lines[0][:120] if lines else "General"

                    yield {
                        "page_number": page_num,
                        "text": cleaned_text,
                        "char_count": len(cleaned_text),
                        "section_title": section_candidate,
                        "total_pages": total_pages,
                    }
                except asyncio.TimeoutError:
                    logger.warning(
                        f"Timed out extracting page {page_num} in {self.raw_path} "
                        f"after {PAGE_EXTRACT_TIMEOUT_SECONDS}s; skipping page"
                    )
                    yield {
                        "page_number": page_num,
                        "text": "",
                        "char_count": 0,
                        "section_title": "Unreadable Page",
                        "total_pages": total_pages,
                    }
                except Exception as exc:
                    logger.warning(f"Error reading page {page_num} in {self.raw_path}: {exc}")
                    yield {
                        "page_number": page_num,
                        "text": "",
                        "char_count": 0,
                        "section_title": "Unreadable Page",
                        "total_pages": total_pages,
                    }

