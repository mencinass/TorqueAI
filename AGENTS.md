# Contexto do agente: TorqueAI (helpMec)

## Como usar este arquivo

Leia este arquivo antes de alterar o projeto. Ele registra o estado real ao fim da sessao de 2026-09-09 no ambiente Linux/Docker (Arch Linux). Existe tambem `docs/PROJECT_STATUS.md`, mas esse arquivo descreve uma sessao ANTERIOR em Windows + Podman e esta desatualizado em varios pontos (nome dos containers, comandos, etc.) — confie neste `AGENTS.md` para o estado atual.

## Ambiente desta sessao

- Arch Linux, GPU NVIDIA GeForce RTX 3060 (driver `nvidia-open`, CUDA funcionando).
- Docker Engine (NAO Podman) + Docker Compose v2 (`docker compose`), usuario no grupo `docker` (sem sudo necessario para comandos docker).
- `nvidia-container-toolkit` instalado e configurado (`nvidia-ctk runtime configure --runtime=docker` + restart do docker) para permitir GPU dentro de containers.

## O que foi feito nesta sessao

1. **Ollama containerizado com GPU**: adicionado servico `ollama` (imagem `ollama/ollama:latest`) no `docker-compose.yml`, com passthrough de GPU via `deploy.resources.reservations.devices` (driver nvidia). Backend fala com ele via `http://ollama:11434` (rede interna do compose, nao mais via `host.containers.internal`, que era um artefato do Podman/Windows).
2. **Modelos baixados**: `llama3.2:3b` (chat) e `bge-m3` (embeddings, dim 1024) ja estao no volume `ollama_data`. `make ollama-pull` baixa ambos se precisar de novo.
3. **Provider padrao trocado**: `.env`/`.env.example`/`docker-compose.yml` usam `CHAT_PROVIDER=ollama` e `EMBEDDING_PROVIDER=ollama` por padrao (antes era `nvidia`, API cloud paga). A chave `NVIDIA_API_KEY` continua no `.env` como fallback, mas nao e mais usada por padrao — considerar revogar se nao for mais necessaria.
4. **PDF extraction reescrita**: `backend/app/rag/pdf_extractor.py` NAO usa mais `pypdf`. Agora usa `poppler-utils` (`pdfinfo`/`pdftotext`) via subprocesso (`asyncio.create_subprocess_exec`), com timeout de 30s e `RLIMIT_AS` de 2GiB por pagina. Isso resolveu um bug real: paginas pesadas travavam a GIL dentro de uma thread (pypdf + `asyncio.to_thread`) e o timeout do `asyncio.wait_for` nunca disparava porque a GIL ficava presa em codigo C (zlib). Com subprocesso isolado, o kill (SIGKILL) funciona de verdade.
   - `backend/Dockerfile` instala `poppler-utils`.
   - `backend/requirements.txt` nao tem mais `pypdf`.
5. **Rede de seguranca de memoria**: `docker-compose.yml` tem `deploy.resources.limits.memory: 4G` no servico `backend`. Se algo vazar memoria, o Docker mata e reinicia so esse container (politica `restart: unless-stopped`), sem arriscar o host (32GB RAM, sem swap configurado).
6. **Qdrant ulimit**: adicionado `ulimits.nofile: 65536` no servico `qdrant` no compose, porque bati no erro `Too many open files (os error 24)` ao criar/deletar varias coleções de teste durante o debug.

## PROBLEMA RESOLVIDO: vazamento de memoria na ingestao de PDFs grandes

**Causa raiz encontrada e corrigida.** O "vazamento" nao era vazamento de verdade, e sim um **loop infinito de alocacao** no `AutomotiveChunker.chunk_page` (`backend/app/rag/chunker.py`). Quando o "clean break" (`\n\n` ou `. `) recuava o `end` para uma posicao tal que `end - chunk_overlap <= start`, o `start` nao avancava (a condicao de escape `if start <= 0 and end <= start` so pegava o caso `start <= 0`), e o loop gerava `DocumentChunk` infinitamente ate estourar o limite de 4GB do cgroup (OOM do container).

