## Why

O diretório `service_guide/CVIC/` contém 13 PDFs de manuais de serviço Honda Civic que ainda não estão cadastrados no catálogo (`technical_documents`) nem indexados no Qdrant. Há 4 duplicatas exatas (mesmo conteúdo) que não devem ser ingeridas, e 9 PDFs únicos que devem entrar no sistema.

## What Changes

- Adiciona a marca **Honda** e o modelo **Civic** (com gerações EJ/EK apropriadas) ao seed do catálogo.
- Cadastra os **9 PDFs únicos** do Civic em `technical_documents`, ignorando as 4 duplicatas.
- Mantém a ingestão automática (`AUTO_INGEST`) ou manual via API como mecanismo de indexação no Qdrant.
- Não altera o pipeline de ingestão nem o chunker.

## Capabilities

### New Capabilities

- `civic-manual-catalog`: catálogo dos manuais Honda Civic (EJ/EG/EK) disponível para consulta e ingestão.

### Modified Capabilities

- `document-ingestion` (existente): passa a cobrir os documentos Civic.

## Impact

- `backend/app/database/seed.py`: novos registros de marca/modelo/geração/documents.
- Nenhum PDF físico é movido/renomeado; apenas referenciado por `file_path`.
- As duplicatas (`62sr320 (1).pdf`, `62sr322 (1).pdf`, `62sr323 (1).pdf`, `62sr324 (1).pdf`) ficam fora do seed.
- Requer reindexação para popular o Qdrant com os novos chunks (auto-ingestão com `AUTO_INGEST_FORCE=true` ou ingestão manual por documento).