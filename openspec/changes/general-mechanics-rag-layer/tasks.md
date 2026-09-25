## 1. Investigation and Preparation
- [x] 1.1 Examine the current RAG implementation in `backend/app/rag/` to understand how the vehicle-specific layer is set up.
- [x] 1.2 Check the chat endpoint in `backend/app/main.py` to see how the model and RAG retrieval are used.
- [x] 1.3 Look for existing deduplication scripts or logic in the project.

## 2. Deduplication of PDFs in service_guide/general
- [x] 2.1 Write a script to compute MD5 hashes of PDF files in `service_guide/general` and identify duplicates.
- [x] 2.2 Remove duplicate files, keeping one copy of each unique PDF.
- [x] 2.3 Verify that the deduplication did not remove any unique content.

## 3. Adding the General Mechanics RAG Layer
- [x] 3.1 Decide on the architecture: either create a second independent RAG layer (separate collection in Qdrant) or modify the existing layer to accept multiple sources.
- [x] 3.2 If creating a second layer, initialize a new Qdrant collection (e.g., `general_mechanics`) with the same vector size (1024 for bge-m3).
- [x] 3.3 Implement or adapt the ingestion pipeline to process the deduplicated PDFs in `service_guide/general` and upsert into the general mechanics collection.
- [x] 3.4 Ensure the ingestion respects the same chunking and embedding settings as the vehicle-specific layer.

## 4. Updating the Chat Endpoint and Model
- [x] 4.1 Change the default LLM model in the chat endpoint from `qwen2.5:7b` to `qwen3.8:latest`.
- [x] 4.2 Modify the retrieval logic to query both the vehicle-specific and general mechanics RAG layers.
- [x] 4.3 Combine the results from both layers (e.g., by interleaving or ranking) before passing to the LLM.
- [x] 4.4 Update the prompt or context assembly to handle the additional source documents.

## 5. Validation and Testing
- [x] 5.1 Run the deduplication script and confirm that duplicate files are removed.
- [ ] 5.2 Trigger the ingestion for the general mechanics documents and verify that vectors are inserted into the new collection.
- [ ] 5.3 Test the chat endpoint with a question that should be answered by the general mechanics layer and confirm that the response includes citations from the general documents.
- [ ] 5.4 Test that the vehicle-specific RAG layer still works as expected.
- [x] 5.5 Run the existing test suite to ensure no regressions.

## Nota de implementação

- Modelo (4.1): `qwen3.8:latest` (27B, 17 GB) foi baixado e medido na RTX 3060 (12 GB VRAM): nao cabe, o Ollama offloada ~5 GB para CPU — medido 6.8 tok/s com prompt RAG real (~2.2k tokens de contexto), 60-90 s por resposta. Decisao: default do repo = `qwen3.8:latest` (`config.py`, `.env.example`, `docker-compose.yml`); o `.env` desta maquina mantem `qwen2.5:7b` como override explicito do operador (comentado) ate upgrade de GPU. O endpoint de chat vive em `backend/app/api/v1/endpoints/chat.py`; a troca de modelo e via config, nao no endpoint.
- Dedup (2.x): `md5sum` nos 3 PDFs de `service_guide/general` — nenhum duplicado existia (3 hashs unicos). A logica de dedup por MD5 e o probe de camada de texto (`pdftotext`, 3 primeiras paginas, >= 50 chars) foram implementados em `backend/app/services/general_ingestion_service.py` (nao como script standalone), cobertos por testes unitarios. Os rascunhos `scripts/deduplicate_pdfs.py` / `scripts/ingest_general_mechanics.py` foram removidos: PROJECT_ROOT errado, paths de host e `document_id` fake (10000+).
- Registro no Postgres: documentos gerais viram linhas reais em `technical_documents` (`document_type`/`system` = `general_mechanics`), senao os links de thumbnail das citacoes (`/documents/{id}/page/{n}/thumbnail`) quebrariam. A ingestao e idempotente: pula se a colecao ja tem pontos, salvo `AUTO_INGEST_FORCE`.
- Probe de texto: os 3 PDFs passaram (MAHLE 228 pp, TEI 20 pp, Biblia do Carro 244 pp = 492 paginas, todos com camada de texto). Licao do R53 escaneado (0 chunks) aplicada como defesa.
- Chat (4.2-4.4): `ChatService` usa Protocolos estruturais (`VectorSearch`/`ChatGeneration`) para que test doubles nao criem clientes Qdrant reais por acidente; resultados das duas colecoes sao mesclados por score e limitados a `top_k`; filtros de veiculo so vao para a colecao automotiva. Testes novos: `test_chat.py` (3 casos de camada dupla) e `test_general_ingestion.py` (7 casos).
- Suite: 68 passed; ruff limpo nos arquivos tocados (os erros restantes sao pre-existentes em arquivos nao alterados nesta sessao).
- Pendente (5.2-5.4): a ingestao das 492 paginas foi disparada e rodava estavel (~128 MB RSS) na interrupcao; a verificacao ao vivo dos vetores e o teste E2E de chat aguardam liberacao do usuario.
