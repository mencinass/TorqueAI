## Purpose

Provide a conversational frontend that lets users ask technical questions about vehicles and service manuals while grounding every answer in the indexed RAG corpus and associated manual metadata.

## ADDED Requirements

### Requirement: Conversational Frontend
The system SHALL provide a browser-based chat interface for submitting questions about vehicle service documentation and technical troubleshooting.

#### Scenario: User Asks a Vehicle Question
- **WHEN** a technician selects a vehicle model and enters a question such as "What is the procedure for removing the steering rack?"
- **THEN** the frontend sends the question and selected vehicle context to the backend chat endpoint and displays a response with the relevant support evidence.

### Requirement: RAG Source Grounding
The system SHALL retrieve the most relevant document chunks from the existing vector index before composing an answer, and it SHALL use those chunks as the source of truth for the response.

#### Scenario: Retrieve Relevant Manual Evidence
- **WHEN** a user asks a question about a specific generation or vehicle system
- **THEN** the system filters retrieval by vehicle metadata, system metadata, and semantic relevance before generating the answer.

### Requirement: Citation Display
The system SHALL include source citations in each answer so that the user can inspect the manual, chapter, and page that support the answer.

#### Scenario: Show Source References
- **WHEN** the backend generates a grounded response
- **THEN** the UI displays the answer together with the corresponding document title, chapter, section, and page references.

### Requirement: Hallucination Guardrails
The system SHALL explicitly indicate when the indexed manuals cannot support the user's question and SHALL avoid presenting unsupported claims as verified facts.

#### Scenario: No Verified Source Found
- **WHEN** the query cannot be matched to any reliable manual section within the indexed corpus
- **THEN** the system returns a clear no-answer or insufficient-evidence response and asks the user for more context instead of inventing a technical answer.

### Requirement: Conversation Context
The system SHALL preserve the current chat session context for follow-up questions and continue the conversation using the same vehicle and system filters unless the user changes them.

#### Scenario: Follow-up Question
- **WHEN** a user asks a follow-up question after an initial answer
- **THEN** the system keeps the prior context and applies the same retrieval boundaries to the new question unless the user changes the vehicle or system filter.
