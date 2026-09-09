## Why

O projeto já possui um `docker-compose.yml`, comandos no `Makefile` e um helper PowerShell, mas Docker Compose e Podman Compose ainda não têm um contrato único de execução e validação. Isso dificulta reproduzir o ambiente, detectar serviços não prontos e executar os testes de integração de forma confiável em Windows, Linux e CI.

## What Changes

- Padroniza a subida do stack com Docker Compose e Podman Compose usando o mesmo arquivo de composição.
- Define comandos equivalentes para build, start, stop, logs, health check e testes.
- Garante que PostgreSQL e Qdrant estejam prontos antes do backend iniciar os testes e validações.
- Executa a suíte de testes dentro do container do backend com dependências reproduzíveis.
- Melhora mensagens de diagnóstico quando Docker, Podman, a máquina Podman ou o daemon não estiverem disponíveis.
- Documenta o fluxo de validação local e o fluxo recomendado para CI.

## Capabilities

### New Capabilities

- `containerized-runtime`: execução reproduzível do backend, PostgreSQL e Qdrant por Docker Compose ou Podman Compose.
- `compose-validation`: comandos e checks para validar readiness, saúde da API, testes automatizados e encerramento limpo do stack.

### Modified Capabilities

<!-- Nenhuma capability principal existente tem requisitos alterados; esta mudança cria o contrato de execução e validação. -->

## Impact

- Afeta `docker-compose.yml`, `Makefile`, `run.ps1`, `backend/Dockerfile` e a documentação do projeto.
- Pode exigir ajustes nos healthchecks, `depends_on`, rede, volumes e variáveis de ambiente.
- Não altera o comportamento funcional da API quando executada fora dos containers.
- Deve manter compatibilidade com Docker Compose v2, `podman compose` e `podman-compose` quando disponíveis.
- A validação do chat com Ollama permanece opcional: o stack deve subir e testar com fallback/mock sem exigir um Ollama externo ativo.
