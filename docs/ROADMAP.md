# Roadmap

Lista priorizada do que fica para as próximas versões. Nada disto está implementado na 0.1; o que existe e o que falta está descrito sem exagero nas *Limitações* do [README](../README.md).

Prioridade: **P1** = reduz risco de enviar uma carta errada ou de expor dados; **P2** = melhora a utilidade; **P3** = conforto.

## P1

1. **Limites do conferidor de factos** (`conferir_fatos`). Hoje só apanha o que está em listas e padrões.
   - Extrair do corpo as ferramentas, cargos e empregadores citados e comparar com o CV-mestre, em vez de depender só de `afirmacoes` declaradas pelo agente.
   - Detetar frases noutro idioma com um modelo de língua leve, em vez de palavras funcionais.
   - Normalizar números e unidades (por exemplo "1,5 milhões" contra "1 500 000") antes de os comparar com o facto citado.
   - Testes de regressão para cada classe de erro nova, com casos sintéticos.
2. **Ferramentas e competências fora do vocabulário** (`scripts/vocabulario.yaml`).
   - Quando uma ferramenta ou competência aparece no texto e não está no vocabulário nem no mestre, **bloquear com pergunta** em vez de passar em silêncio.
   - Permitir que a pessoa estenda o vocabulário a partir do seu repositório privado, sem editar o motor.
3. **Proteção de dados e validação de entradas** (parte já feita na 0.1: limite de 2 MiB na guarda de privacidade, YAML sem aliases, fórmulas de CSV neutralizadas).
   - Aplicar o mesmo limite de tamanho a todas as leituras (`mestre`, `conferir_fatos`, `registrar`, `detectar_duplicados`, `validar_contrato`).
   - Neutralizar markdown e HTML vindos de anúncios em `funil.md`.
   - Alargar a guarda de privacidade: moradas, IBAN/NIF com dígitos de controlo, URLs de perfis pessoais, ficheiros de formatos não texto (PDF/DOCX) com um aviso em vez de os ignorar.
   - Verificação opcional da guarda sobre o histórico (`git log -p`) antes de um *push*.
4. **Validação de datas e intervalos** no CV-mestre e no log.
   - Hoje `fim` anterior a `inicio` e `inicio` no futuro passam sem aviso e distorcem os anos de experiência calculados.
   - Detetar sobreposições suspeitas, buracos longos, datas do log fora de ordem ou no futuro e formatos mistos.
5. **Mais testes de regressão**: um por cada achado desta auditoria já existe em `testes/test_revisao_final.py` e `testes/test_yaml_seguro.py`; acrescentar testes de propriedades (Hypothesis) para os analisadores de texto e testes de desempenho com entradas grandes e hostis.

## P2

6. **Deteção de duplicados.**
   - Hoje compara só rascunhos locais por semelhança textual (limiar 0,8).
   - Acrescentar: mesma vaga em portais diferentes (empresa + título + local), vaga republicada, mesma carta com poucas palavras trocadas, e um relatório com o motivo de cada par.
7. **Integração com o Notion** (espelho opcional do `log.csv`; a fonte de verdade continua a ser o ficheiro local).
   - **Uma vaga por registo**, com chave estável (URL normalizada) e atualização idempotente.
   - Execução em modo de simulação por omissão, com pré-visualização do que seria escrito.
   - Credencial só por variável de ambiente, com permissões mínimas, nunca em ficheiros; sem enviar CVs nem cartas, só campos de acompanhamento (empresa, vaga, estado, datas).
   - Tratar o conteúdo vindo do Notion como não confiável.
8. **CI no GitHub** com permissões mínimas (`contents: read`): testes em Python 3.11 a 3.13, `pip-audit`, `bandit` e verificação de privacidade em cada *pull request*, mais Dependabot para as dependências fixadas.

## P3

9. Empacotar como comando (`apply-me …`) em vez de `python -m scripts.…`.
10. Hashes nos ficheiros `requirements*.txt`.
11. Suporte a mais idiomas de carta e vocabulários por setor.
12. Relatório de funil com mais métricas (tempo até resposta, taxa por ângulo).
