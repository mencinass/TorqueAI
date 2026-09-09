## Context

O backend já possui `ChatService`, embeddings e busca de chunks no Qdrant, além de um frontend que consome `POST /api/v1/chat/messages`. A geração atual é extrativa: devolve os trechos recuperados diretamente. Esta mudança adiciona uma etapa opcional de síntese local, preservando a resposta segura quando não há evidência ou quando o Ollama falha.

## Goals / Non-Goals

**Goals:**
- Encapsular a comunicação com Ollama em um provider assíncrono substituível.
- Enviar contexto delimitado e metadados de citação ao modelo.
- Garantir que perguntas sem evidência não acionem geração técnica.
- Manter respostas e testes determinísticos sem exigir Ollama durante CI.

**Non-Goals:**
- Adicionar SDK oficial de LLM ou bibliotecas nativas.
- Permitir pesquisa na internet ou conhecimento externo ao RAG.
- Implementar streaming de tokens nesta primeira integração.
- Persistir conversas em PostgreSQL nesta mudança.

## Decisions

### Decision 1: HTTP compatível com Ollama
- **Chosen Approach**: Implementar um provider com `httpx.AsyncClient` chamando `POST /api/chat`, com `model`, `messages`, `stream: false` e opções configuráveis.
- **Rationale**: Mantém o backend Python-only, usa a dependência HTTP já existente e facilita testes com `httpx.MockTransport`.
- **Alternative Rejected**: SDK oficial ou integração direta com runtime local, pois adicionaria dependências e acoplamento desnecessários.

### Decision 2: Pipeline de geração após recuperação
- **Chosen Approach**: O serviço recupera os chunks, aplica limiar de relevância, monta o prompt e só então chama Ollama.
- **Rationale**: Evita usar o modelo como fonte de conhecimento e reduz chamadas inúteis.
- **Alternative Rejected**: Enviar a pergunta diretamente ao modelo, pois viola o grounding exigido para procedimentos automotivos.

### Decision 3: Prompt estruturado e contexto delimitado
- **Chosen Approach**: Usar mensagem de sistema fixa com regras de segurança e mensagem de usuário contendo pergunta, veículo e blocos de fonte numerados.
- **Rationale**: Separa instruções de dados recuperados, facilita auditoria e permite validar a presença das fontes no provider.
- **Alternative Rejected**: Prompt livre montado no frontend, pois permitiria alterar as regras de segurança no cliente.

### Decision 4: Fallback explícito
- **Chosen Approach**: Preservar `grounded=false` e a mensagem de evidência insuficiente sem chamar Ollama quando não houver chunks válidos; retornar HTTP 503 para indisponibilidade do provider.
- **Rationale**: Diferencia ausência de conhecimento do RAG de falha operacional e impede respostas inventadas.
- **Alternative Rejected**: Responder com texto genérico do modelo em ambos os casos, pois mascara a causa e pode gerar instruções não verificadas.

## Risks / Trade-offs

- **[Risk]** Ollama local pode estar desligado ou sem o modelo instalado.
  - **Mitigation**: Timeout finito, erro 503, health check opcional e provider fake nos testes.
- **[Risk]** O modelo pode ignorar as instruções de grounding.
  - **Mitigation**: Contexto delimitado, prompt explícito, validação de citações no resultado e exibição das fontes originais no payload.
- **[Risk]** Modelos diferentes podem retornar formatos ou níveis de qualidade distintos.
  - **Mitigation**: Validar o JSON mínimo (`message.content`), configurar modelo por ambiente e manter fallback extrativo como estratégia controlada.

## Migration Plan

1. Adicionar configurações do modelo de chat com defaults locais e manter o provider extrativo como fallback configurável.
2. Implementar o provider Ollama, prompt builder e integração no `ChatService`.
3. Atualizar schemas, frontend e testes com transportes HTTP falsos.
4. Validar com Ollama local e modelo instalado antes de ativar o provider por padrão em ambiente de desenvolvimento.
5. Reverter definindo o provider de chat como extrativo ou desativando a geração, sem alterar os dados já indexados.
