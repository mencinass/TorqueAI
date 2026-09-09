## Purpose

Extracts, chunks, embeds, and indexes large technical automotive service manuals into vector storage with full contextual metadata.

## ADDED Requirements

### Requirement: Streaming PDF Text Extraction
The system SHALL stream text from PDF service manuals page by page using pure Python without reading the complete file into RAM simultaneously.

#### Scenario: Extract Page Text with Page Metadata
- **WHEN** a document ingestion process processes a large service manual PDF
- **THEN** the system extracts page text sequentially and tags each page with its 1-indexed page number and detected chapter or header information.

### Requirement: Automotive Context Chunking
The system SHALL partition extracted page text into sliding-window text chunks while permanently attaching vehicle, system, and document metadata to each chunk.

#### Scenario: Chunk Generated with Vehicle Metadata
- **WHEN** text is partitioned from a MINI R56 manual covering the steering system
- **THEN** every resulting chunk payload retains `generation_code: "R56"`, `system: "steering"`, `document_id`, and `page_number` for downstream retrieval filtering.

### Requirement: Vector Storage and Payload Indexing
The system SHALL generate high-dimensional embeddings for all chunks and upsert them in batches into Qdrant with payload indices on vehicle attributes.

#### Scenario: Chunks Upserted to Vector Collection
- **WHEN** embeddings are generated for extracted document chunks
- **THEN** the system upserts vectors to the `automotive_manuals` Qdrant collection alongside searchable metadata fields.

### Requirement: Background Job Execution and Progress Tracking
The system SHALL support asynchronous background execution for document ingestion jobs and provide real-time status query endpoints.

#### Scenario: Start Background Ingestion Job
- **WHEN** a client submits a valid ingestion request to `POST /api/v1/ingestion/start`
- **THEN** the system schedules the ingestion in the background and returns HTTP 202 Accepted with a unique job ID and initial status "pending".

#### Scenario: Query Ingestion Progress
- **WHEN** a client queries `GET /api/v1/ingestion/jobs/{job_id}` for an active ingestion job
- **THEN** the system returns the current progress including pages processed, total pages, chunks created, and job status.

