## Purpose
This spec defines the behavior of the general mechanics RAG layer, which indexes general mechanical knowledge documents to assist the chatbot in answering non-vehicle-specific questions. It also defines the change to the LLM model used in the chat endpoint.

## ADDED Requirements
### Requirement: General Mechanics RAG Layer
O sistema SHALL fornecer uma camada RAG adicional indexando documentos de mecânica geral localizados em `service_guide/general`.

#### Scenario: Ingest General Mechanics Documents
- **WHEN** the ingestion process is triggered for the general mechanics layer
- **THEN** the system SHALL process each unique PDF file in `service_guide/general` (after deduplication) and insert its chunks into the Qdrant collection `general_mechanics` using the bge-m3 embedding model (1024 dimensions).

#### Scenario: Deduplication of PDFs
- **WHEN** the deduplication script runs on `service_guide/general`
- **THEN** the system SHALL compute the MD5 hash of each PDF file and remove duplicates, keeping only one copy of each unique PDF.

#### Scenario: Query General Mechanics Layer
- **WHEN** a chat request is made
- **THEN** the system SHALL query both the `automotive_manuals` and `general_mechanics` collections, combine the results (e.g., by interleaving or ranking), and pass the combined context to the LLM.

### Requirement: LLM Model Upgrade
O sistema SHALL usar o modelo `qwen3.8:latest` como padrão para geração de respostas no endpoint de chat.

#### Scenario: Chat Endpoint Uses New Model
- **WHEN** a chat request is received and no model is explicitly specified
- **THEN** the system SHALL use the `qwen3.8:latest` model via Ollama to generate the response.