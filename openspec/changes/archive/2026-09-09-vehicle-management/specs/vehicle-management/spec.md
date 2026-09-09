## Purpose

Manages the relational vehicle catalog hierarchy and links technical service manuals with specific brands, models, generations, and automotive systems.

## ADDED Requirements

### Requirement: Hierarchical Vehicle Catalog
The system SHALL maintain a normalized relational hierarchy consisting of Brands, Models, Generations, Engines, and Vehicle configurations to uniquely identify automotive contexts.

#### Scenario: Retrieve Models for a Specific Brand
- **WHEN** a client queries models filtered by a valid brand ID
- **THEN** the system returns only models associated with that brand.

#### Scenario: Retrieve Vehicle Detailed Context
- **WHEN** a client queries a vehicle configuration by its unique ID
- **THEN** the system returns the complete automotive context including brand name, model name, generation code, production years, and engine specifications.

### Requirement: Technical Document Association
The system SHALL register and query technical document metadata indexed by document type, automotive system, vehicle generation, and engine variant.

#### Scenario: Filter Documents by Generation and Automotive System
- **WHEN** a client requests technical documents specifying generation code "R56" and system "steering"
- **THEN** the system returns only documents matching that vehicle generation and system without leaking documents belonging to other vehicles.

#### Scenario: Prevent Orphan Documents
- **WHEN** a document registration request specifies a nonexistent generation ID
- **THEN** the system rejects the registration with an HTTP 404 or 422 error and does not persist the record.

### Requirement: Initial Vehicle Seeding
The system SHALL provide an idempotent database seeder that creates initial vehicle entries for available workshop manuals on application startup.

#### Scenario: First Boot Catalog Seeding
- **WHEN** the application starts up and finds an empty vehicle catalog
- **THEN** it automatically creates records for MINI Cooper R56, MINI Cooper S R53, and Fiat 500 alongside their corresponding manual file references.
