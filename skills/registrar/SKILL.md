---
name: registrar
description: Regista ou atualiza a candidatura no log.csv depois de a pessoa a enviar, sem duplicar a vaga.
le:
  - candidaturas/<empresa-vaga>/plano.yaml
  - log.csv
escreve:
  - log.csv
contrato_entrada: qa
contrato_saida: null
---

# Registrar

## Quando usar
Depois de `qa.yaml` aprovado e de a **pessoa** ter enviado a candidatura; e quando chegar uma resposta (atualiza a linha).

## Entrada
Os dados da vaga e do plano, e o `status` informado pela pessoa (`rascunho`, `enviada`, `resposta`, `entrevista`, `oferta`, `rejeitada`).

## Saída
Uma linha em `log.csv`: `python -m scripts.registrar log.csv url=… empresa=… vaga=… data=… angulo=… versao_mestre=… tipo_vaga=… status=…`. A chave é a URL normalizada; repetir a URL atualiza a linha.

## Regras
- Só registe `enviada` quando a pessoa disser que enviou.
- Campo desconhecido é rejeitado pelo script; não o contorne.

## Não faz
Não envia candidaturas, não edita outras linhas, não gera relatório.
