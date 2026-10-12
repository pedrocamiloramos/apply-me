---
name: qa
description: Verifica o rascunho com os scripts determinísticos e depois faz a revisão de julgamento, gravando qa.yaml.
le:
  - cv-mestre.md
  - conquistas.md
  - candidaturas/<empresa-vaga>/plano.yaml
  - candidaturas/<empresa-vaga>/rascunho.md
escreve:
  - candidaturas/<empresa-vaga>/qa.yaml
contrato_entrada: rascunho
contrato_saida: qa
---

# QA

## Quando usar
Depois de cada versão de `rascunho.md`.

## Entrada
`rascunho.md`, `plano.yaml` e o mestre.

## Saída
`qa.yaml` com `vaga_url`, `estado` (`aprovado` ou `correcoes`), `correcoes[]` (`local`, `mensagem`) e `voltas` (0 a 2). Valide com `validar_contrato qa`.

## Regras
Ordem obrigatória:

1. `python -m scripts.conferir_fatos <dados> candidaturas/<empresa-vaga>`. Código 1: liste cada achado em `correcoes` com o `local` indicado. Código 2: pare e pergunte à pessoa.
2. `python -m scripts.detectar_duplicados <dados>`. Se a carta for quase igual a outra, peça reescrita do ângulo.
3. Só com 1 e 2 limpos, a revisão de julgamento: tom, aderência ao ângulo do plano, clareza, tamanho.

Cada devolução ao `redigir` soma uma volta. Com `voltas` = 2 e ainda com correções, o estado é bloqueado: pare e entregue à pessoa.

## Não faz
Não reescreve a carta, não aprova texto com frase sem facto, não envia.
