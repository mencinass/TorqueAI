import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DocumentChunk:
    """A granular unit of technical manual text enriched with vehicle metadata."""

    chunk_id: str
    text: str
    chunk_index: int
    page_number: int
    section_title: str
    document_id: int
    document_title: str
    document_type: str
    system: str
    generation_code: Optional[str]
    engine_code: Optional[str]
    created_at: str

    def to_payload(self) -> Dict[str, Any]:
        """Convert chunk into a JSON-compatible dictionary for Qdrant vector payload."""
        return asdict(self)


class AutomotiveChunker:
    """Partitions page text into coherent chunks while preserving critical automotive context."""

    NAMESPACE = uuid.UUID("a7b3c2d1-e4f5-4a6b-8c9d-0e1f2a3b4c5d")

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        min_chunk_size: int = 60,
        overlap: int | None = None,
    ):
        if overlap is not None:
            chunk_overlap = overlap
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_page(
        self,
        page_text: str,
        page_number: int,
        section_title: str,
        document_metadata: Dict[str, Any],
    ) -> List[DocumentChunk]:
        """Split a single page's text into overlapping chunks with full vehicle context."""
        cleaned_text = page_text.strip()
        if not cleaned_text or len(cleaned_text) < self.min_chunk_size:
            return []

        # Split text into sliding windows
        chunks: List[DocumentChunk] = []
        start = 0
        chunk_idx = 0
        text_len = len(cleaned_text)

        while start < text_len:
            end = start + self.chunk_size

            # If not at the very end, try to break cleanly on a paragraph or newline
            if end < text_len:
                newline_pos = cleaned_text.rfind("\n\n", start, end)
                if newline_pos > start + self.min_chunk_size:
                    end = newline_pos + 2
                else:
                    period_pos = cleaned_text.rfind(". ", start, end)
                    if period_pos > start + self.min_chunk_size:
                        end = period_pos + 2

            segment = cleaned_text[start:end].strip()

            if len(segment) >= self.min_chunk_size:
                doc_id = document_metadata.get("document_id", 0)
                # Deterministic UUID5 based on document, page, and chunk index
                unique_name = f"doc_{doc_id}_p_{page_number}_c_{chunk_idx}"
                point_id = str(uuid.uuid5(self.NAMESPACE, unique_name))

                chunks.append(
                    DocumentChunk(
                        chunk_id=point_id,
                        text=segment,
                        chunk_index=chunk_idx,
                        page_number=page_number,
                        section_title=section_title,
                        document_id=doc_id,
                        document_title=document_metadata.get("document_title", ""),
                        document_type=document_metadata.get("document_type", "workshop_manual"),
                        system=document_metadata.get("system", "general").lower(),
                        generation_code=document_metadata.get("generation_code"),
                        engine_code=document_metadata.get("engine_code"),
                        created_at=datetime.now(timezone.utc).isoformat(),
                    )
                )
                chunk_idx += 1

            if end >= text_len:
                break

            start = end - self.chunk_overlap
            if start <= 0 and end <= start:
                break

        return chunks

