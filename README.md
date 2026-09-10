# Automotive AI Agent 🚗🔧

Sistema inteligente de assistência técnica automotiva baseado em Inteligência Artificial, RAG (*Retrieval-Augmented Generation*) e agentes autônomos para consulta de manuais de serviço, diagnóstico de falhas, especificações técnicas (torque, folgas, fluidos) e códigos OBD/DTC.

O estado operacional atual (Docker, Ollama, ingestão, troubleshooting) está documentado em [AGENTS.md](AGENTS.md), que é a fonte de verdade para o ambiente real. O arquivo [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) descreve uma sessão anterior (Windows + Podman) e pode estar desatualizado.

---

## 📌 Visão Geral do Projeto

O **Automotive AI Agent** foi concebido para auxiliar mecânicos, oficinas e entusiastas automotivos a encontrarem informações técnicas precisas diretamente nos manuais do fabricante, eliminando alucinações e citando sempre a fonte (manual, capítulo e página).

### Pilares Fundamentais:
1. **Python puro no núcleo**: Backend, conexões e agentes rodam em Python (sem SDKs C/C++ de LLM). A extração de PDF usa a ferramenta de sistema **poppler-utils** (`pdftotext`/`pdfinfo`) em subprocessos isolados, com timeout e limite de memória por página — escolha deliberada para que uma página problemática possa ser morta sem travar o processo.
2. **Padrão OpenSpec (Spec-Driven Development)**: Todas as especificações, capacidades e mudanças seguem rigorosamente o padrão OpenSpec com cenários observáveis WHEN / THEN.
3. **Confiabilidade Absoluta**: O sistema **não inventa dados técnicos nem torques**. Se a informação não constar nos documentos, o agente informa claramente a ausência.
4. **Rastreabilidade de Fontes**: Toda resposta técnica indica o documento, sistema e página de origem.
5. **Diferenciação Estrita**: Hipóteses de diagnóstico são explicitamente separadas de procedimentos oficiais do fabricante.
6. **Arquitetura Modular**: Monólito modular limpo, escalável e preparado para múltiplos modelos de veículos e provedores de IA.


## 🏗️ Arquitetura da Fase 1 — Fundação

A Fase 1 estabelece a infraestrutura essencial e o esqueleto do projeto:

```
Automotive AI Agent
├── Backend (FastAPI - Python 3.11)
│   ├── API assíncrona com Uvicorn
│   ├── Verificação de integridade (Health Check real)
│   ├── Modelos SQLAlchemy 2.0 (asyncpg)
│   ├── Pipeline RAG (extração PDF → chunking → embeddings → upsert)
│   └── Cliente Qdrant com suporte assíncrono
├── Banco Relacional (PostgreSQL 16)
│   └── Usuários, veículos, histórico de diagnósticos e metadados de documentos
├── Banco Vetorial (Qdrant)
│   └── Armazenamento de vetores de alta dimensão com filtros de metadados
└── Ollama (opcional, com GPU)
    └── Geração local de chat (llama3.2:3b) e embeddings (bge-m3)
```


## 📂 Estrutura do Repositório

