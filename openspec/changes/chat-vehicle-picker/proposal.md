## Why

O chat hoje usa campos de texto livre para "Geração" e "Sistema", o que é confuso e propenso a erro (códigos errados, caixa alta/baixa, valores que não existem no catálogo). Além disso, as thumbnails de fonte são exibidas enfileiradas uma embaixo da outra, ocupando muito espaço e dificultando a leitura.

## What Changes

- Substitui os campos de texto "Geração" e "Sistema" por **dropdowns** populados a partir do que existe no catálogo (gerações com manuais indexados e sistemas disponíveis).
- Adiciona endpoints de "opções" que listam as gerações e sistemas com documentos disponíveis.
- Transforma as thumbnails de fonte em **hyperlinks compactos**: um único link por citação que, ao ser clicado, expande/abre a imagem para leitura (inline modal ou nova aba), em vez de enfileirar todas as imagens.
- Preserva o fluxo de chat e os filtros (agora vindos dos dropdowns).

## Capabilities

### New Capabilities

- `vehicle-system-picker`: seleção de veículo/geração e sistema via dropdowns populados dinamicamente a partir do catálogo indexado.

### Modified Capabilities

- `workshop-chat-frontend` (existente): thumbnails viram hyperlinks expandíveis em vez de imagens enfileiradas.

## Impact

- `backend/app/api/v1/endpoints/chat.py` (HTML/JS): dropdowns + modal de imagem.
- Novo endpoint (ou extensão de `documents`/`vehicles`): listar gerações e sistemas com manuais disponíveis.
- A `ChatCitation` já expõe `document_id`/`page_number` para montar a URL do thumbnail; a mudança é só de apresentação.
- Não altera o pipeline RAG nem os schemas de resposta.