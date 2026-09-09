## Context

Service manuals for MINI Cooper R56, R53, and Fiat 500 range from 400MB to nearly 600MB. Parsing these documents naively or with C-dependent libraries risks memory crashes or compilation failures. The ingestion pipeline must be strictly 100% pure Python, highly memory efficient, and designed to preserve automotive metadata throughout the chunking and embedding processes.

## Goals / Non-Goals

**Goals:**
- Implement streaming page-by-page PDF extraction using `pypdf` (100% pure Python).
- Build an automotive chunker that associates every chunk with vehicle generation, engine, system, document type, and page number.
- Implement an extensible async embedding service supporting Ollama, OpenAI, and Mock providers.
- Manage Qdrant collections and payload indexes dynamically with deterministic point IDs.
- Provide async job tracking (`JobTracker`) via FastAPI `BackgroundTasks` and a standalone CLI tool.

**Non-Goals:**
- No semantic query search or agent tool execution in this phase (reserved for Phase 4 & 5).
- No OCR processing on raster images (manuais already contain digital text layers).

## Decisions

### Decision 1: Pure Python PDF Streaming via `pypdf`
- **Chosen Approach**: Use `pypdf.PdfReader` with page iteration generators. Read each page, extract text, and release page objects from memory.
- **Alternatives Considered**: `pymupdf` (uses C wrapper) or `pdf2image` + Tesseract. Rejected to maintain strict 100% pure Python compliance without C dependencies.

### Decision 2: Context-Rich Chunking Strategy
- **Chosen Approach**: Slices text into windows of ~1,000 characters with 150 characters of overlap, snapping to paragraph or sentence boundaries.
- **Rationale**: Keeps technical procedures and torque specifications cohesive without splitting critical numerical values across arbitrary boundaries.

### Decision 3: Pluggable Async Embeddings via HTTP
- **Chosen Approach**: Implement `BaseEmbeddingProvider` using `httpx.AsyncClient` for Ollama and OpenAI, with a deterministic `MockEmbeddingProvider` for testing.
- **Rationale**: Prevents hardcoding to a single model while enabling testing without active GPUs or network connections.

### Decision 4: Idempotent Qdrant Point Generation
- **Chosen Approach**: Generate deterministic UUID5 values based on `f"{document_id}:{page_number}:{chunk_index}"`.
- **Rationale**: Allows re-running ingestion on a document without creating duplicate vector points in Qdrant.

## Risks / Trade-offs

- **[Risk]** Extraction speed on 500MB+ PDFs.
  - **Mitigation**: Process in batches of pages and provide progress updates via `JobTracker` and CLI feedback.
- **[Risk]** Ollama service unavailable during background task.
  - **Mitigation**: Clear error logging and marking job status as `failed` with descriptive error messages.

