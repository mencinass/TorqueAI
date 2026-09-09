## Context

The system requires structured vehicle context to ensure that searches in service manuals only match the vehicle under inspection. Technical documents on disk (`service_guide/`) need relational representation so that metadata (generation, engine, system, document type) can be leveraged by the future RAG retriever.

## Goals / Non-Goals

**Goals:**
- Provide normalized SQLAlchemy 2.0 ORM models for Brands, Models, Generations, Engines, Vehicles, and Technical Documents.
- Implement async CRUD services with strict Pydantic v2 schemas.
- Provide REST endpoints for vehicle queries and document metadata filtering.
- Implement an idempotent database seeder for MINI R56, MINI R53, and Fiat 500.

**Non-Goals:**
- No PDF parsing or text extraction in this phase (reserved for Phase 3).
- No vector embeddings or Qdrant point creation in this phase (reserved for Phase 3).
- No file upload endpoint for huge PDFs (manuais are read from local storage or volume mount).

## Decisions

### Decision 1: Relational Normalization Hierarchy
- **Chosen Approach**: Separate `brands`, `models`, `generations`, `engines`, and `vehicles` (junction/variant entity) into normalized tables.
- **Rationale**: A model like "Cooper" exists across multiple generations ("R53", "R56", "F56") with completely different engines ("W11" vs "N16" vs "B38") and completely different service manuals. Normalizing generations and engines ensures precision.

### Decision 2: Document Categorization Taxonomy
- **Chosen Approach**: Categorize documents by `document_type` (`workshop_manual`, `repair_manual`, `electrical_diagram`, `torque_specs`) and `system` (`engine`, `transmission`, `steering`, `suspension`, `brakes`, `electrical`, `general`).
- **Rationale**: Allows the future agent to query specifically for `system=steering` when analyzing steering noise complaints.

### Decision 3: Startup Database Seeding
- **Chosen Approach**: Execute `seed_initial_vehicles()` within the FastAPI lifespan startup event if the brand table is empty.
- **Rationale**: Provides instant testing capability for developers without requiring manual database fixtures.

## Risks / Trade-offs

- **[Risk]** Heavy join queries when retrieving vehicle details.
  - **Mitigation**: Use SQLAlchemy `selectinload` / `joinedload` on relationships for single-query hydration.
- **[Risk]** Missing PDF files on disk referenced in the database.
  - **Mitigation**: The seeder checks `os.path.exists()` and records file size dynamically if present.
