## Why

The project already ingests and indexes technical manuals in Qdrant, but the knowledge remains inaccessible to end users in a natural way. The next step is to provide a conversational interface where technicians, mechanics, and service advisors can ask questions using the vehicle manuals as the source of truth, instead of relying on raw document search or manual navigation.

This interface must be grounded in the existing RAG pipeline, support source-backed answers, and clearly distinguish verified manual facts from hypotheses or unsupported suggestions. The result is a user-facing Q&A experience specialized for automotive troubleshooting and service information retrieval.

## What Changes

- **Python-native web chat frontend** served by the existing FastAPI application using Jinja2 templates and lightweight HTML/JS or HTMX, avoiding Node.js or a separate frontend build pipeline.
- **Conversation API layer** for sending user prompts to the agent and receiving structured responses with citations.
- **RAG-backed answer generation** that retrieves relevant chunks from Qdrant and composes answers using indexed manual evidence.
- **Vehicle and system filtering** so users can scope questions to the correct model, generation, and vehicle system.
- **Citation and source transparency** showing the exact document, chapter, and page references for each answer.
- **Safety guardrails** for hallucination prevention and no-answer scenarios when the source data is not sufficient.

## Capabilities

### New Capabilities
- `agent-chat-frontend`: browser-based conversational interface for user questions grounded in indexed automotive manuals.
- `rag-grounded-chat`: retrieval and answer generation based on Qdrant vector data and metadata filters.
- `manual-citation-display`: source-backed answer tracing with chapter/page references.

### Modified Capabilities
- Existing document ingestion and retrieval pipeline becomes user-visible through a chat surface.
- API layer gains conversational endpoints for UI interactions and session history.

## Impact

- Adds a user-friendly interface to explore the indexed manuals without writing raw queries.
- Makes the RAG system visible and usable by non-technical users.
- Introduces a chat API contract and lightweight frontend templates in the Python application.
- Requires careful answer filtering to preserve the zero-hallucination automotive policy.
- Sets the foundation for future agent features such as troubleshooting steps, follow-up questions, and service workflow suggestions.
