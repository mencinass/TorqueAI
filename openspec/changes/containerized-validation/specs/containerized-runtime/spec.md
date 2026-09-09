## Purpose

Define uma execução reproduzível do helpMec em containers, permitindo iniciar o backend, PostgreSQL e Qdrant com Docker Compose ou Podman Compose usando o mesmo contrato operacional.

## ADDED Requirements

### Requirement: Compose-Compatible Stack
O sistema SHALL subir os serviços `backend`, `postgres` e `qdrant` usando Docker Compose v2, `podman compose` ou `podman-compose`, sem exigir alteração manual no arquivo de composição.

#### Scenario: Start with Docker Compose
- **WHEN** o operador executa `docker compose up -d --build` na raiz do projeto
- **THEN** os três serviços são criados na rede do projeto e o backend fica acessível em `http://localhost:8000`.

#### Scenario: Start with Podman Compose
- **WHEN** o operador executa `podman compose up -d --build` na raiz do projeto
- **THEN** os mesmos serviços, portas, volumes e variáveis de ambiente são provisionados sem mudanças no código da aplicação.

### Requirement: Service Readiness Ordering
O sistema SHALL aguardar PostgreSQL e Qdrant em estado saudável antes de considerar o backend pronto para testes ou uso.

#### Scenario: Dependencies Are Not Ready
- **WHEN** PostgreSQL ou Qdrant ainda não responde ao healthcheck
- **THEN** o backend não deve ser anunciado como pronto e a composição deve continuar tentando dentro do limite configurado.

### Requirement: Persistent Development Data
O sistema SHALL persistir os dados do PostgreSQL e Qdrant em volumes nomeados durante reinicializações normais do stack.

#### Scenario: Restart Preserves Data
- **WHEN** o operador executa `compose down` seguido de `compose up -d` sem remover volumes
- **THEN** os dados persistidos continuam disponíveis para o backend.

### Requirement: Runtime Diagnostics
O sistema SHALL apresentar uma mensagem operacional clara quando o runtime escolhido, o daemon Docker ou a máquina Podman não estiver disponível.

#### Scenario: Container Runtime Unavailable
- **WHEN** o operador executa o comando de inicialização sem um runtime funcional
- **THEN** o helper retorna falha identificável e orienta a iniciar ou conectar o Docker Engine ou a Podman Machine.
