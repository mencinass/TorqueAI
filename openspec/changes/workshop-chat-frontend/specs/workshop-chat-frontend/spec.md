## Purpose

Define a identidade visual e de marca da página de chat do TorqueAI: interface web servida pelo backend com temática de oficina, coerente com a marca, sem build de frontend separado e sem alterar o contrato da API.

## ADDED Requirements

### Requirement: Modern Workshop-Themed Chat UI
A página de chat SHALL apresentar um visual moderno com temática de oficina (tema escuro/industrial, tipografia técnica, destaque de cor coerente com a marca TorqueAI).

#### Scenario: Renders Workshop-Themed Chat
- **WHEN** o usuário abre `GET /api/v1/chat/`
- **THEN** a página exibe o título "TorqueAI", um cabeçalho com o assistente de oficina e estilos de tema escuro/industrial, sem depender de nenhum build ou CDN obrigatória.

#### Scenario: Responsive and Accessible
- **WHEN** a página é aberta em viewport estreito ou com leitor de tela
- **THEN** o layout se adapta (mobile-first) e as mensagens são anunciadas via `aria-live`, com contraste de texto suficiente.

### Requirement: Brand Identity Consistency
O produto SHALL se identificar como "TorqueAI" em todos os pontos visíveis e de sistema, eliminando referências residuais à marca anterior "helpMec".

#### Scenario: No Legacy Brand Left
- **WHEN** um operador inspeciona o HTML do chat, o `SYSTEM_PROMPT`, o contexto do OpenSpec e a documentação
- **THEN** nenhuma referência a "helpMec" permanece; a identidade exibida é "TorqueAI".

### Requirement: Chat Flow Unchanged
A refatoração visual SHALL preservar o fluxo funcional de conversa existente (pergunta, filtros de geração/sistema, citações e estado "sem evidência").

#### Scenario: Conversation Still Works
- **WHEN** o usuário envia uma pergunta pela página refatorada
- **THEN** a página faz `POST /api/v1/chat/messages` com `session_id`, `generation_code` e `system`, exibe a resposta com citações e trata erro restaurando a pergunta, exatamente como antes.