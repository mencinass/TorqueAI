# helpMec: estado atual do projeto

## Visao geral

O helpMec e um backend FastAPI para consulta tecnica automotiva usando manuais de servico como fonte de evidencias. O sistema combina PostgreSQL para catalogo de veiculos e documentos, Qdrant para busca vetorial, Ollama para embeddings e geracao local, e uma interface web de chat.

Politicas centrais:

- Respostas tecnicas devem ser baseadas nos trechos recuperados dos manuais.
- Fontes devem ser exibidas com documento, secao e pagina quando disponiveis.
- Ausencia de evidencia deve resultar em uma resposta de evidencia insuficiente, nao em invencao.
- Hipoteses diagnosticas devem ser diferenciadas de fatos confirmados pelo manual.

## Componentes em execucao

| Componente | Funcao | Porta |
| --- | --- | --- |
| FastAPI backend | API, chat, ingestao e healthcheck | `8000` |
| PostgreSQL 16 | Catalogo de veiculos e documentos | `5432` |
| Qdrant | Colecao vetorial `automotive_manuals` | `6333` / `6334` |
| Ollama | Chat local e embeddings | `11434` |

O backend, PostgreSQL e Qdrant sao gerenciados pelo Compose. O Ollama e executado como container separado, conectado a rede `helpmec_automotive_net`, com o volume `ollama_data`.

## Configuracao atual

O arquivo `.env` local esta configurado para:

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

`AUTO_INGEST_FORCE=true` deve ser usado somente durante uma reindexacao completa. Depois que todos os documentos forem processados, altere para:

```env
AUTO_INGEST_FORCE=false
```

Caso contrario, cada reinicio do backend reprocessara os PDFs.

## Modelos Ollama

Modelos esperados no container:

```text
llama3.2:3b  # geracao de respostas
bge-m3       # embeddings multilingues, dimensao 1024
```

Verificar:

```powershell
podman exec automotive-ai-ollama ollama list
```

## Documentos

Os PDFs ficam em `service_guide/` e sao montados como somente leitura em `/app/service_guide` no backend. O catalogo inicial contem manuais para:

- MINI R56
- MINI R53
- Fiat 500

A ingestao cria chunks com texto e metadados de documento, geracao, motor, sistema e pagina. Os vetores sao gravados em `automotive_manuals`.

## Ingestao automatica

No startup, o backend consulta os documentos cadastrados no PostgreSQL e inicia jobs sequenciais quando `AUTO_INGEST_ENABLED=true`. A ingestao e executada em background e usa embeddings Ollama em lote.

Acompanhar logs:

```powershell
podman logs -f automotive-ai-backend
```

Eventos importantes:

```text
automatic_ingestion_started
qdrant_upsert_complete
ingestion_complete
automatic_ingestion_finished
ingestion_failed
```

Verificar o indice:

```powershell
$data=(Invoke-WebRequest http://localhost:6333/collections/automotive_manuals -UseBasicParsing).Content | ConvertFrom-Json
"dimensao=$($data.result.config.params.vectors.size) pontos=$($data.result.points_count) status=$($data.result.status)"
```

Consultar jobs:

```powershell
Invoke-WebRequest http://localhost:8000/api/v1/ingestion/jobs -UseBasicParsing
```

A quantidade de pontos pode nao mudar durante o reprocessamento de um documento, porque os IDs dos chunks sao deterministas e os pontos existentes sao sobrescritos.

## Chat

Interface web:

```text
http://localhost:8000/api/v1/chat/
```

Endpoints principais:

- `POST /api/v1/chat/messages`: pergunta com filtros opcionais de geracao e sistema.
- `GET /api/v1/chat/sessions/{session_id}`: historico da sessao em memoria.
- `GET /api/v1/ingestion/jobs`: progresso dos jobs de ingestao.
- `GET /health`: saude de PostgreSQL e Qdrant.
- `GET /docs`: Swagger/OpenAPI.

O chat responde no idioma da pergunta quando o Ollama esta ativo. As fontes podem estar em ingles; a explicacao pode ser sintetizada no idioma da pergunta sem alterar a referencia original.

## Execucao com Podman

A Podman Machine usada pelo projeto foi recriada com 16 GiB e 6 CPUs:

```powershell
podman machine inspect podman-machine-default
```

Subir os servicos principais:

```powershell
cd C:\Users\mathe\Documents\PROJETO\helpMec
podman compose up -d --build
podman start automotive-ai-ollama
```

Se o Ollama precisar ser recriado:

```powershell
podman rm -f automotive-ai-ollama
podman run -d --name automotive-ai-ollama --network helpmec_automotive_net -p 11434:11434 -v ollama_data:/root/.ollama docker.io/ollama/ollama:latest
```

Validar o backend:

```powershell
Invoke-WebRequest http://localhost:8000/health -UseBasicParsing
podman compose exec -T backend pytest -q
```

Parar sem remover dados:

```powershell
podman compose down
podman stop automotive-ai-ollama
```

Nao use `down -v` ou remova a Podman Machine sem backup.

## Backups

Backups locais da recriacao da Podman Machine ficam em `.podman-backups/` e nao devem ser versionados. Para criar novos backups:

```powershell
New-Item -ItemType Directory -Force .podman-backups | Out-Null
podman volume export helpmec_postgres_data --output .podman-backups/postgres.tar
podman volume export helpmec_qdrant_data --output .podman-backups/qdrant.tar
podman volume export ollama_data --output .podman-backups/ollama.tar
```

## Testes e validacao

Testes locais com Python 3.11:

```powershell
cd backend
C:\Users\mathe\AppData\Local\Python\pythoncore-3.11-64\python.exe -m pytest -q
```

Validacao OpenSpec:

```powershell
openspec validate --changes --json
```

A imagem containerizada deve ser validada com:

```powershell
podman compose exec -T backend pytest -q
```

## Limitacoes conhecidas

- A extracao de PDFs grandes ainda e custosa em CPU e memoria, embora tenha sido movida para threads para manter a API responsiva.
- O cliente Qdrant instalado e mais novo que o servidor Qdrant 1.11.3 e pode emitir warning de compatibilidade.
- A memoria consumida depende do tamanho do PDF, do `pypdf` e do modelo Ollama carregado.
- O historico de chat e mantido em memoria e e perdido ao reiniciar o backend.
- `AUTO_INGEST_FORCE` deve ser desligado depois da reindexacao completa.

## Estrutura de OpenSpec

Mudancas criadas ate agora:

- `agent-chat-frontend`
- `ollama-grounded-chat`
- `containerized-validation`

As mudancas completas ficam em `openspec/changes/` ate serem arquivadas. As especificacoes principais ficam em `openspec/specs/`.
