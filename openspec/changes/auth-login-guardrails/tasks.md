## 1. Autenticação básica

- [x] 1.1 Criar `app/core/security.py` com hash/verificação de senha (PBKDF2-HMAC-SHA256, salt aleatório) e comparação em tempo constante.
- [x] 1.2 Criar `app/services/auth_service.py` com login/logout, sessões opacas em memória e TTL.
- [x] 1.3 Adicionar credenciais no `config.py`/`.env` (`ADMIN_USERNAME`, `ADMIN_PASSWORD`).

## 2. Endpoints de auth

- [x] 2.1 `POST /api/v1/auth/login` valida credencial, cria sessão e seta cookie HttpOnly/SameSite=Lax.
- [x] 2.2 `POST /api/v1/auth/logout` revoga a sessão e limpa o cookie.
- [x] 2.3 `GET /api/v1/auth/me` retorna se o usuário está autenticado.

## 3. Proteção das rotas

- [x] 3.1 Nova dependência `require_auth` em `app/api/deps.py` que valida o cookie/sessão.
- [x] 3.2 Aplicar `require_auth` ao router de chat (página + messages) e ao router de ingestão.
- [x] 3.3 Servir página de login e redirecionar usuário não autenticado (401 → frontend redireciona).

## 4. Hardening

- [x] 4.1 Rate limiting leve no login (lockout após N falhas).
- [x] 4.2 Sessão com TTL e revogação no logout; token não previsível (`secrets`).
- [x] 4.3 Cookie com `HttpOnly`, `SameSite=Lax`, e `Secure` quando não-debug.

## 5. Guardrails da IA

- [x] 5.1 Reforçar o `SYSTEM_PROMPT` contra alucinação e exigir recusa explícita sem evidência.
- [x] 5.2 Sanitizar/validar a pergunta (limites existentes de `ChatRequest` mantidos).
- [x] 5.3 Instruções anti prompt-injection e recusa de escopo fora de oficina no prompt.

## 6. Validação

- [x] 6.1 `pytest` verde (59 testes), incluindo novos testes de auth e guardrails.
- [x] 6.2 Validar manualmente login → chat → logout no navegador (via curl: 401 sem auth, 200 com cookie, 401 após logout).
- [x] 6.3 `openspec validate --changes --json` (7 changes válidas).