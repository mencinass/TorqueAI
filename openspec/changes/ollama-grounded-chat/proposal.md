## Why

O chat já recupera trechos dos manuais, mas ainda não transforma essa evidência em respostas naturais e contextualizadas. Integrar um LLM Ollama local agora permite oferecer uma experiência conversacional útil sem enviar dados técnicos para serviços externos, mantendo o RAG como fonte obrigatória.

## What Changes

- Adiciona um provedor de geração de texto via API HTTP local do Ollama.
- Envia ao modelo somente a pergunta, o contexto recuperado do Qdrant e o histórico relevante da sessão.
- Define um prompt automotivo que obriga respostas baseadas nas fontes, com citações e distinção entre fatos verificados e hipóteses.
- Expõe configuração para URL, modelo, timeout e parâmetros de geração do Ollama.
- Mantém fallback seguro quando o Ollama estiver indisponível ou quando o RAG não encontrar evidência suficiente.
- Atualiza a resposta do chat para conter texto sintetizado, status de grounding e fontes originais.

## Capabilities

### New Capabilities

- `ollama-chat-generation`: geração local de respostas conversacionais usando o Ollama com contexto recuperado do RAG.
- `grounded-automotive-prompting`: regras de prompt, citações obrigatórias e tratamento de ausência de evidência.

### Modified Capabilities

<!-- No existing main capability requirements are modified; the active chat change will consume these capabilities. -->

## Impact

- Afeta `backend/app/services/chat_service.py`, o novo módulo de geração Ollama, schemas e endpoint de chat.
- Adiciona configurações `OLLAMA_BASE_URL`, modelo de chat, timeout e parâmetros de geração.
- Requer um Ollama local acessível, com um modelo de chat instalado; testes devem usar um fake HTTP ou provider determinístico.
- Não adiciona SDK nativo nem dependência externa de LLM: a comunicação será feita com `httpx`.
- Respostas técnicas continuam sujeitas à política de zero alucinação: sem evidência recuperada, o sistema não deve afirmar procedimentos, torques ou especificações.
