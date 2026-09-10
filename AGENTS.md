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

## PROBLEMA NAO RESOLVIDO: vazamento de memoria na ingestao de PDFs grandes

Apos a correcao do pypdf (item 4 acima), ficou provado que a extracao de PDF (`PDFExtractor.stream_pages`) sozinha e limpa (testada com 300 paginas reais, RSS ficou flat em ~35MB). MAS o pipeline completo (`PDFExtractor` + `AutomotiveChunker` + `OllamaEmbeddingProvider` + `QdrantManager`, ou seja `IngestionPipeline.run()` em `backend/app/rag/ingestion_pipeline.py`) ainda vaza memoria de forma real e reprodutivel quando processa VARIAS CENTENAS de paginas seguidas do mesmo documento grande (`service_guide/MINI_R56/mini_R56_service.pdf`, 2129 paginas, 561MB).

### Evidencias coletadas (nao repetir esses testes, ja estao provados)

- `PDFExtractor` isolado (sem chunker/embedder/qdrant): 300 paginas reais, RSS **flat** (~35MB). Sem vazamento.
- Pipeline completo via script manual, 70 paginas: RSS **flat** (~113MB -> 133MB). Limpo.
- Pipeline completo via API real (`POST /api/v1/ingestion/start`) com `max_pages=70`: `status: done`, memoria ficou baixa (~110MB). Limpo.
- Pipeline completo via API real com `max_pages=500`: crash por OOM em ~10-20s (bateu no limite de 4GB do container).
- Pipeline completo via API real com `max_pages=100`: tambem crashou (~2.6GB antes de estourar) — ou seja o limiar NAO e um numero fixo de paginas, varia entre execucoes (pode depender de qual pagina especifica calhou de ser processada, ou nao ser puramente deterministico).
- Scan de `pdftotext -f N -l N` pagina por pagina (1 a 500) da `mini_R56_service.pdf`: NENHUMA pagina individual produz saida anormalmente grande (>5000 bytes). Isso descarta a teoria de "uma pagina especifica corrompida/bomba de descompressao".
- Teste com `tracemalloc` bisectando pagina 20 -> 60 (dentro de uma execucao limpa de 70 paginas): sem crescimento significativo, sem alocacao suspeita nos diffs.
- Hipotese em teste (NAO CONCLUIDA, foi interrompida por limpeza de terminal, nao por OOM real): `MALLOC_ARENA_MAX=1` (mitigacao classica para fragmentacao de arenas do glibc malloc quando ha muitas threads/subprocessos de vida curta, como os milhares de `pdftotext` spawnados por documento). Rodou ate a pagina 50 com RSS baixo (101MB) antes do processo ser encerrado (SIGKILL, causa ambigua: pode ter sido o cgroup OU limpeza de terminal do proprio ambiente de dev, nao confirmado como OOM real).
- Erro secundario encontrado (e corrigido): `Too many open files (os error 24)` no Qdrant, causado por varias colecoes de teste (`leak_test_collection`, `leak_test_collection2`, `leak_test_arena1`) criadas durante o debug. Ja deletadas. Ulimit do Qdrant ja aumentado (ver item 6 acima).

### Proximo passo recomendado (nao feito ainda)

1. **Retomar o teste `MALLOC_ARENA_MAX=1`** ate completar (nao interromper por outros comandos no mesmo terminal — usar terminal dedicado e so fazer `get_terminal_output` para checar, nunca `run_in_terminal` sincrono em paralelo no mesmo terminal, isso manda Ctrl+C e mata o teste). Se resolver, aplicar `MALLOC_ARENA_MAX=1` como env var permanente do servico `backend` no `docker-compose.yml`.
2. Se nao resolver, investigar se o watcher de subprocessos do asyncio (`ThreadedChildWatcher`, 1 thread por `pdftotext` spawnado) esta relacionado — testar reduzindo chamadas de subprocesso (ex: extrair varias paginas por chamada de `pdftotext` em vez de uma por vez) para ver se o vazamento desaparece.
3. Alternativa mais robusta para producao: mover a extracao/ingestao para um **worker separado** do processo da API (fora do escopo desta sessao, ver secao "Melhorias sugeridas para producao" abaixo).

### Estado atual (seguro, mas com ingestao parcial)

- `.env`: `AUTO_INGEST_ENABLED=false` — NAO ligar para `true` com `AUTO_INGEST_FORCE=true` sem querer reproduzir o crash loop nos documentos grandes.
- 4 documentos ja tem as primeiras 50 paginas ingeridas (testado como seguro) via `POST /api/v1/ingestion/start` com `max_pages: 50`:
  - id 1: MINI R56 Service — 60 chunks
  - id 2: MINI R56 Repair — 72 chunks
  - id 3: MINI R53 Service — 0 chunks (paginas 1-50 sao capa/indice, sem texto util, nao e bug)
  - id 4: Fiat 500 — rodou, resultado nao confirmado no fim da sessao (conferir com `GET /api/v1/ingestion/jobs`)
- Colecao `automotive_manuals` no Qdrant tinha 206+ pontos ao fim da sessao.
- Para ingerir mais paginas de um documento com seguranca, usar `max_pages` bounded (50-70 confirmado seguro; 100+ pode crashar, mas o `mem_limit: 4G` protege o host de qualquer forma):
  ```bash
  curl -X POST http://localhost:8000/api/v1/ingestion/start -H 'Content-Type: application/json' \
    -d '{"document_id": 1, "pdf_path": "/app/service_guide/MINI_R56/mini_R56_service.pdf", "max_pages": 50}'
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

- Nao ligar `AUTO_INGEST_FORCE=true` sem limitar `max_pages` ou sem estar pronto para o vazamento de memoria acontecer de novo (esta contido pelo `mem_limit: 4G`, mas ainda assim reinicia o container).
- Nao remover o `mem_limit` do backend nem os `ulimits` do Qdrant — foram adicionados por causa de problemas reais encontrados nesta sessao.
- `AGENTS.md` (este arquivo) reflete o estado real; `docs/PROJECT_STATUS.md` esta desatualizado (Windows/Podman) e deve ser tratado com cautela ou atualizado numa proxima sessao.

