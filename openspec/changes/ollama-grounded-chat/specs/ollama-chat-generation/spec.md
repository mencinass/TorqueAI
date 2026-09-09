## Purpose

Gera respostas conversacionais locais para dúvidas automotivas usando o Ollama, com o contexto recuperado do RAG como base obrigatória e sem depender de provedores externos de linguagem.

## ADDED Requirements

### Requirement: Local Ollama Generation
O sistema SHALL enviar uma solicitação de geração ao Ollama local usando uma configuração explícita de URL e modelo de chat, incorporando a pergunta e o contexto recuperado do RAG.

#### Scenario: Generate Answer from Retrieved Context
- **WHEN** uma pergunta válida possui trechos relevantes recuperados do manual
- **THEN** o sistema envia ao Ollama a pergunta, o contexto delimitado e as instruções automotivas, retornando o texto gerado junto às fontes originais.

### Requirement: Ollama Configuration
O sistema SHALL permitir configurar a URL base, o modelo, o timeout e os parâmetros de geração do Ollama por configuração da aplicação, com valores padrão adequados para execução local.

#### Scenario: Use Local Defaults
- **WHEN** nenhuma configuração específica de Ollama é fornecida
- **THEN** o sistema usa a URL local configurada por padrão, um modelo de chat definido pela aplicação e um timeout finito, sem bloquear indefinidamente a requisição.

### Requirement: Provider Failure Handling
O sistema SHALL retornar uma resposta de serviço indisponível quando o Ollama não puder ser alcançado ou responder com erro, sem expor credenciais, prompts internos ou detalhes sensíveis da infraestrutura.

#### Scenario: Ollama Is Unavailable
- **WHEN** a chamada ao Ollama falha por timeout, conexão recusada ou resposta HTTP de erro
- **THEN** o endpoint retorna HTTP 503 com uma mensagem genérica orientando o usuário a verificar o serviço local.