- **Gatilho determinístico**: a pagina 85 do `mini_R56_service.pdf` (texto com paragrafos separados por `\n\n`, sem `. ` para ancorar o fallback) fazia `start` ficar preso em 897 e `end` em 1047 para sempre.
- **Evidencia**: `dmesg` no host mostrava `Memory cgroup out of memory: Killed process (python) anon-rss: ~4.08GB` sempre identico; `faulthandler.dump_traceback` capturou o stack preso em `chunker.py:84 (uuid5)` / `:87 (DocumentChunk.__init__)`.
- **Correcao** (em `chunker.py`): garantir progresso monotono — `next_start = end - overlap; if next_start <= start: next_start = start + 1`.
- **Prova**: pipeline completo (extract + chunk + embed Ollama + upsert Qdrant) rodou **471 paginas** sem OOM, com **peak VmRSS 118MB / anon 84MB** (antes: OOM em ~95 paginas). Teste de regressao adicionado em `tests/test_ingestion.py::test_chunk_page_terminates_when_clean_break_pulls_back`.
- `MALLOC_ARENA_MAX=1` nao era a causa (testado e descartado). `ThreadedChildWatcher`/FD leak tambem descartados (threads=2, fds=7 constantes ao longo do run).

### Estado atual (seguro, ingestao completa possivel)

- `.env`: `AUTO_INGEST_ENABLED=false` e `AUTO_INGEST_FORCE=false` (estado seguro). Os defaults no codigo agora tambem sao `false`/`ollama`/`bge-m3`/`1024` (alinhados com o compose e `.env.example` — antes havia incoerencia: compose usava `AUTO_INGEST_ENABLED=true` e `config.py` tinha `mock`/`nomic-embed-text`/`768`/`extractive`).
- 4 documentos cadastrados (ids 1-4, ver `seed.py`), colecao `automotive_manuals` (dim 1024) ativa no Qdrant.
- Ingerir paginas de um documento (agora sem limite de seguranca de 50 paginas, mas o `mem_limit: 4G` continua como rede de seguranca):
  ```bash
  curl -X POST http://localhost:8000/api/v1/ingestion/start -H 'Content-Type: application/json' \
    -d '{"document_id": 1, "pdf_path": "/app/service_guide/MINI_R56/mini_R56_service.pdf", "max_pages": 500}'
  ```

## Melhorias sugeridas para producao (discutidas, nao implementadas)

- Separar a ingestao pesada em um **worker/container dedicado**, diferente do container da API que serve o chat — assim um documento problematico nunca derruba a API.
- Persistir o `JobTracker` (hoje em memoria, some ao reiniciar o backend) no Postgres.
- Considerar rate limiting / paginacao de ingestao com checkpoint (retomar de onde parou em vez de sempre reiniciar da pagina 1).

## Comandos uteis (Linux/Docker, este ambiente)

```bash
docker compose up -d --build        # subir tudo
docker compose ps                   # status
docker compose logs backend -f      # logs do backend
docker stats --no-stream            # uso de CPU/memoria por container
make ollama-pull                    # baixar llama3.2:3b e bge-m3 no container ollama
curl http://localhost:8000/health   # healthcheck
curl http://localhost:8000/api/v1/ingestion/jobs   # progresso de jobs de ingestao
```

## Cuidados

- Nao ligar `AUTO_INGEST_FORCE=true` sem intencao de reindexacao completa (a cada restart do backend, reprocessa os PDFs). O bug de memoria que causava crash foi corrigido, mas o `mem_limit: 4G` do backend e os `ulimits` do Qdrant continuam como rede de seguranca — nao remover.
- `AGENTS.md` (este arquivo) reflete o estado real; `docs/PROJECT_STATUS.md` esta desatualizado (Windows/Podman) e deve ser tratado com cautela ou atualizado numa proxima sessao.

