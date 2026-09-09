## 1. Dependencies & Core Extractors

- [x] 1.1 Add `pypdf` to `backend/requirements.txt` maintaining strict pure Python compliance
- [x] 1.2 Implement `PDFExtractor` streaming page parser in `backend/app/rag/pdf_extractor.py`
- [x] 1.3 Implement `AutomotiveChunker` with metadata preservation in `backend/app/rag/chunker.py`

## 2. Embeddings & Vector Storage

- [x] 2.1 Implement `BaseEmbeddingProvider` with Ollama, OpenAI, and Mock providers in `backend/app/rag/embeddings.py`
- [x] 2.2 Implement Qdrant collection initialization and batch upsert in `backend/app/rag/qdrant_manager.py`

## 3. Ingestion Pipeline & Background Execution

- [x] 3.1 Implement `IngestionPipeline` orchestrator and `JobTracker` in `backend/app/rag/ingestion_pipeline.py`
- [x] 3.2 Implement CLI ingestion tool in `backend/app/rag/cli.py`
- [x] 3.3 Implement ingestion REST endpoints in `backend/app/api/v1/endpoints/ingestion.py` and register in `backend/app/api/v1/api.py`

## 4. Verification & Testing

- [x] 4.1 Implement automated tests for extractor, chunker, and embeddings in `backend/tests/test_ingestion.py`
- [ ] 4.2 Validate and archive OpenSpec change `document-ingestion`

