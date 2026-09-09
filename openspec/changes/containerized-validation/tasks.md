## 1. Compose Stack

- [ ] 1.1 Revisar e ajustar `docker-compose.yml` para Docker Compose v2 e Podman Compose, verificando `docker compose config` e `podman compose config` (Podman validado; Docker pendente porque não está instalado)
- [x] 1.2 Garantir healthchecks funcionais para PostgreSQL, Qdrant e backend, verificando que dependências aguardam estado saudável
- [x] 1.3 Validar volumes nomeados, rede interna, portas e variáveis de ambiente, verificando persistência após reinicialização sem remoção de volumes

## 2. Cross-Platform Commands

- [x] 2.1 Atualizar `Makefile` com comandos equivalentes de up, down, build, logs, status, health e test, verificando a cadeia equivalente no helper e no Podman Compose
- [x] 2.2 Atualizar `run.ps1` para autodetectar Docker/Podman e diagnosticar daemon ou Podman Machine indisponível, verificando execução no Windows
- [x] 2.3 Adicionar ação explícita de limpeza destrutiva de volumes, verificando que o comando padrão de parada não remove dados

## 3. Containerized Validation

- [x] 3.1 Implementar o fluxo de healthcheck pós-subida e verificar sucesso HTTP 200; o cenário de falha permanece coberto pelo código de retorno do helper
- [ ] 3.2 Executar a suíte completa com `compose exec backend pytest` em Docker Compose, verificando código de saída e logs de falha
- [x] 3.3 Executar a suíte completa com `podman compose exec backend pytest` ou `podman-compose exec backend pytest`, verificando equivalência do resultado
- [x] 3.4 Validar build limpo do backend e importação da aplicação dentro do container, verificando que a aplicação responde no healthcheck

## 4. Documentation & CI

- [x] 4.1 Documentar pré-requisitos, comandos Docker Compose e Podman Compose, troubleshooting e remoção de volumes no README
- [x] 4.2 Adicionar um fluxo de validação automatizável para CI sem exigir Ollama externo, verificando health, testes e encerramento
- [x] 4.3 Executar `openspec validate --changes --json` e revisar todos os artefatos antes de arquivar a mudança
