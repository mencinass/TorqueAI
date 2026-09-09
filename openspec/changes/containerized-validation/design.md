## Context

O projeto já possui um `docker-compose.yml` com PostgreSQL, Qdrant e backend, healthchecks básicos e volumes nomeados. O `Makefile` detecta alguns modos de Compose e o `run.ps1` seleciona comandos no Windows, mas os contratos de readiness, diagnóstico e validação ainda não estão formalizados.

## Goals / Non-Goals

**Goals:**
- Manter um único arquivo Compose compatível com Docker e Podman.
- Garantir que comandos de teste e healthcheck sejam reproduzíveis dentro do ambiente containerizado.
- Preservar dados por padrão e tornar limpeza destrutiva explícita.
- Fornecer mensagens úteis para falhas de runtime em Windows e Linux/macOS.

**Non-Goals:**
- Migrar para Kubernetes ou outro orquestrador.
- Criar imagens separadas por ambiente além do backend atual.
- Exigir Ollama como serviço obrigatório do Compose nesta mudança.
- Alterar contratos funcionais da API ou do RAG.

## Decisions

### Decision 1: Um arquivo Compose compartilhado
- **Chosen Approach**: Continuar com `docker-compose.yml` como fonte única para Docker Compose e Podman Compose.
- **Rationale**: Evita divergência de portas, redes, healthchecks e variáveis entre runtimes.
- **Alternative Rejected**: Arquivos separados, pois duplicariam configuração e aumentariam drift.

### Decision 2: Readiness por healthcheck e dependências condicionais
- **Chosen Approach**: Usar healthchecks reais para PostgreSQL, Qdrant e backend, com dependências condicionadas ao estado saudável.
- **Rationale**: `container_started` não garante que o serviço esteja pronto para conexões assíncronas.
- **Alternative Rejected**: Delays fixos, pois variam conforme máquina e carga e causam flakiness.

### Decision 3: Detecção de runtime com override explícito
- **Chosen Approach**: Manter autodetecção em `Makefile`/PowerShell e permitir configurar o comando Compose por variável (`COMPOSE` ou equivalente).
- **Rationale**: Suporta ambientes com Docker, Podman Compose e `podman-compose`, além de CI controlado.
- **Alternative Rejected**: Fixar Docker ou Podman, pois excluiria parte dos ambientes suportados.

### Decision 4: Testes dentro do container
- **Chosen Approach**: O comando de teste executa `pytest` via `compose exec backend`, após readiness do stack.
- **Rationale**: Valida a imagem, dependências, rede e runtime que serão usados na execução real.
- **Alternative Rejected**: Testar apenas no host, pois não detecta falhas de empacotamento ou conectividade interna.

## Risks / Trade-offs

- **[Risk]** Podman Compose pode ter diferenças de suporte em `depends_on` e healthchecks.
  - **Mitigation**: Validar ambos os comandos, documentar versões suportadas e manter health endpoint como check final.
- **[Risk]** Volumes antigos podem conter schema ou dados incompatíveis.
  - **Mitigation**: Documentar limpeza explícita com remoção de volumes e preservar o comportamento não destrutivo por padrão.
- **[Risk]** O host não possui Docker ou Podman ativo.
  - **Mitigation**: Falhar cedo com diagnóstico do runtime, sem simular sucesso.

## Migration Plan

1. Ajustar Compose, healthchecks e comandos auxiliares mantendo nomes de serviços e portas atuais.
2. Executar build e subida com Docker Compose e Podman Compose em ambientes disponíveis.
3. Rodar healthcheck e testes dentro do backend containerizado.
4. Atualizar a documentação com os fluxos Windows, Linux/macOS e CI.
5. Em caso de regressão, reverter apenas os ajustes de orquestração; os dados persistidos permanecem nos volumes.
