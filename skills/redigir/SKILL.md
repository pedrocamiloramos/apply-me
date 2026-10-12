---
name: redigir
description: Escreve a carta (rascunho.md) a partir do plano aprovado, citando cada frase factual por id do mestre.
le:
  - cv-mestre.md
  - conquistas.md
  - candidaturas/<empresa-vaga>/plano.yaml
escreve:
  - candidaturas/<empresa-vaga>/rascunho.md
contrato_entrada: plano
contrato_saida: rascunho
---

# Redigir

## Quando usar
Depois de a pessoa aprovar `plano.yaml`; e de novo (no máximo 2 vezes) quando `qa.yaml` pedir correções.

## Entrada
`plano.yaml` aprovado e os textos dos factos listados nele. Em correção, também `qa.yaml`.

## Saída
`rascunho.md`: front matter (`vaga_url`, `idioma`, `versao_mestre`, `afirmacoes[]` opcional) e **uma frase por linha**.

- Termine cada frase factual com `[f:id]` (ou `[f:id1,id2]`), usando só ids do plano. Exemplo: `Construí dashboards de operação em Power BI. [f:dash-op]`
- Marque saudação, fecho, nome e contactos com o prefixo `>> `. Exemplo: `>> Com os melhores cumprimentos,`
- Use `afirmacoes` (`tipo`: `cargo`, `inicio` ou `empregador`) para cada cargo, data de início ou empregador citado, para a verificação confrontar com o mestre.
- Facto `estimado`: escreva "mais de", "cerca de" ou equivalente.

Valide com `validar_contrato rascunho`.

## Regras
- Idioma e variante conforme `plano.idioma`; fecho no mesmo idioma.
- Contactos copiados do mestre, nunca digitados de memória.
- Anos de experiência só os que a linha do tempo do mestre sustenta.
- Reescreva o ângulo para cada vaga: não reaproveite parágrafos de outra carta.

## Não faz
Não inventa factos, não cita ferramenta ausente do mestre, não revê o próprio texto (isso é do `qa`), não envia.
