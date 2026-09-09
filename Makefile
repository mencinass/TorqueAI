# ==============================================================================
# Automotive AI Agent - Makefile
# Automation commands for Podman / Docker on Linux (Pop!_OS) & macOS
# ==============================================================================

# Automatically detect podman compose or docker compose
COMPOSE ?= $(shell if podman compose version >/dev/null 2>&1; then echo "podman compose"; elif command -v podman-compose >/dev/null 2>&1; then echo "podman-compose"; else echo "docker compose"; fi)

.PHONY: help up down clean restart build logs logs-backend test lint health validate ps shell

help:
	@echo "Automotive AI Agent - Comandos Disponíveis:"
	@echo "  make up            - Inicia todos os serviços em background"
	@echo "  make down          - Para e remove os contêineres"
	@echo "  make clean         - Para e remove contêineres e volumes (destrutivo)"
	@echo "  make restart       - Reinicia os serviços"
	@echo "  make build         - Reconstrói a imagem do backend"
	@echo "  make ps            - Exibe status dos contêineres"
	@echo "  make logs          - Exibe logs de todos os serviços"
	@echo "  make logs-backend  - Exibe logs do backend FastAPI"
	@echo "  make test          - Executa os testes automatizados (pytest)"
	@echo "  make lint          - Executa análise estática com ruff"
	@echo "  make health        - Testa o endpoint de saúde do sistema"
	@echo "  make validate      - Sobe o stack, valida a saúde e executa os testes"
	@echo "  make shell         - Abre um terminal interativo dentro do contêiner backend"

up:
	@echo "==> Iniciando serviços com $(COMPOSE)..."
	$(COMPOSE) up -d

down:
	@echo "==> Parando serviços..."
	$(COMPOSE) down

clean:
	@echo "==> Removendo serviços e volumes (ação destrutiva)..."
	$(COMPOSE) down -v

restart: down up

build:
	@echo "==> Reconstruindo imagens..."
	$(COMPOSE) build

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

logs-backend:
	$(COMPOSE) logs -f backend

test:
	@echo "==> Executando testes automatizados..."
	$(COMPOSE) exec backend pytest -v

validate: up health test

lint:
	@echo "==> Executando verificação de código..."
	$(COMPOSE) exec backend ruff check app tests

health:
	@echo "==> Verificando saúde dos serviços..."
	@curl --fail --silent --show-error http://localhost:8000/health || curl --fail --silent --show-error http://127.0.0.1:8000/health

specs:
	@echo "==> Listando especificações do OpenSpec..."
	@openspec list --specs

spec-validate:
	@echo "==> Validando especificações do OpenSpec..."
	@openspec validate --specs

shell:
	$(COMPOSE) exec backend /bin/bash