```text
helpMec/
├── backend/
│   ├── app/
│   │   ├── api/                # Rotas da API e injeção de dependências
│   │   │   ├── v1/endpoints/   # Endpoints versionados (ex: health)
│   │   │   └── deps.py         # Injeção de sessão do banco e clientes
│   │   ├── core/               # Configurações Pydantic, logging estruturado e exceções
│   │   ├── database/           # Engine assíncrona SQLAlchemy e DeclarativeBase
│   │   ├── services/           # Serviços de conectividade (PostgreSQL e Qdrant)
│   │   ├── schemas/            # Schemas Pydantic de validação e serialização
│   │   ├── models/             # (Fase 2) Modelos relacionais ORM
│   │   ├── rag/                # (Fase 3/4) Chunking, embeddings e recuperação vetorial
│   │   ├── agents/             # (Fase 5/6) Orquestração de agentes e raciocínio técnico
│   │   ├── tools/              # Ferramentas do agente (DTC lookup, busca de manuais)
│   │   └── main.py             # Instanciação FastAPI e ciclo de vida (lifespan)
│   ├── tests/                  # Testes automatizados com pytest
│   ├── Dockerfile              # Imagem leve do backend (Python 3.11-slim)
│   ├── requirements.txt        # Dependências de produção
│   ├── requirements-dev.txt    # Dependências de teste e qualidade
│   └── .env.example            # Variáveis de ambiente de exemplo
├── service_guide/              # Manuais de serviço em PDF (MINI R56, MINI R53, Fiat 500)
├── openspec/                   # Especificações e capacidades no padrão OpenSpec
│   ├── config.yaml             # Configuração e regras de contexto do OpenSpec
│   └── specs/                  # Capacidades validadas (system-foundation, etc.)
├── .agents/                    # Skills e workflows do OpenSpec para o assistente AI
├── docker-compose.yml          # Orquestração do Backend, PostgreSQL e Qdrant
├── run.ps1                     # Script de automação PowerShell para Windows
├── Makefile                    # Automação de comandos para Linux / macOS
├── .env                        # Variáveis de ambiente ativas para desenvolvimento local
├── .gitignore                  # Arquivos ignorados pelo controle de versão
└── README.md                   # Documentação do projeto
```


## 🚀 Como Executar

O ambiente é compatível com **Linux**, **macOS** e **Windows**, com suporte a **Docker Compose** (principal) e **Podman** (compatível).

### 1. Pré-requisitos

- Docker Engine + Docker Compose v2 (`docker compose`), ou Podman + `podman-compose`.
- Para aceleração de GPU nos modelos locais: driver NVIDIA + `nvidia-container-toolkit` (opcional).

### 2. Inicialização no Windows (PowerShell)

No Windows, utilize o script `run.ps1`:

```powershell
.\run.ps1 up          # Iniciar todos os serviços em segundo plano
.\run.ps1 ps          # Ver status dos contêineres
.\run.ps1 health      # Testar o health check
.\run.ps1 logs        # Acompanhar logs em tempo real
.\run.ps1 test        # Executar os testes automatizados
.\run.ps1 down        # Parar os serviços
.\run.ps1 validate    # Subir, verificar saúde e executar testes
.\run.ps1 clean       # Remover também os volumes (destrutivo)
```


### 3. Inicialização no Linux / macOS (Makefile)

Em ambientes Linux ou macOS com `make`:

```bash
# Iniciar todos os serviços em segundo plano
make up

# Visualizar o status dos contêineres
make ps

# Executar o health check
make health

# Ver logs em tempo real
make logs

# Rodar os testes automatizados
make test

# Parar os serviços
make down

# Subir, verificar saúde e executar testes
make validate

# Remover também os volumes (destrutivo)
make clean
```


### 4. Inicialização Manual

#### Usando Podman:
```bash
podman compose up -d --build
```

#### Usando Docker:
```bash
docker compose up -d --build
```

Para validar o stack com Podman, use o mesmo arquivo Compose:

```bash
podman compose up -d --build
podman compose exec backend pytest -q
podman compose down
```

O comando padrão `down` não remove os volumes. Use `make clean` ou `.\run.ps1 clean` somente quando quiser apagar os dados locais.

Se a inicialização falhar, confirme que o Docker Engine está ativo ou que a Podman Machine está iniciada (`podman machine start`). O comando `validate` falha quando o healthcheck não retorna sucesso e exibe o erro do serviço.

### 5. Chat local com Ollama

O Ollama roda como um serviço do Compose (`ollama`), já configurado no `docker-compose.yml` com acesso à GPU (quando disponível). Por padrão, o backend usa:

- Chat: `llama3.2:3b` via `CHAT_PROVIDER=ollama`.
- Embeddings: `bge-m3` (dimensão 1024) via `EMBEDDING_PROVIDER=ollama`.

Baixe os modelos necessários no contêiner Ollama:

```bash
make ollama-pull        # baixa llama3.2:3b e bge-m3
```

As variáveis relevantes no `.env` são (defaults já alinhados com o Compose):

```env
CHAT_PROVIDER=ollama
CHAT_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://ollama:11434
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=1024
```

