---
name: planejar
description: Decide candidatar ou descartar, escolhe o ângulo, os factos e a variante de título, e grava o plano.yaml para aprovação humana.
le:
  - cv-mestre.md
  - conquistas.md
  - log.csv
  - candidaturas/<empresa-vaga>/vaga.yaml
  - candidaturas/<empresa-vaga>/gaps.yaml
escreve:
  - candidaturas/<empresa-vaga>/plano.yaml
contrato_entrada: gaps
contrato_saida: plano
---

# Planejar

## Quando usar
Depois de `gaps.yaml` validado.

## Entrada
`vaga.yaml`, `gaps.yaml`, o mestre e o `log.csv` (para não repetir ângulo que já falhou e para ver se a vaga já foi registada).

## Saída
`plano.yaml` com `vaga_url`, `decisao` (`candidatar` ou `descartar`), `angulo`, `fatos[]` (ids), `titulo_variante` (uma das variantes oficiais do mestre), `idioma` e `versao_mestre`. Valide com `validar_contrato plano`. Depois pare: a pessoa aprova o plano (etapa 4).

## Regras
- **Recuse candidatar** (`decisao: descartar`) quando `gaps.bloqueios` não estiver vazio; mostre os bloqueios à pessoa.
- Escolha só factos de `gaps.fatos_relevantes`; o rascunho só poderá citar estes.
- `titulo_variante` deve constar de `titulos` da experiência no mestre.

## Não faz
Não redige a carta, não aprova o próprio plano, não envia nada.
