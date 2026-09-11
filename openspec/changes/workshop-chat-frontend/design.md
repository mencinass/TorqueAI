## Context

A página de chat é um único bloco HTML (`_CHAT_PAGE`) embutido em `backend/app/api/v1/endpoints/chat.py`, servido diretamente por `HTMLResponse`. Não há framework de frontend, build step nem assets estáticos. O `SYSTEM_PROMPT` em `agents/prompt.py` e o HTML referenciam "helpMec", enquanto a pasta do repositório e a identidade desejada são "TorqueAI".

## Goals / Non-Goals

**Goals:**
- Unificar a identidade visível em "TorqueAI".
- Dar à página de chat um visual moderno, escuro/industrial, coerente com oficina mecânica.
- Manter a página autocontida (sem build, sem CDN obrigatória) e sem mudar a API.

**Non-Goals:**
- Introduzir framework frontend (React/Vue) ou pipeline de build.
- Adicionar OCR, autenticação ou novas funcionalidades de chat.
- Alterar os contratos da API (`POST /messages`, schemas de resposta) ou o fluxo RAG.

## Decisions

### Decision 1: Página autocontida no servidor
- **Chosen Approach**: manter o HTML embutido em `chat.py`, agora reescrito com CSS moderno.
- **Rationale**: zero infraestrutura extra, deploy simples, endpoint continua sendo único ponto de serviço.
- **Alternative Rejected**: migrar para assets estáticos separados + framework, por custo/benefício desproporcional para uma tela única.

### Decision 2: Tema visual escuro/industrial ("oficina")
- **Chosen Approach**: paleta grafite/aço com destaque âmbar (torque/tomada), tipografia técnica, badges de fonte.
- **Rationale**: comunica o domínio automotivo e diferencia mensagens/citações/estado de forma clara.
- **Alternative Rejected**: manter o tema claro serif atual, por não refletir a marca nem o domínio.

### Decision 3: Marca "TorqueAI" sem nome interno conflitante
- **Chosen Approach**: "TorqueAI" como identidade de produto; `PROJECT_NAME` passa a refletir a marca.
- **Rationale**: elimina a dualidade helpMec/TorqueAI em logs, títulos e testes.
- **Alternative Rejected**: manter "Automotive AI Agent" interno e só mudar o visível — deixaria a dualidade persistente.

## Risks / Trade-offs

- **[Risk]** Mudar `PROJECT_NAME` quebra `test_health.py` e pode impactar o título do `/docs`.
  - **Mitigation**: atualizar o teste junto e revisar todos os usos de `settings.PROJECT_NAME`.
- **[Risk]** Visual escuro pode reduzir legibilidade se mal calibrado.
  - **Mitigation**: validar contraste (WCAG AA) e `aria-live` para acessibilidade.
- **[Risk]** Regressão no fluxo JS ao reescrever o bloco.
  - **Mitigation**: preservar a lógica de `fetch`/`session_id`/filtros e manter teste que renderiza a página.

## Migration Plan

1. Reescrever `_CHAT_PAGE` com o novo visual mantendo a estrutura semântica (aside de filtros + area de mensagens + composer).
2. Atualizar `SYSTEM_PROMPT` e textos de marca.
3. Alinhar `PROJECT_NAME` e os testes afetados.
4. Atualizar documentação.
5. Validar com `pytest` e `openspec validate`; em caso de regressão, reverter o bloco HTML e os textos mantendo a API intacta.