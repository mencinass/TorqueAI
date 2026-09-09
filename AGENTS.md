# Contexto do agente: helpMec

## Como usar este arquivo

Leia este arquivo antes de alterar o projeto. Ele registra o estado conhecido no fim da sessao de 2026-09-09 e evita repetir diagnosticos ou destruir dados persistentes sem backup.

O documento operacional mais amplo esta em `docs/PROJECT_STATUS.md`.

## Projeto

`helpMec` e um assistente tecnico automotivo baseado em FastAPI, RAG e manuais de servico. A regra principal e zero-hallucination: respostas tecnicas devem usar somente evidencias recuperadas dos manuais, exibir fontes e diferenciar fatos de hipoteses.

Stack:

- Python 3.11
- FastAPI, Pydantic v2, SQLAlchemy async e asyncpg
- PostgreSQL 16
- Qdrant 1.11.3
- Ollama em container Podman
- `llama3.2:3b` para geracao
- `bge-m3` para embeddings multilingues, dimensao 1024
- pytest, pytest-asyncio e httpx

## Estado operacional atual

A Podman Machine foi recriada com:

- Memoria: 16384 MiB
- CPUs: 6
- Disco: 100 GiB
- Nome: `podman-machine-default`

Containers esperados:

- `automotive-ai-postgres`
- `automotive-ai-qdrant`
- `automotive-ai-ollama`
- `automotive-ai-backend`

Ollama e um container separado na rede `helpmec_automotive_net`, usando o volume `ollama_data`.

O `.env` local esta configurado com:

```env
CHAT_PROVIDER=ollama
CHAT_MODEL=llama3.2:3b
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=1024
AUTO_INGEST_ENABLED=true
AUTO_INGEST_FORCE=true
OLLAMA_BASE_URL=http://automotive-ai-ollama:11434
```

### Ponto de atencao imediato

`AUTO_INGEST_FORCE=true` foi habilitado porque a ingestao anterior parou parcialmente com apenas parte dos chunks no Qdrant. O modo force reprocessa os documentos mesmo quando ja existem pontos.

Nao desligue ou recrie o backend durante a ingestao sem necessidade. Quando os logs mostrarem:

```text
automatic_ingestion_finished
```

altere o `.env` para:

```env
AUTO_INGEST_FORCE=false
```

Depois recrie somente o backend:

```powershell
podman compose up -d backend
```

A quantidade de pontos pode ficar temporariamente igual durante o reprocessamento, pois os IDs dos chunks sao deterministas e os pontos sao sobrescritos.

## Comandos de inicio

```powershell
cd C:\Users\mathe\Documents\PROJETO\helpMec
podman machine start
podman start automotive-ai-ollama
podman compose up -d --build
```

Se a Podman Machine estiver parada ou inconsistente:

```powershell
podman machine stop
podman machine start
```

Nao use `podman machine rm` sem exportar antes os volumes:

```powershell
podman volume export helpmec_postgres_data --output .podman-backups/postgres.tar
podman volume export helpmec_qdrant_data --output .podman-backups/qdrant.tar
podman volume export ollama_data --output .podman-backups/ollama.tar
```

## URLs

- Chat: `http://localhost:8000/api/v1/chat/`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Qdrant: `http://localhost:6333/dashboard`
- Ollama: `http://localhost:11434`

## Acompanhamento da ingestao

Logs:

```powershell
podman logs -f automotive-ai-backend
```

Eventos relevantes:

- `automatic_ingestion_started`
- `qdrant_upsert_complete`
- `ingestion_complete`
- `automatic_ingestion_finished`
- `ingestion_failed`

Indice:

```powershell
$data=(Invoke-WebRequest http://localhost:6333/collections/automotive_manuals -UseBasicParsing).Content | ConvertFrom-Json
"dimensao=$($data.result.config.params.vectors.size) pontos=$($data.result.points_count) status=$($data.result.status)"
```

Jobs:

```powershell
Invoke-WebRequest http://localhost:8000/api/v1/ingestion/jobs -UseBasicParsing
```

