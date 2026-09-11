## Purpose

Define a autenticação e a proteção das rotas operacionais do TorqueAI, e os guardrails da IA que impedem alucinação e respostas sem evidência.

## ADDED Requirements

### Requirement: Login Required for Chat and Ingestion
O acesso ao chat e aos endpoints de ingestão SHALL exigir autenticação; usuários não autenticados são redirecionados/negados.

#### Scenario: Unauthenticated Access Denied
- **WHEN** uma requisição sem sessão válida tenta acessar `/api/v1/chat/`, `/api/v1/chat/messages` ou `/api/v1/ingestion/*`
- **THEN** a API retorna HTTP 401 (ou redireciona à página de login para navegador).

#### Scenario: Login Grants Access
- **WHEN** o usuário envia credenciais corretas para `POST /api/v1/auth/login`
- **THEN** recebe um cookie de sessão HttpOnly e passa a acessar as rotas protegidas.

#### Scenario: Logout Revokes Session
- **WHEN** o usuário chama `POST /api/v1/auth/logout`
- **THEN** a sessão é invalidada e o cookie é limpo; acessos subsequentes são negados.

### Requirement: Password and Session Hardening
As credenciais e sessões SHALL usar hashing e tokens não previsíveis.

#### Scenario: Password Is Hashed
- **WHEN** a senha é armazenada/verificada
- **THEN** nunca é comparada em texto puro; usa PBKDF2 e comparação em tempo constante.

#### Scenario: Session Token Is Unpredictable
- **WHEN** uma sessão é criada
- **THEN** o token é gerado com `secrets` (entropia criptográfica) e o cookie é `HttpOnly; SameSite=Lax`.

### Requirement: AI Guardrails
O assistente SHALL recusar afirmar dados técnicos (torques, DTC, procedimentos) sem evidência nos manuais, e SHALL sanitizar a entrada.

#### Scenario: Refuses Without Evidence
- **WHEN** a pergunta não tem evidência suficiente recuperada
- **THEN** o assistente responde explicitamente que não é possível confirmar, sem inventar valores.

#### Scenario: Input Is Validated
- **WHEN** a pergunta excede limites ou contém payload malformado
- **THEN** a API rejeita com HTTP 422 sem processar.