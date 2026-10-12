---
name: comparar
description: Compara os requisitos da vaga com o CV-mestre e os factos, listando factos relevantes, lacunas e bloqueios em gaps.yaml.
le:
  - cv-mestre.md
  - conquistas.md
  - candidaturas/<empresa-vaga>/vaga.yaml
escreve:
  - candidaturas/<empresa-vaga>/gaps.yaml
contrato_entrada: vaga
contrato_saida: gaps
---

# Comparar

## Quando usar
Depois de `vaga.yaml` validado.

## Entrada
`vaga.yaml`, `cv-mestre.md` e `conquistas.md`. Rode antes `python -m scripts.mestre <dados>`: código 2 (conflito aberto) interrompe esta etapa.

## Saída
`gaps.yaml` com `vaga_url`, `fatos_relevantes[]` (ids de `conquistas.md`), `lacunas[]` (requisitos sem facto) e `bloqueios[]` (o que impede candidatar: facto `desconhecido` necessário, conflito aberto, requisito eliminatório não cumprido). Valide com `validar_contrato gaps`.

## Regras
- Só cite ids que existem em `conquistas.md`.
- Facto `desconhecido` necessário para a vaga vira bloqueio com a pergunta para a pessoa.
- Uma lacuna é honesta: não a preencha com ferramentas ou experiência que o mestre não tem.

## Não faz
Não decide candidatar, não escolhe ângulo, não escreve texto de carta.
