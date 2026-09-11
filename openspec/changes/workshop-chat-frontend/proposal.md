## Why

O projeto é referenciado por dois nomes: o histórico "helpMec" (presente no HTML do chat, no `SYSTEM_PROMPT`, no `openspec/config.yaml` e na documentação) e "TorqueAI" (parent do repositório e pasta). Essa dualidade confunde acessos, logs e a identidade do produto. Ao mesmo tempo, a página de chat é um único bloco HTML embutido no `backend/app/api/v1/endpoints/chat.py` com um visual genérico (serif, verde/marrom) que não reflete o domínio automotivo nem a marca.

## What Changes

- Renomeia a identidade visível do produto de "helpMec" para "TorqueAI" no HTML do chat, no `SYSTEM_PROMPT`, no `openspec/config.yaml` e na documentação.
- Refatora o HTML do chat para um visual moderno com temática de oficina (dark industrial, tipografia técnica, acentos de "ferramenta"/torque), mantendo a mesma API e comportamento funcional.
- Mantém `PROJECT_NAME` (usado no healthcheck e título da API) coerente: passa a exibir "TorqueAI" (ou "TorqueAI — Assistente Técnico Automotivo") sem quebrar os testes existentes.

## Capabilities

### New Capabilities

- `workshop-chat-frontend`: interface web do chat com identidade visual moderna e temática de oficina, servida sem build de frontend separado.

### Modified Capabilities

- `grounded-automotive-prompting` (existente): ajusta a identidade de marca no prompt de sistema (helpMec → TorqueAI).

## Impact

- `backend/app/api/v1/endpoints/chat.py` (bloco `_CHAT_PAGE`): todo o HTML/CSS/JS da página.
- `backend/app/agents/prompt.py` (`SYSTEM_PROMPT`): menção à marca.
- `openspec/config.yaml`, `README.md`, `AGENTS.md`, `docs/PROJECT_STATUS.md`: referências textuais a "helpMec".
- Testes: `backend/tests/test_chat.py` verifica o texto "Assistente de oficina" — precisa permanecer ou ser atualizado junto; `test_health.py` verifica `project == "Automotive AI Agent"`, que pode mudar para "TorqueAI".
- Não altera os endpoints, o fluxo RAG nem o formato das respostas da API.