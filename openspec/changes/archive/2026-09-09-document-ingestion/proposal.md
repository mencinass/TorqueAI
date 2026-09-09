## Why

Technical service manuals for vehicles are massive documents (400MB to 600MB with thousands of pages). To enable fast, accurate, and zero-hallucination semantic search in subsequent phases, the system must stream, extract, chunk, vectorize, and index these documents into Qdrant with detailed automotive metadata (generation, engine, system, page number, chapter).

## What Changes

- **Pure Python PDF Streaming Extractor**: Streamed page-by-page text extraction using `pypdf` without loading complete 600MB files into memory.
- **Intelligent Automotive Chunker**: Context-preserving text chunking with configurable window and overlap, tagging every chunk with document and vehicle metadata.
- **Async Embedding Providers**: Modular embedding service supporting Ollama, OpenAI, and deterministic Mock providers for testing.
- **Qdrant Collection & Index Management**: Dynamic collection configuration and payload indexing for generation, system, document type, and page number.
- **Background Ingestion & Job Tracking**: Non-blocking background task execution via FastAPI and CLI runner with real-time progress metrics.

## Capabilities

### New Capabilities
- `document-ingestion`: Extraction, intelligent chunking, embedding generation, and vector indexing of large technical automotive service manuals.

### Modified Capabilities
<!-- No existing capabilities modified -->

## Impact

- Adds `pypdf` dependency (100% pure Python).
- Introduces `app/rag/` pipeline components.
- Exposes `/api/v1/ingestion` endpoints and CLI runner.
- Populates the Qdrant `automotive_manuals` vector collection.