Se jobs ou comandos Podman expirarem, verifique memoria e CPU antes de reiniciar. A extracao de PDFs grandes e pesada; o backend usa `asyncio.to_thread` em `pdf_extractor.py` e `ingestion_pipeline.py` para nao bloquear o event loop.

## Arquitetura relevante

- `backend/app/main.py`: lifespan, banco, tracker, pipeline e auto-ingest.
- `backend/app/services/auto_ingestion_service.py`: busca documentos cadastrados e inicia reingestao sequencial.
- `backend/app/rag/ingestion_pipeline.py`: PDF -> chunks -> embeddings -> Qdrant.
- `backend/app/rag/pdf_extractor.py`: leitura pagina a pagina com extraçao em thread.
- `backend/app/rag/embeddings.py`: providers mock, Ollama e OpenAI-compatible; Ollama usa `/api/embed` em lote.
- `backend/app/rag/qdrant_manager.py`: colecao, indices, upsert e busca via `query_points`.
- `backend/app/services/chat_service.py`: retrieval-first, citations, fallback e chamada do Ollama.
- `backend/app/api/v1/endpoints/chat.py`: interface web e endpoints do chat.
- `backend/tests/`: testes de chat, Ollama, ingestao, documentos, veiculos e health.

## Correcoes importantes ja feitas

- Logger ausente em `backend/app/main.py` foi corrigido.
- Cliente Qdrant deixou de usar `async with`; clientes sao fechados explicitamente.
- Busca Qdrant usa `query_points`, compativel com qdrant-client 1.19.
- Colecao ausente retorna evidencia insuficiente, nao HTTP 503.
- PDFs sao montados em `/app/service_guide`.
- Auto-ingest foi adicionado ao startup.
- Uvicorn no container roda sem `--reload`, para nao cancelar ingestao longa.
- Ollama foi colocado na rede do Compose.
- Embeddings Ollama foram otimizados para lote via `/api/embed`.
- Extraçao PDF e contagem de paginas foram movidas para threads.

## Validacao

Python local usado durante as validacoes:

```powershell
C:\Users\mathe\AppData\Local\Python\pythoncore-3.11-64\python.exe
```

Testes locais conhecidos:

- `45 passed` antes das ultimas mudancas de documentacao e threads.
- `28 passed` em ingestao + chat apos a correcao de threads.
- `23 passed` em ingestao apos ajustes de reingestao.

Rode novamente antes de afirmar que o estado atual esta verde:

```powershell
cd backend
C:\Users\mathe\AppData\Local\Python\pythoncore-3.11-64\python.exe -m pytest -q
```

Dentro do container:

```powershell
podman compose exec -T backend pytest -q
```

OpenSpec:

```powershell
openspec validate --changes --json
```

Ultima validacao OpenSpec conhecida: `3 passed, 0 failed`.

## OpenSpec

Mudancas criadas:

- `agent-chat-frontend`: chat web grounded no RAG.
- `ollama-grounded-chat`: provider Ollama, prompt automotivo e citacoes.
- `containerized-validation`: Docker/Podman Compose, health, testes e CI.

Todas foram validadas como changes. Verifique o status antes de arquivar:

```powershell
openspec list --json
openspec status --change containerized-validation --json
```

## Proximas acoes recomendadas

1. Acompanhar a reingestao forcada ate `automatic_ingestion_finished`.
2. Confirmar que todos os documentos cadastrados tiveram jobs `done`.
3. Definir `AUTO_INGEST_FORCE=false` e recriar somente o backend.
4. Rodar testes locais e `podman compose exec -T backend pytest -q`.
5. Testar uma pergunta em portugues e uma em ingles pelo chat.
6. Medir a busca com filtro `generation_code=R56` e `system=steering`.
7. Atualizar/arquivar a change OpenSpec de containerizacao somente depois da validacao efetiva no runtime.

## Cuidados

- Nunca remover volumes ou a Podman Machine sem backup.
- Nao considerar `points_count > 0` como prova de ingestao completa.
- Nao deixar `AUTO_INGEST_FORCE=true` depois da reindexacao.
- Nao afirmar que uma resposta tecnica esta correta sem verificar suas citacoes.
- O historico de chat atual e em memoria e se perde ao reiniciar o backend.
