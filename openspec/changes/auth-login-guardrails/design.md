## Context

A aplicação é um monólito FastAPI sem autenticação. O chat (HTML embutido), a consulta RAG (`/chat/messages`) e a ingestão (`/ingestion/start`) são públicos. Não há modelo de usuário nem biblioteca de auth no `requirements.txt` (apenas stdlib + pydantic + sqlalchemy + httpx + qdrant).

## Goals / Non-Goals

**Goals:**
- Proteger o chat e a ingestão atrás de login com credencial única de admin.
- Usar apenas o que já está disponível (stdlib `hashlib`/`secrets`/`hmac`), sem novos pacotes.
- Sessão opaca em cookie HttpOnly/SameSite.
- Guardrails de IA reforçados (zero-alucinação, recusa sem evidência).

**Non-Goals:**
- Não implementar OAuth2/JWT multi-usuário nem RBAC completo (fora de escopo).
- Não migrar para um store de sessão externo (Redis) — manter em memória como o JobTracker atual.

## Decisions

### Decision 1: Sessão opaca + cookie HttpOnly (em vez de JWT)
- **Chosen Approach**: token aleatório (`secrets.token_urlsafe`), store em memória de hash do token → sessão, cookie `HttpOnly; SameSite=Lax; Path=/`.
- **Rationale**: sem dependência nova, sem assinatura JWT para gerenciar; revogação trivial (remover do store).
- **Alternative Rejected**: JWT (exige lib de assinatura e dificulta revogação imediata); Basic Auth por header (inviável para o frontend HTML).

### Decision 2: Senha PBKDF2 em tempo constante
- **Chosen Approach**: `hashlib.pbkdf2_hmac("sha256", password, salt, iterações)` com `hmac.compare_digest`.
- **Rationale**: padrão, seguro, só stdlib.
- **Alternative Rejected**: senha em texto puro (inaceitável); bcrypt (exige `bcrypt`).

### Decision 3: Credencial via env
- **Chosen Approach**: `ADMIN_USERNAME`/`ADMIN_PASSWORD` no `.env`; a senha é hasheada em memória no boot.
- **Rationale**: simples, e já existe o padrão de config por env.
- **Alternative Rejected**: seed de usuário no Postgres (mais partes móveis sem ganho aqui).

## Risks / Trade-offs

- **[Risk]** Sessões em memória se perdem a cada restart.
  - **Mitigation**: aceitável (mesmo trade-off do JobTracker); documentar.
- **[Risk]** `SECRET_KEY` default inseguro já existe.
  - **Mitigation**: instruir troca em produção; usar a key para derivar salt quando disponível.
- **[Risk]** Rate limiting rudimentar pode ser contornado.
  - **Mitigation**: mitigação básica de força bruta (backoff), suficiente para o escopo.

## Migration Plan

1. Adicionar `security.py` + `auth_service.py` + endpoints de auth.
2. Adicionar `require_auth` e proteger as rotas.
3. Atualizar o frontend de chat para redirecionar ao login quando 401.
4. Reforçar guardrails no prompt.
5. Testar e validar.