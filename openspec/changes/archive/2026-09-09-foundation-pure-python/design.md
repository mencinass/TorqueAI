## Context

The Automotive AI Agent requires a reliable, modular, and reproducible foundation. The system must operate with 100% pure Python on the backend without any native C/C++ compiler toolchains or libraries, while seamlessly supporting local development on Windows (via PowerShell and Podman Machine) and Linux/macOS.

## Goals / Non-Goals

**Goals:**
- Provide a clean, modular monolith backend built exclusively in Python 3.11+.
- Implement asynchronous relational database connectivity via SQLAlchemy 2.0 and `asyncpg`.
- Integrate the official `qdrant-client` for vector database health and collection inspection.
- Build resilient, concurrent health checks (`/health` and `/api/v1/health`) executing in parallel via `asyncio.gather`.
- Provide zero-friction cross-platform execution via `run.ps1` (Windows) and `Makefile` (Linux).
- Standardize all architecture, capabilities, and verification tasks using OpenSpec.

**Non-Goals:**
- No C/C++ code compilation or native extension building.
- No relational vehicle models or CRUD in Phase 1 (reserved for Phase 2).
- No PDF chunking, embedding generation, or vector ingestion in Phase 1 (reserved for Phase 3/4).
- No LLM agent workflows in Phase 1 (reserved for Phase 5/6).

## Decisions

### Decision 1: Pure Python Runtime & Zero C Build Tooling
- **Chosen Approach**: Use Python 3.11 slim image with precompiled Python wheels (`asyncpg`, `qdrant-client`, `fastapi`, `pydantic`). Remove `gcc`, `libpq-dev`, and `psycopg2-binary`.
- **Alternatives Considered**: Building `psycopg2` from source with `gcc` and `libpq-dev`. Rejected because it introduces C toolchain dependencies and violates the strict pure Python requirement.

### Decision 2: Parallel Dependency Health Probes
- **Chosen Approach**: Execute `check_database_health()` and `check_qdrant_health()` concurrently using `asyncio.gather()`.
- **Rationale**: Guarantees fast response times for container probes and health monitors, avoiding cumulative sequential timeouts.

### Decision 3: Cross-Platform Automation via PowerShell and Makefile
- **Chosen Approach**: Supply `run.ps1` for native Windows execution and `Makefile` for Linux/macOS.
- **Rationale**: Windows users often lack `make`. A dedicated PowerShell script provides equal convenience and automatically ensures Python user scripts are accessible in `$env:PATH`.

## Risks / Trade-offs

- **[Risk]** Host Ollama unreachable from inside container.
  - **Mitigation**: Added `extra_hosts: ["host.containers.internal:host-gateway"]` in `docker-compose.yml` to bridge the container to the host machine.
- **[Risk]** Podman machine stopped on Windows.
  - **Mitigation**: Error handling in `run.ps1` alerts the user if the Podman engine socket is not reachable.
