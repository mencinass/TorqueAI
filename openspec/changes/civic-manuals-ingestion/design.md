## Context

O seed atual (`backend/app/database/seed.py`) cria apenas MINI (R56/R53) e Fiat (500). Os PDFs do Honda Civic estão fisicamente em `service_guide/CVIC/` mas não referenciados no banco. A ingestão é acionada por auto-ingestão no startup ou via `POST /api/v1/ingestion/start`.

## Goals / Non-Goals

**Goals:**
- Disponibilizar os manuais Civic no catálogo e habilitar sua ingestão.
- Evitar ingerir duplicatas.
- Manter o seed idempotente.

**Non-Goals:**
- Não mexe no pipeline de ingestão/chunker/embeddings.
- Não renomeia/reorganiza os PDFs existentes.

## Decisions

### Decision 1: Cadastrar apenas PDFs únicos por conteúdo
- **Chosen Approach**: deduplicar por md5; cadastrar os 9 únicos.
- **Rationale**: evita chunks duplicados no Qdrant e custo de ingestão desnecessário.
- **Alternative Rejected**: cadastrar tudo, que poluiria o índice.

### Decision 2: Marca/modelo dedicados para Civic
- **Chosen Approach**: adicionar `Honda` + `Civic`, com gerações por chassis (EJ/EG/EK).
- **Rationale**: permite filtrar consultas por geração como já acontece com MINI/Fiat.
- **Alternative Rejected**: reaproveitar marca/modelo genérico, que perderia rastreabilidade.

## Risks / Trade-offs

- **[Risk]** `file_path` com espaço/parênteses (`Civic EJ6, EJ7, EJ8 (96-00)...`) pode quebrar resolução de caminho.
  - **Mitigation**: usar exatamente o nome de arquivo real e validar `resolve_size`/`is_file` no seed.
- **[Risk]** PDFs escaneados (sem camada de texto) geram 0 chunks.
  - **Mitigation**: validar extração de texto de uma amostra antes de concluir a ingestão.

## Migration Plan

1. Atualizar `seed.py` com Honda/Civic + 9 documentos.
2. Recriar o backend e acionar reindexação (`AUTO_INGEST_FORCE=true`, depois desligar).
3. Validar pontos no Qdrant e busca real por geração Civic.