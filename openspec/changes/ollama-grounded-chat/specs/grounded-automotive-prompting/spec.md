## Purpose

Define regras observáveis para que respostas automotivas geradas por LLM permaneçam limitadas às evidências dos manuais, apresentem citações e diferenciem fatos confirmados de hipóteses diagnósticas.

## ADDED Requirements

### Requirement: Evidence-Bounded Prompt
O sistema SHALL instruir o modelo a usar somente os trechos recuperados e SHALL proibir a invenção de torques, especificações, procedimentos, códigos ou referências que não estejam no contexto fornecido.

#### Scenario: Answer Uses Manual Evidence
- **WHEN** o modelo recebe trechos relevantes do manual
- **THEN** a resposta contém uma síntese baseada nesses trechos e não introduz especificações técnicas ausentes nas fontes.

### Requirement: Mandatory Citations
O sistema SHALL exigir que afirmações técnicas sejam acompanhadas de referências às fontes recuperadas, incluindo documento e página quando esses metadados estiverem disponíveis.

#### Scenario: Generated Answer Includes Citations
- **WHEN** uma resposta fundamentada é retornada ao frontend
- **THEN** o payload inclui as citações dos trechos usados, com título do documento, seção e página, sem permitir uma resposta fundamentada com lista de fontes vazia.

### Requirement: Insufficient Evidence
O sistema SHALL evitar a geração de afirmações técnicas quando a recuperação não fornecer evidência suficiente e SHALL informar explicitamente que a resposta não foi verificada nos manuais.

#### Scenario: No Supporting Context
- **WHEN** a busca retorna zero trechos ou resultados abaixo do limiar mínimo de relevância
- **THEN** o sistema não chama o modelo para produzir uma conclusão técnica e retorna uma mensagem de evidência insuficiente com grounding falso.

### Requirement: Fact and Hypothesis Separation
O sistema SHALL marcar diagnósticos inferidos como hipóteses e SHALL separá-los visualmente dos fatos diretamente suportados pelos manuais.

#### Scenario: Hypothesis Is Clearly Labeled
- **WHEN** a resposta inclui uma possibilidade diagnóstica além do procedimento documentado
- **THEN** essa possibilidade é apresentada com um rótulo explícito de hipótese e não é descrita como procedimento confirmado pelo fabricante.
