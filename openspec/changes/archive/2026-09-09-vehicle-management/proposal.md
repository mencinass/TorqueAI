## Why

Automotive technical assistance requires strict vehicle contextualization so that diagnostic queries, service procedures, and torque values are never mixed across incompatible vehicle models, generations, or engine variants. This change establishes the structured relational catalog for vehicles and associates technical service manuals with specific vehicle generations and systems.

## What Changes

- **Vehicle Catalog Domain Models**: Pure Python SQLAlchemy 2.0 models for Brands, Models, Generations, Engines, and Vehicle configurations.
- **Document Metadata Models**: Technical Document metadata tracking file paths, file sizes, document types, automotive systems, and vehicle generation linkages.
- **RESTful Endpoints**: Versioned FastAPI endpoints for CRUD and hierarchical querying of brands, models, generations, engines, vehicles, and technical documents.
- **Automated Pre-seeding**: Database seeder for the existing workshop manuals (MINI Cooper R56, MINI Cooper S R53, and Fiat 500).
- **Validation Schemas**: Pydantic v2 request and response schemas ensuring strict input typing.

## Capabilities

### New Capabilities
- `vehicle-management`: Relational vehicle catalog management and association of technical service manuals with vehicle metadata.

### Modified Capabilities
<!-- No modified capabilities -->

## Impact

- Populates the PostgreSQL schema with tables for `brands`, `models`, `generations`, `engines`, `vehicles`, and `technical_documents`.
- Exposes `/api/v1/vehicles` and `/api/v1/documents` endpoints.
- Establishes the prerequisite filtering foundation for the RAG ingestion pipeline (Phase 3 & 4).
