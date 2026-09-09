## Context

The application already stores automotive manuals, chunks, and embeddings in Qdrant. The missing capability is a user-facing chat layer that turns those technical artifacts into an interactive assistant for service and technical questions.

The frontend must help users ask natural questions such as: "Where is the steering rack procedure in this generation?" or "What does this manual say about the DTC P0101 for this vehicle?"

## Goals / Non-Goals

**Goals:**
- Provide a conversational web interface to ask questions grounded in the indexed RAG corpus.
- Keep the chat experience anchored to verified manual sources and metadata filters.
- Surface citations and vehicle/system context in every answer.
- Work with the existing Python backend and RAG infrastructure without introducing a separate Node-based frontend.

**Non-Goals:**
- Full autonomous agent planning or workflow execution beyond retrieval and answer generation.
- Generic internet browsing or external knowledge lookup.
- Automatic warranty or legal claims beyond the indexed manuals.

## Decisions

### Decision 1: Python-native frontend
- **Chosen Approach**: Serve a lightweight chat interface through FastAPI using Jinja2 templates + HTMX or vanilla JavaScript.
- **Rationale**: This preserves the project's strict Python-only backend requirement and avoids introducing a separate frontend build pipeline.

### Decision 2: Retrieval-first answer generation
- **Chosen Approach**: Query Qdrant with vehicle/system filters, rank relevant chunks, and build responses only from the retrieved sources.
- **Rationale**: This keeps the assistant grounded in the service data and minimizes hallucinated technical instructions.

### Decision 3: Citation-first UX
- **Chosen Approach**: Every answer includes a list of sources with document name, section, page, and confidence notes when available.
- **Rationale**: Automotive users need traceability to verify procedures before acting on them.

## Risks / Trade-offs

- **[Risk]** Too much context in a single answer can become verbose.
  - **Mitigation**: Limit the prompt to the top K relevant chunks and summarize only the verified evidence.
- **[Risk]** Ambiguous vehicle or system selection can lead to noisy retrieval.
  - **Mitigation**: Require vehicle context or provide a selector for model/generation/system before the answer is generated.
- **[Risk]** Users may interpret model suggestions as definitive procedures.
  - **Mitigation**: Clearly label uncertain or hypothesis-driven responses as non-verified and separate them from raw manual facts.