Também há providers alternativos para chat (`nvidia`, `extractive`) e embeddings (`openai`, `mock` para testes offline). Com a API em execução, abra `http://localhost:8000/api/v1/chat/`. O modelo recebe somente os trechos recuperados dos manuais; sem evidência suficiente, o chat não gera uma conclusão técnica.


## 📋 OpenSpec (Spec-Driven Development)

O projeto adota o **OpenSpec** para governar o ciclo de vida do desenvolvimento orientado a especificações. Todas as novas funcionalidades, modelos e comportamentos devem ser validados pelo OpenSpec antes e após a implementação.

### Comandos do OpenSpec:
```bash
# Listar especificações ativas
openspec list --specs
# ou no Windows PowerShell:
.\run.ps1 specs

# Validar conformidade de todas as especificações
openspec validate --specs
# ou no Windows PowerShell:
.\run.ps1 spec-validate

# Iniciar uma nova proposta de mudança
openspec new change <nome-da-mudanca>
```

As especificações ativas e validadas residem no diretório `openspec/specs/`.

## 🩺 Verificação e Endpoints

Após iniciar os contêineres:

| Serviço | URL / Porta | Descrição |
| :--- | :--- | :--- |
| **FastAPI Root Health** | `http://localhost:8000/health` | Status geral e verificação ativa do Postgres e Qdrant |
| **FastAPI v1 Health** | `http://localhost:8000/api/v1/health` | Endpoint versionado do health check |
| **Swagger / OpenAPI** | `http://localhost:8000/docs` | Documentação interativa da API |
| **ReDoc** | `http://localhost:8000/redoc` | Documentação estática alternativa |
| **Qdrant Dashboard** | `http://localhost:6333/dashboard` | Interface web para inspecionar coleções vetoriais |
| **PostgreSQL** | `localhost:5432` | Banco relacional (`user: automotive_user`, `db: automotive_db`) |
| **Ollama** | `localhost:11434` | Chat local e embeddings (`llama3.2:3b`, `bge-m3`) |
| **Chat do agente** | `http://localhost:8000/api/v1/chat/` | Interface conversacional fundamentada no RAG |
| **Jobs de ingestão** | `http://localhost:8000/api/v1/ingestion/jobs` | Progresso dos jobs de ingestão de PDF |

### Exemplo de Resposta do Health Check:
```json
{
  "status": "healthy",
  "project": "Automotive AI Agent",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-09-09T17:15:00.000000Z",
  "services": {
    "database": {
      "status": "connected",
      "latency_ms": 1.45,
      "database": "automotive_db"
    },
    "vector_db": {
      "status": "connected",
      "latency_ms": 2.10,
      "collections_count": 0
    }
  }
}
```

> **Nota**: Se o PostgreSQL ou o Qdrant ficarem indisponíveis, o endpoint `/health` responde automaticamente com HTTP **503 Service Unavailable** e detalha o motivo no campo `error`.


## 🧪 Executando os Testes

Para rodar a suíte de testes de integração e mocks:

```bash
# Via Makefile
make test

# Ou diretamente dentro do contêiner
docker compose exec backend pytest -v
```


## ⚠️ Notas e limitações conhecidas

- **Ingestão de PDFs grandes**: corrigido um bug de *loop infinito* no chunker (`AutomotiveChunker`) que estourava a memória do container ao processar certas páginas (ex.: página 85 do manual MINI R56). O pipeline completo agora processa centenas de páginas com uso estável de memória (~118 MB). O serviço `backend` mantém um `mem_limit` de 4 GB como rede de segurança.
- **JobTracker em memória**: o estado dos jobs de ingestão é mantido em memória e é perdido ao reiniciar o backend (não persistido no Postgres).
- **Compatibilidade Qdrant**: o cliente (`qdrant-client` 1.19) é mais novo que o servidor (Qdrant 1.11.3) e emite um *warning* de compatibilidade; não afeta o funcionamento.
- **Auto-ingestão**: `AUTO_INGEST_ENABLED` e `AUTO_INGEST_FORCE` vêm desabilitados por padrão. Ligue `AUTO_INGEST_FORCE=true` apenas para reindexação completa, pois reprocessa os PDFs a cada restart.

## 🗺️ Próximos Passos (Roadmap de Fases)


