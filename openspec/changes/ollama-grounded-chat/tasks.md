## 1. Ollama Provider & Configuration

- [x] 1.1 Add chat-model, base URL, timeout, temperature, and token-limit settings and verify defaults load under Python 3.11
- [x] 1.2 Implement the asynchronous Ollama HTTP provider for `POST /api/chat` and verify success, malformed response, timeout, and HTTP error tests
- [x] 1.3 Add provider selection and an explicit extrative fallback configuration, then verify unknown provider values fail with a clear configuration error

## 2. Grounded Prompt & Chat Integration

- [x] 2.1 Implement a server-side automotive system prompt with strict source-grounding and citation rules, verified by prompt unit tests
- [x] 2.2 Build the bounded context payload from retrieved chunks, including vehicle metadata and numbered source references, verified by unit tests
- [x] 2.3 Integrate Ollama generation into the chat service while preserving `grounded`, citations, session context, and no-evidence behavior, verified by service tests
- [x] 2.4 Map provider connection and timeout failures to HTTP 503 without leaking infrastructure details, verified by endpoint integration tests

## 3. Frontend Response Experience

- [x] 3.1 Render synthesized assistant responses as text or markdown-safe HTML while retaining original manual citations, verified by UI response tests
- [x] 3.2 Display explicit labels for verified evidence, insufficient evidence, and diagnostic hypotheses, verified by frontend behavior tests
- [x] 3.3 Show a non-blocking local-model availability error and preserve the submitted question for retry, verified by browser/API integration tests

## 4. Verification & Documentation

- [x] 4.1 Document Ollama installation, model pull, environment variables, and local startup commands in the project guide
- [x] 4.2 Run the complete Python 3.11 test suite with Ollama mocked and verify no regressions
- [x] 4.3 Validate the OpenSpec change and review the generated API contract before implementation is considered complete
