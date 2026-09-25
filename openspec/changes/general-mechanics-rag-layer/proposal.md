## Why
The current RAG system only indexes vehicle-specific service manuals. To improve the assistant's ability to answer general mechanical questions (e.g., tool usage, common procedures, theory) that are not tied to a specific vehicle, we need a second RAG layer containing general mechanics knowledge bases. Additionally, duplicate files in the general service guide folder waste indexing resources and may cause inconsistent results. The LLM model should also be updated to the more capable qwen3.8:latest for better reasoning.

## What Changes
- Add a new RAG layer for general mechanics documents located in `service_guide/general`.
- Deduplicate PDF files in `service_guide/general` by content hash before ingestion.
- Change the default LLM model for the chat endpoint from `qwen2.5:7b` to `qwen3.8:latest`.

## Capabilities
### New Capabilities
- `general-mechanics-rag`: A RAG layer that indexes general mechanics documents for use in chat responses, providing foundational mechanical knowledge.

### Modified Capabilities
- `ollama-chat-generation (existente)`: Update the default LLM model used in grounded chat generation to `qwen3.8:latest`.

## Impact
- Files touched:
    - `backend/app/core/config.py` (new `GENERAL_MECHANICS_COLLECTION` setting; `CHAT_MODEL` default changed to `qwen3.8:latest`)
    - `backend/app/services/chat_service.py` (dual-collection retrieval with score-ranked merge, structural protocols)
    - `backend/app/services/general_ingestion_service.py` (new: MD5 dedup, text-layer probe, Postgres registration, general-mechanics ingestion)
    - `backend/app/main.py` (second `IngestionPipeline` wired to the general collection + startup task)
    - `backend/tests/test_chat.py`, `backend/tests/test_general_ingestion.py` (new tests)
    - `.env`, `.env.example`, `docker-compose.yml` (collection and model configuration aligned)
    - `openspec/changes/general-mechanics-rag-layer/*` (these artifacts)
- Does NOT change: the vehicle-specific RAG layer, the database schema for chat history, the frontend, or the embedding model (which remains `bge-m3`).