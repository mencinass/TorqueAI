## Why

O chat e todos os endpoints — incluindo a consulta RAG e a ingestão — estão expostos sem autenticação. Qualquer pessoa com acesso à rede pode usar o assistente e disparar jobs de ingestão. Não há proteção da interface, nem controle de quem acessa o conhecimento técnico indexado, nem guardrails explícitos sobre o que a IA pode afirmar.

## What Changes

- Adiciona uma **página de login** e torna o acesso ao chat e aos endpoints de consulta/ingestão condicionado a autenticação.
- Implementa **sessões autenticadas** via cookie HttpOnly/SameSite, com um usuário administrativo configurado por variáveis de ambiente.
- Adiciona **camadas de segurança** no código: hashing de senha (PBKDF2), token de sessão opaco (não previsível), proteção contra força bruta (delay/limite), e rate limiting básico no login.
- Reforça **guardrails da IA**: instruções de sistema reforçadas contra alucinação/DTC, e validação/sanitização da entrada da consulta.

## Capabilities

### New Capabilities

- `authnz-login`: autenticação por credencial + sessão, protegendo as rotas operacionais.
- `ai-guardrails`: restrições e sanitização aplicadas à entrada/saída do assistente.

### Modified Capabilities

- `agent-chat-frontend` / `workshop-chat-frontend` (existentes): o chat passa a exigir login.
- `document-ingestion` (existente): o endpoint de ingestão passa a exigir autenticação.

## Impact

- Novos arquivos: `app/core/security.py`, `app/api/v1/endpoints/auth.py`, `app/services/auth_service.py`, página de login HTML.
- `app/api/deps.py`: nova dependência `require_auth`.
- `app/main.py`: wiring de middleware/sessão.
- `config.py` / `.env`: `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` (ou seed de senha), `SESSION_TTL`.
- Rota de chat e ingestão passam a receber `require_auth`.
- Testes novos cobrindo login/logout, proteção de rota e guardrails.