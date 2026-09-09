## 1. API Contract & Session Model

- [x] 1.1 Define chat request/response schema for frontend and backend communication
- [x] 1.2 Add API endpoints for chat submission and conversation history retrieval
- [x] 1.3 Define vehicle/system filter payloads and validation rules

## 2. Frontend Shell & UX

- [x] 2.1 Create the chat page shell in the Python web app and ensure responsive layout
- [x] 2.2 Implement message list, composer, loading states, and empty-state content
- [x] 2.3 Add vehicle selector and optional system filter controls to the interface

## 3. Retrieval & Grounded Answer Pipeline

- [x] 3.1 Connect the frontend to the existing Qdrant-based retrieval pipeline
- [x] 3.2 Assemble top-K chunks with vehicle, generation, and system metadata filters
- [x] 3.3 Build the answer composer to summarize only verified manual evidence

## 4. Source Citation & Safety

- [x] 4.1 Render document, chapter, page, and section references in the UI
- [x] 4.2 Implement no-answer fallback when source retrieval is insufficient
- [x] 4.3 Add explicit labeling for uncertain or non-manual hypotheses

## 5. Verification & Regression Coverage

- [x] 5.1 Add backend tests for chat request validation and grounded answer flow
- [x] 5.2 Add UI-level tests for message rendering and citation display
- [x] 5.3 Validate the OpenSpec change and ensure the feature is ready for review
