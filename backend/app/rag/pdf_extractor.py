import os
import asyncio
import resource
import subprocess
from typing import AsyncGenerator, Dict, Optional
from app.core.logging import logger

PAGE_EXTRACT_TIMEOUT_SECONDS = 30.0
# Caps the address space of each per-page pdftotext subprocess so a single
# pathological page (e.g. a zlib decompression bomb) fails fast with a clean
# error instead of exhausting host memory.
PAGE_EXTRACT_MEMORY_LIMIT_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB


def _limit_child_memory() -> None:
    """preexec_fn: apply RLIMIT_AS to the pdftotext child process only."""
    resource.setrlimit(
        resource.RLIMIT_AS,
        (PAGE_EXTRACT_MEMORY_LIMIT_BYTES, PAGE_EXTRACT_MEMORY_LIMIT_BYTES),
    )


class PDFExtractor:
    """Streaming PDF page extractor backed by poppler-utils (pdfinfo/pdftotext).

    Each page is extracted in its own OS subprocess with a hard timeout and a
    memory cap. Unlike an in-process library (e.g. pypdf) running inside a
    thread, a stuck or memory-hungry page gets killed outright (SIGKILL) via
    the subprocess, and the asyncio event loop stays fully responsive since no
    GIL-holding C call ever runs in the main process.
    """

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
        """Read the page count via ``pdfinfo`` (blocking; callers run this in a worker thread)."""
        if not self.exists():
            raise FileNotFoundError(f"PDF file not found at: {self.resolved_path}")
        result = subprocess.run(
            ["pdfinfo", self.resolved_path],
            capture_output=True,
            text=True,
            timeout=PAGE_EXTRACT_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            raise RuntimeError(f"pdfinfo failed for {self.resolved_path}: {result.stderr.strip()[:200]}")
        for line in result.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":", 1)[1].strip())
        raise RuntimeError(f"pdfinfo output missing 'Pages:' for {self.resolved_path}")

    async def _extract_page_text(self, page_num: int) -> str:
        """Run pdftotext for a single page in its own subprocess, with a hard
        timeout and memory cap so a pathological page can never hang or grow
        without bound."""
        proc = await asyncio.create_subprocess_exec(
            "pdftotext",
            "-f", str(page_num),
            "-l", str(page_num),
            "-layout",
            self.resolved_path,
            "-",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=_limit_child_memory,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=PAGE_EXTRACT_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise

        if proc.returncode != 0:
            raise RuntimeError(
                f"pdftotext failed for page {page_num} (exit {proc.returncode}): "
                f"{stderr.decode(errors='replace').strip()[:200]}"
            )
        return stdout.decode("utf-8", errors="replace")

    async def stream_pages(
        self,
        start_page: int = 1,
        max_pages: Optional[int] = None,
    ) -> AsyncGenerator[Dict[str, any], None]:
        """Stream pages sequentially, each extracted in its own subprocess."""
        if not self.exists():
            raise FileNotFoundError(f"PDF file not found at: {self.resolved_path}")

        logger.info(f"Streaming PDF extraction: {self.resolved_path} (from page {start_page})")

        total_pages = await asyncio.to_thread(self.get_total_pages)
        end_page = total_pages
        if max_pages is not None:
            end_page = min(total_pages, start_page + max_pages - 1)

        for page_num in range(start_page, end_page + 1):
            try:
                text = await self._extract_page_text(page_num)
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

