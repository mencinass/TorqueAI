## Context

O frontend do chat é um bloco HTML único em `chat.py`. Os filtros são inputs de texto livre e as thumbnails são grade de imagens sempre renderizadas. O catálogo já tem marcas/modelos/gerações e os chunks carregam `system` e `generation_code` no payload.

## Goals / Non-Goals

**Goals:**
- Facilidade de uso: dropdowns com opções reais (sem digitação).
- Leitura de fonte: thumbnail por hyperlink expansível, layout limpo.
- Manter o chat autocontido (sem build).

**Non-Goals:**
- Não muda RAG, schemas de resposta, nem adiciona framework.

## Decisions

### Decision 1: Dropdowns populados por endpoint
- **Chosen Approach**: novo endpoint `GET /api/v1/vehicles/picker` retorna gerações (`code` + `name`) e sistemas (`system`) com documentos; frontend preenche `<select>` via fetch.
- **Rationale**: evita hardcode e só mostra o que está disponível/ingerido.
- **Alternative Rejected**: manter texto livre com datalist (ainda permite erros).

### Decision 2: Thumbnail como hyperlink + modal
- **Chosen Approach**: cada citação vira um link compacto; clique abre modal com a imagem ampliada (mesmo endpoint de thumbnail já existe).
- **Rationale**: elimina enfileiramento confuso, dá leitura ampliada sob demanda.
- **Alternative Rejected**: manter grade de miniaturas (ocupa espaço e cansa visualmente).

## Risks / Trade-offs

- **[Risk]** Modal de imagem pode ser pesado (PNG ~182KB por página).
  - **Mitigation**: lazy-load só no clique, `loading="lazy"` quando aplicável.
- **[Risk]** `GET /vehicles/picker` pode retornar vazio se nada ingerido.
  - **Mitigation**: dropdown mostra "Sem opções" e permite busca sem filtro.

## Migration Plan

1. Adicionar endpoint de opções.
2. Atualizar HTML/JS para dropdowns + modal.
3. Validar com testes e manualmente no navegador.