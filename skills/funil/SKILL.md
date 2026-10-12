---
name: funil
description: Gera o funil.md com a taxa de resposta por ângulo e tipo de vaga a partir do log.csv e sugere ajustes.
le:
  - log.csv
escreve:
  - funil.md
contrato_entrada: null
contrato_saida: null
---

# Funil

## Quando usar
Periodicamente (por exemplo semanal) ou quando a pessoa quiser saber o que está a funcionar.

## Entrada
`log.csv`.

## Saída
`python -m scripts.gerar_funil log.csv funil.md`. Depois, em conversa, resuma o que o funil mostra e sugira no máximo três ajustes.

## Regras
- Grupos marcados "amostra pequena" (menos de 5 enviadas) não sustentam conclusões; diga isso.
- `funil.md` é gerado: não edite à mão.

## Não faz
Não altera o `log.csv`, não muda o mestre, não envia nada.
