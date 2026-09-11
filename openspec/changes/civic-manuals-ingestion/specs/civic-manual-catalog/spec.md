## Purpose

Define o catálogo dos manuais Honda Civic (EJ/EG/EK) no sistema, garantindo que apenas PDFs únicos sejam cadastrados e ingeridos, sem duplicação de conteúdo no índice vetorial.

## ADDED Requirements

### Requirement: Civic Manual Catalog
O sistema SHALL catalogar os manuais de serviço Honda Civic presentes em `service_guide/CVIC/`, referenciando apenas arquivos únicos (desduplicados por conteúdo).

#### Scenario: Unique Civic PDFs Are Cataloged
- **WHEN** o catálogo é inicializado (seed)
- **THEN** os 9 PDFs únicos do Civic são cadastrados em `technical_documents` com `file_path` válido e metadados coerentes.

#### Scenario: Duplicate PDFs Are Excluded
- **WHEN** existem arquivos com conteúdo idêntico (mesmo hash) no diretório
- **THEN** apenas uma cópia de cada conteúdo é cadastrada; as duplicatas são ignoradas.

### Requirement: Civic Ingestable
Os documentos Civic SHALL ser ingeríveis pelo pipeline existente, produzindo chunks no Qdrant com filtros por veículo/geração.

#### Scenario: Civic Searchable
- **WHEN** um manual Civic é ingerido
- **THEN** seus chunks ficam buscáveis com filtro de geração correspondente (EJ/EK/EG).