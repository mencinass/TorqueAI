## 1. Identidade / Marca

- [x] 1.1 Substituir "helpMec" por "TorqueAI" no HTML do chat (`backend/app/api/v1/endpoints/chat.py`): `<title>`, `<h1>` e qualquer texto visível.
- [x] 1.2 Atualizar o `SYSTEM_PROMPT` em `backend/app/agents/prompt.py` para a nova marca.
- [x] 1.3 Atualizar `openspec/config.yaml` (contexto do projeto) e as referências em `README.md`, `AGENTS.md` e `docs/PROJECT_STATUS.md`.
- [x] 1.4 Decidir e aplicar o valor de `PROJECT_NAME` ("TorqueAI") e ajustar `backend/tests/test_health.py` que valida `project`, além do `.env`, `.env.example` e `docker-compose.yml`.

## 2. Visual moderno com temática de oficina

- [x] 2.1 Reescrever o CSS do `_CHAT_PAGE`: tema escuro/industrial (grafite, aço, âmbar/laranja de destaque), tipografia técnica monoespaçada para dados e sans-serif para texto, cantos arredondados moderados, sombras suaves.
- [x] 2.2 Adicionar identidade visual de oficina: logotipo/monograma "TorqueAI" com acento de torquímetro (SVG inline), header com indicação de sistema/geração ativa.
- [x] 2.3 Estilizar os balões de mensagem (usuário vs. assistente), a barra de fontes/citações e o estado "sem evidência" como badges visuais.
- [x] 2.4 Tornar responsivo (mobile-first) e acessível: contraste adequado, foco visível, `aria-live` nas mensagens, sem confiar apenas em cor.

## 3. Comportamento (sem regressão)

- [x] 3.1 Manter o mesmo fluxo JS: `fetch POST /api/v1/chat/messages`, `session_id`, filtros `generation_code`/`system`, tratamento de erro que restaura a pergunta.
- [x] 3.2 Manter o endpoint `GET /api/v1/chat/` servindo a página via `HTMLResponse` sem build step.
- [x] 3.3 Atualizar/ajustar `backend/tests/test_chat.py` (assert de "Assistente de oficina") conforme o novo texto do header, mantendo um assert que valide a página renderizada.

## 4. Validação

- [x] 4.1 Executar `pytest` e garantir que todos os testes passam.
- [x] 4.2 Validar visualmente a página (hot reload / subir stack) e confirmar o fluxo de pergunta/resposta com fontes.
- [x] 4.3 Executar `openspec validate --changes --json` e revisar os artefatos antes de arquivar.