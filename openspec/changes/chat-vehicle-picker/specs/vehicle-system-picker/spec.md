## Purpose

Define a experiência de seleção de veículo/geração e sistema no chat via dropdowns populados pelo catálogo, e a apresentação das fontes de resposta como hyperlinks que expandem a imagem da página para leitura.

## ADDED Requirements

### Requirement: Vehicle and System Dropdowns
O chat SHALL apresentar seletores (dropdowns) para Geração e Sistema populados a partir dos dados disponíveis no catálogo, em substituição a campos de texto livre.

#### Scenario: Options Populated From Catalog
- **WHEN** a página do chat é carregada
- **THEN** os dropdowns de Geração e Sistema são preenchidos com as opções existentes (incluindo uma opção "Todos" que não aplica filtro).

#### Scenario: Filtering Still Works
- **WHEN** o usuário seleciona geração/sistema e envia uma pergunta
- **THEN** o `POST /api/v1/chat/messages` envia `generation_code`/`system` correspondentes e a resposta é filtrada como antes.

### Requirement: Expandable Source Thumbnails
As fontes citadas SHALL ser apresentadas como hyperlinks compactos; ao clicar, a miniatura da página correspondente deve expandir para leitura do conteúdo.

#### Scenario: Click Expands Image
- **WHEN** o usuário clica no hyperlink de uma citação
- **THEN** um modal (ou nova aba) exibe a imagem ampliada da página da fonte, permitindo leitura do conteúdo original.

#### Scenario: Compact Layout
- **WHEN** uma resposta tem múltiplas citações
- **THEN** os hyperlinks ficam dispostos de forma compacta (não enfileirados como imagens grandes), mantendo a resposta legível.