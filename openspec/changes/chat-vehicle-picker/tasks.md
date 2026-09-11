## 1. Opções de veículo/sistema (backend)

- [x] 1.1 Adicionar endpoint que lista gerações com documentos cadastrados (ex.: `/api/v1/vehicles/picker`), retornando código de geração legível para o dropdown.
- [x] 1.2 Adicionar a lista de sistemas disponíveis derivada dos documentos (valores de `system` distintos).
- [x] 1.3 Testar os endpoints de opções (unit).

## 2. Frontend: dropdowns

- [x] 2.1 Substituir inputs de texto "Geração"/"Sistema" por `<select>` populados via fetch no carregamento.
- [x] 2.2 Incluir opção "Todos" (vazio) para busca sem filtro.
- [x] 2.3 Enviar os valores selecionados no `POST /api/v1/chat/messages` como antes.

## 3. Frontend: thumbnails como hyperlink expansível

- [x] 3.1 Renderizar cada citação como um link compacto (texto "p. N" ou título) em vez de uma grade de imagens.
- [x] 3.2 Ao clicar, abrir um **modal** com a imagem ampliada (ou nova aba) para leitura do conteúdo da página.
- [x] 3.3 Garantir legibilidade da imagem ampliada (altura/dimensões adequadas) e fechamento do modal.

## 4. Validação

- [x] 4.1 `pytest` verde.
- [x] 4.2 Validar visualmente dropdown e modal no navegador (subir stack).
- [x] 4.3 `openspec validate --changes --json`.