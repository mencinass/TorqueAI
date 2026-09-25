# TorqueAI 🚗🔧

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-1.11-DC382D?logo=qdrant&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local_LLM-000000?logo=ollama&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![NVIDIA](https://img.shields.io/badge/GPU-NVIDIA_optional-76B900?logo=nvidia&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-8-0A9EDC?logo=pytest&logoColor=white)
![Ruff](https://img.shields.io/badge/Ruff-linter-261230?logo=ruff&logoColor=white)
![OpenSpec](https://img.shields.io/badge/OpenSpec-spec_driven-5C67E6)

Intelligent automotive technical-assistant system based on AI, RAG (Retrieval-Augmented Generation) and grounded chat for querying service manuals, diagnosing faults, technical specifications (torque, clearances, fluids) and OBD/DTC codes.

> The current operational state (Docker, Ollama, ingestion, troubleshooting) is documented in [AGENTS.md](AGENTS.md), which is the source of truth for the real environment. [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) describes an earlier session (Windows + Podman) and may be outdated.

---

## 📌 Project Overview

**TorqueAI** (formerly helpMec) was designed to help mechanics, workshops and automotive enthusiasts find precise technical information directly from manufacturer manuals, eliminating hallucinations and always citing the source (manual, chapter and page).

### Core Pillars

1. **Pure Python core**: Backend, connections and agents run in Python (no C/C++ LLM SDKs). PDF extraction uses the system tool **poppler-utils** (`pdftotext`/`pdfinfo`) in isolated subprocesses, with a per-page timeout and memory limit — a deliberate choice so a pathological page can be killed without hanging the process.
2. **OpenSpec standard (Spec-Driven Development)**: All specifications, capabilities and changes strictly follow the OpenSpec standard with observable WHEN/THEN scenarios.
3. **Zero-hallucination policy**: The system **never invents technical data or torque values**. If the information is not in the indexed documents, the agent explicitly says so.
4. **Source traceability**: Every technical answer states the source document, system and page.
5. **Strict differentiation**: Diagnostic hypotheses are explicitly separated from official manufacturer procedures.
6. **Modular architecture**: Clean modular monolith, scalable and prepared for multiple vehicle models and AI providers.

## 🏗️ Architecture

```
TorqueAI
├── Backend (FastAPI - Python 3.11)
│   ├── Async API with Uvicorn
│   ├── Real health checks (PostgreSQL + Qdrant)
│   ├── SQLAlchemy 2.0 models (asyncpg)
│   ├── Two-layer RAG pipeline (PDF extraction → chunking → embeddings → upsert)
│   │   ├── automotive_manuals  (vehicle-specific service manuals)
│   │   └── general_mechanics  (foundational mechanical knowledge)
│   ├── Session auth (login page + guarded endpoints)
│   └── Page thumbnails for source validation in the chat UI
├── Relational DB (PostgreSQL 16)
│   └── Users, vehicles, document metadata, chat history
├── Vector DB (Qdrant)
│   └── High-dimensional vectors with metadata filters
└── Ollama (GPU-accelerated when available)
    └── Local chat generation and embeddings (bge-m3)
```

### The two RAG layers

| Layer | Qdrant collection | Content | Filters |
| :--- | :--- | :--- | :--- |
| Vehicle-specific | `automotive_manuals` | Manufacturer service manuals (MINI R56/R53, Fiat 500, Honda Civic) | `generation_code`, `system`, `engine_code` |
| General mechanics | `general_mechanics` | Foundational knowledge (engine theory, tools, procedures) | none |

At query time the chat endpoint searches **both** collections, merges the results **ranked by similarity score** and caps the combined context at `top_k`. Vehicle filters are applied only to the vehicle-specific layer. General-mechanics PDFs are deduplicated by MD5 and probed for a text layer (scanned/image-only PDFs are skipped) before registration and ingestion.

## 📂 Repository Structure

```text
TorqueAI/
├── backend/
│   ├── app/
│   │   ├── api/                # API routes and dependency injection
│   │   │   ├── v1/endpoints/   # Versioned endpoints (auth, chat, documents, health, ingestion, vehicles)
│   │   │   └── deps.py         # DB session and auth dependency providers
│   │   ├── core/               # Pydantic settings, structured logging, exceptions
│   │   ├── database/           # Async SQLAlchemy engine, seed and init
│   │   ├── models/             # Relational ORM models
│   │   ├── rag/                # PDF extraction, chunking, embeddings, Qdrant manager, ingestion pipeline
│   │   ├── agents/             # Chat providers (Ollama/NVIDIA) and grounded prompting
│   │   ├── schemas/            # Pydantic validation/serialization schemas
│   │   ├── services/           # Chat, ingestion, thumbnails, auth, vehicle services
│   │   └── main.py             # FastAPI instantiation and lifespan
│   ├── tests/                  # pytest test suite (unit + integration)
│   ├── Dockerfile              # Slim backend image (python:3.11-slim + poppler-utils)
│   ├── requirements.txt        # Production dependencies
│   └── requirements-dev.txt    # Test and quality dependencies
├── service_guide/              # Service manuals in PDF (MINI R56/R53, Fiat 500, Honda Civic, general/)
├── openspec/                   # OpenSpec specs, changes and archive
├── .agents/                    # OpenSpec skills and workflows for the AI assistant
├── docs/                       # Historical project status notes
├── docker-compose.yml          # Backend, PostgreSQL, Qdrant and Ollama orchestration
├── run.ps1                     # PowerShell automation script (Windows)
├── Makefile                    # Command automation for Linux / macOS
├── .env.example                # Example environment variables
└── README.md                   # This documentation
```

## 🚀 How to Run

The environment is compatible with **Linux**, **macOS** and **Windows**, with **Docker Compose** (primary) and **Podman** (compatible).

### 1. Prerequisites

- Docker Engine + Docker Compose v2 (`docker compose`), or Podman + `podman-compose`.
- For GPU acceleration of local models: NVIDIA driver + `nvidia-container-toolkit` (optional).

### 2. Quick start (Linux / macOS)

```bash
cp .env.example .env        # adjust values if needed
make up                     # start all services in the background
make ollama-pull            # download the chat + embedding models
make health                 # verify the stack
```

Then open <http://localhost:8000/api/v1/auth/login> and sign in with the admin credentials from your `.env` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`).

Other useful Makefile targets:

```bash
make ps         # container status
make logs       # live logs (backend: make logs-backend)
make test       # run the automated test suite
make lint       # static analysis with ruff
make validate   # up + health + test
make down       # stop services (volumes are kept)
make clean      # stop services AND remove volumes (destructive)
```

### 3. Windows (PowerShell)

```powershell
.\run.ps1 up          # start all services in the background
.\run.ps1 ps          # container status
.\run.ps1 health      # health check
.\run.ps1 logs        # live logs
.\run.ps1 test        # automated tests
.\run.ps1 down        # stop services
.\run.ps1 validate    # up + health + tests
.\run.ps1 clean       # also remove volumes (destructive)
```

### 4. Manual start

```bash
docker compose up -d --build
```

The default `down` does not remove volumes. Use `make clean` / `.\run.ps1 clean` only when you want to wipe local data. If startup fails, confirm Docker Engine is running (or the Podman machine is started with `podman machine start`).

### 5. Local chat with Ollama

Ollama runs as a Compose service with GPU access (when available). The backend uses:

- Embeddings: `bge-m3` (1024 dimensions) via `EMBEDDING_PROVIDER=ollama`.
- Chat: `CHAT_PROVIDER=ollama` with `CHAT_MODEL` — the repo default is `qwen3.8:latest`.

> **GPU sizing note**: `qwen3.8:latest` is a 27B model (~17 GB quantized). On GPUs with less than ~18 GB of VRAM (e.g. RTX 3060 12 GB) Ollama offloads to CPU and answers take 60–90 s. On such hardware set `CHAT_MODEL=qwen2.5:7b` in your `.env` (fast, fully in-VRAM answers) — this is what the provided `.env` does.

```bash
make ollama-pull      # pulls the configured models into the ollama container
```

Relevant `.env` variables (defaults aligned with the Compose file):

```env
CHAT_PROVIDER=ollama
CHAT_MODEL=qwen3.8:latest     # or qwen2.5:7b on <18 GB GPUs
OLLAMA_BASE_URL=http://ollama:11434
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=1024
QDRANT_COLLECTION=automotive_manuals
GENERAL_MECHANICS_COLLECTION=general_mechanics
```

Alternative providers exist for chat (`nvidia` — NVIDIA NIM/OpenAI-compatible, `extractive` — extract snippets only) and embeddings (`openai`, `mock` for offline tests). With the API running, open <http://localhost:8000/api/v1/chat/>. The model receives only the excerpts retrieved from the indexed manuals; without sufficient evidence the chat refuses to produce a technical conclusion.

## 📥 PDF Ingestion via API

Locally registered manuals are ingested automatically on first startup (see [Auto-ingestion](#auto-ingestion-on-startup)). For **new** PDFs, use `POST /api/v1/ingestion/start`.

### Before ingesting

1. Place the PDF in `service_guide/` (mounted read-only at `/app/service_guide` inside the backend container) or any path accessible from the container.
2. The document must be registered in the `technical_documents` table (Postgres) — insert a row with its `file_path`, or reference an existing `document_id`. The `pdf_path` in the request body may point directly at the file inside the container (e.g. `/app/service_guide/<folder>/<file>.pdf`), but `document_id` is required.

### Starting an ingestion

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/start \
  -H 'Content-Type: application/json' \
  -d '{
    "document_id": 5,
    "pdf_path": "/app/service_guide/NEW/manual.pdf",
    "max_pages": 500,
    "document_metadata": {
      "document_title": "New Model Manual",
      "document_type": "workshop_manual",
      "system": "engine",
      "generation_code": "F56",
      "engine_code": "B48"
    }
  }'
```

Request body fields (`IngestionStartRequest`):

| Field | Type | Description |
| :--- | :--- | :--- |
| `document_id` | int | Required. PK of the `TechnicalDocument` (existing or new). |
| `pdf_path` | string | Optional. Path to the PDF inside the container; if omitted it is auto-resolved from the `document_id`. |
| `max_pages` | int | Optional page limit (e.g. `500`). `null`/omitted = all pages. |
| `chunk_size` | int | Optional, default `1000`. Chunk size in characters. |
| `chunk_overlap` | int | Optional, default `150`. Overlap between chunks. |
| `document_metadata` | object | Optional. `document_title`, `document_type`, `system`, `generation_code`, `engine_code`. **Pass it** so chunks carry correct metadata (otherwise they fall back to the `workshop_manual`/`general` defaults). |

The response is `202 Accepted` with a `job_id`; ingestion runs in the background.

### Tracking progress

```bash
# List all jobs
curl http://localhost:8000/api/v1/ingestion/jobs

# Status of a specific job
curl http://localhost:8000/api/v1/ingestion/jobs/<job_id>
```

A job reports `status` (`pending` → `running` → `done`/`failed`), `total_pages`, `pages_processed`, `chunks_created` and `points_upserted`.

### Auto-ingestion on startup

On startup the backend ingests two document sets when their collections are empty (`AUTO_INGEST_ENABLED=true`):

- **Vehicle-specific manuals** — rows already present in `technical_documents`.
- **General mechanics** — every unique, text-bearing PDF in `service_guide/general`, registered automatically in `technical_documents` (deduplicated by MD5; scanned/image-only PDFs are skipped).

To reprocess everything from scratch set `AUTO_INGEST_FORCE=true` (reprocesses PDFs on every restart — use only for reindexing and set it back to `false` afterwards). Adjust these variables in `.env` and recreate the container (`docker compose up -d --force-recreate backend`); a plain `restart` does not re-read `.env`.

> **OCR note**: **scanned** PDFs (image without a text layer) produce no text via `pdftotext` and yield 0 chunks — this is the case for the R53 manual in this repository. Those require an OCR step (e.g. `ocrmypdf`) before ingestion.

## 📋 OpenSpec (Spec-Driven Development)

The project adopts **OpenSpec** to govern the spec-driven development lifecycle. All new features, models and behaviors must be validated with OpenSpec before and after implementation.

```bash
# List active specs
openspec list --specs

# Validate all specs for conformance
openspec validate --specs

# Start a new change proposal
openspec new change <change-name>
```

Validated specs live in `openspec/specs/`; in-flight changes in `openspec/changes/`.

## 🩺 Verification and Endpoints

With the containers running:

| Service | URL / Port | Description |
| :--- | :--- | :--- |
| **FastAPI Root Health** | `http://localhost:8000/health` | Overall status with live PostgreSQL and Qdrant checks |
| **FastAPI v1 Health** | `http://localhost:8000/api/v1/health` | Versioned health check |
| **Swagger / OpenAPI** | `http://localhost:8000/docs` | Interactive API documentation |
| **ReDoc** | `http://localhost:8000/redoc` | Alternative static documentation |
| **Login** | `http://localhost:8000/api/v1/auth/login` | Session login page (single admin user) |
| **Chat** | `http://localhost:8000/api/v1/chat/` | RAG-grounded conversational UI (requires login) |
| **Vehicle picker** | `http://localhost:8000/api/v1/vehicles/picker` | Generations and systems for the chat filters |
| **Ingestion jobs** | `http://localhost:8000/api/v1/ingestion/jobs` | PDF ingestion job progress (requires login) |
| **Page thumbnail** | `/api/v1/documents/{id}/page/{n}/thumbnail` | Renders manual page `n` as PNG (visual source validation in chat) |
| **Qdrant Dashboard** | `http://localhost:6333/dashboard` | Web UI to inspect vector collections |
| **PostgreSQL** | `localhost:5432` | Relational DB (`user: automotive_user`, `db: automotive_db`) |
| **Ollama** | `localhost:11434` | Local chat generation and embeddings |

Example health check response:

```json
{
  "status": "healthy",
  "project": "TorqueAI",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-09-25T14:57:59.660074Z",
  "services": {
    "database": { "status": "connected", "latency_ms": 1.9, "database": "automotive_db" },
    "vector_db": { "status": "connected", "latency_ms": 2.3, "collections_count": 1 }
  }
}
```

> **Note**: If PostgreSQL or Qdrant become unavailable, `/health` automatically responds with HTTP **503 Service Unavailable** and details the reason in the `error` field.

## 🧪 Running the Tests

```bash
# Via Makefile
make test

# Or directly inside the container
docker compose exec backend pytest -v
```

## ⚠️ Known Notes and Limitations

- **Large PDF ingestion**: an infinite-loop bug in the chunker (`AutomotiveChunker`) that exhausted container memory on certain pages (e.g. page 85 of the MINI R56 manual) has been fixed. The full pipeline now processes hundreds of pages with stable memory usage (~118 MB peak). The `backend` service keeps a 4 GB `mem_limit` as a safety net.
- **In-memory JobTracker**: ingestion job state lives in memory and is lost on backend restart (not persisted to Postgres).
- **Qdrant compatibility**: the client (`qdrant-client` 1.19) is newer than the server (Qdrant 1.11.3) and emits a compatibility warning; it does not affect operation.
- **Model sizing**: `qwen3.8:latest` does not fit GPUs with < 18 GB VRAM without severe CPU offloading (see the GPU sizing note above); on such hardware use `qwen2.5:7b`.
- **Auto-ingestion**: `AUTO_INGEST_ENABLED` and `AUTO_INGEST_FORCE` default to disabled. Enable `AUTO_INGEST_FORCE=true` only for full reindexing, since it reprocesses PDFs on every restart.
