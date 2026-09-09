## Purpose

Padroniza validações executadas sobre o stack containerizado, incluindo healthcheck da API, testes automatizados, logs diagnósticos e encerramento controlado para desenvolvimento e CI.

## ADDED Requirements

### Requirement: Containerized Test Command
O sistema SHALL fornecer um comando documentado que execute toda a suíte de testes dentro do container `backend` usando as dependências instaladas na imagem.

#### Scenario: Run Tests in Backend Container
- **WHEN** o operador executa o comando de teste do projeto com o stack ativo
- **THEN** o comando executa `pytest` dentro do backend, retorna o código de saída original e falha se qualquer teste falhar.

### Requirement: Health Validation
O sistema SHALL fornecer um comando de healthcheck que consulte `GET /health` após a subida e diferencie resposta saudável de serviço indisponível.

#### Scenario: Healthy Stack
- **WHEN** backend, PostgreSQL e Qdrant estão prontos e o operador executa a validação de saúde
- **THEN** o comando retorna sucesso e confirma o estado HTTP saudável da API.

#### Scenario: Unhealthy Stack
- **WHEN** a API não responde ou retorna HTTP 503
- **THEN** o comando retorna código de falha e informa que o stack não está pronto, sem mascarar o erro.

### Requirement: Cross-Platform Compose Commands
O sistema SHALL disponibilizar comandos equivalentes para subir, parar, reconstruir, consultar status e visualizar logs em PowerShell e Makefile.

#### Scenario: Equivalent Developer Workflows
- **WHEN** o operador usa `run.ps1` no Windows ou `make` em Linux/macOS
- **THEN** os comandos correspondentes controlam o mesmo arquivo Compose e produzem o mesmo resultado operacional.

### Requirement: Clean Shutdown
O sistema SHALL permitir parar o stack sem remover volumes por padrão e SHALL oferecer uma ação explícita para limpeza destrutiva dos dados.

#### Scenario: Stop Without Data Loss
- **WHEN** o operador executa o comando padrão de parada
- **THEN** os containers são removidos ou parados, mas os volumes nomeados permanecem.
