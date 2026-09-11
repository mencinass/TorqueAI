## 1. Catálogo

- [x] 1.1 Adicionar marca Honda e modelo Civic (com gerações EJ/EG) ao `seed.py`, mantendo o padrão existente.
- [x] 1.2 Cadastrar os 9 PDFs únicos em `technical_documents`, com `document_type`/`system` coerentes.
- [x] 1.3 Excluir as 4 duplicatas por conteúdo do seed.

## 2. Validação

- [x] 2.1 Executar `pytest` e garantir que o seed continua idempotente (não duplica marcas existentes).
- [x] 2.2 Validar que os `file_path` dos Civic resolvem para arquivos reais em `service_guide/CVIC/`.
- [x] 2.3 Executar `openspec validate --changes --json` e revisar artefatos.

## Nota de implementação

- Somente 1 de 9 PDFs Civic tem camada de texto (`Civic EJ6, EJ7, EJ8 (96-00) Service Manual.pdf`); os outros 8 são escaneados (imagem sem OCR) e geram 0 chunks. O único com texto (id 6) foi ingerido com sucesso (97.608 chunks).
- Corrigido bug de auto-resolução de `pdf_path`/`document_metadata` na ingestão via API: agora `POST /ingestion/start` resolve `file_path` e metadados a partir do `document_id` quando omitidos (antes exigia `pdf_path` e gravava metadata vazio).