# Auditoria de segurança e privacidade — versão 0.1

Data: 2026-10-12. Autoria: a auditoria foi executada por um agente de IA (Claude) a pedido do dono do repositório, sem revisão independente de terceiros.

Este documento diz **o que foi verificado, com que ferramenta e com que resultado**. Não afirma que o projeto é seguro: afirma apenas que, com os controlos abaixo, não foram encontrados dados pessoais, credenciais nem falhas críticas ou altas por resolver. Falhas que ainda não conhecemos podem existir.

## Âmbito

Todo o repositório: código, testes, contratos, skills, exemplos, modelo de dados, documentação, hooks, configuração, dependências e **todo o histórico Git**. Fora do âmbito: o repositório privado de dados de cada pessoa, que nunca faz parte deste projeto.

## Resultado em resumo

| Critério | Resultado |
|---|---|
| Dados pessoais no código, testes, exemplos ou histórico | Nenhum encontrado (ver *Privacidade*) |
| Credenciais válidas no código ou histórico | Nenhuma encontrada; o projeto não usa credenciais |
| Vulnerabilidades críticas ou altas por resolver | Nenhuma encontrada |
| Vulnerabilidades médias | 4 encontradas, 4 corrigidas, cada uma com teste de regressão |
| Vulnerabilidades baixas | 4 encontradas, 4 corrigidas |
| Dependências com vulnerabilidades conhecidas | Nenhuma (`pip-audit`, 2026-10-12) |
| Testes | Todos passam (ver *Controlos executados*) |
| Separação motor / dados privados | `.gitignore` + teste + hook de pré-commit (ver abaixo) |

## Achados e correções

| ID | Gravidade | Achado | Estado |
|---|---|---|---|
| A1 | Média (disponibilidade) | A expressão regular de e-mail testava todas as posições de uma sequência longa: uma só linha de 30 000 caracteres bloqueava a guarda de privacidade e o conferidor durante vários segundos, com crescimento quadrático. | Corrigido: âncora no início do *token* (tempo linear). Testes com 4 formas de entrada hostil, limite de 2 s. |
| A2 | Média (disponibilidade) | A verificação de números de documento comparava cada número com todos os telefones da mesma linha (quadrático): 40 000 números numa linha não terminavam em 60 s. | Corrigido: pesquisa binária nos intervalos. Teste de regressão. |
| A3 | Média (disponibilidade) | Um ficheiro YAML com "bomba de aliases" (poucos KB) num campo previsto no contrato fazia `validar_contrato` não terminar em 20 s. | Corrigido: aliases YAML são recusados em entradas externas (`scripts/yaml_seguro.py`). Testes para contrato, front matter e plano. |
| A4 | Média (integridade) | `registrar` gravava no `log.csv` valores vindos de anúncios sem neutralizar fórmulas (`=`, `+`, `-`, `@`), que o Excel ou o Google Sheets podem executar ao abrir o ficheiro. | Corrigido: prefixo `'` nessas células, idempotente. Testes parametrizados. |
| B1 | Baixa | `assert` a validar um campo obrigatório do CV-mestre (`inicio`): com `inicio` nulo dava *traceback*. | Corrigido: `ValueError` com mensagem. Teste. |
| B2 | Baixa | A guarda de privacidade lia ficheiros inteiros para memória, sem limite. | Corrigido: limite de 2 MiB, ficheiros de texto maiores reprovam com `FICHEIRO_GRANDE`; binários continuam ignorados. Testes. |
| B3 | Baixa | `.gitignore` sem padrões para segredos, chaves e documentos de escritório. | Corrigido; teste verifica os padrões. |
| B4 | Baixa | Dependências sem limites de versão nem versões fixadas. | Corrigido: limites em `pyproject.toml` e `requirements*.txt` fixados; instalação num ambiente novo a partir desses ficheiros foi testada. |
| P1 | Privacidade | Casos de teste de regressão tinham sido derivados de material real. | Substituídos por casos sintéticos e **histórico reescrito antes da primeira publicação**; as varreduras abaixo foram repetidas no resultado. |

## Controlos executados

| Controlo | Âmbito | Resultado |
|---|---|---|
| `pytest` num ambiente novo, instalado só a partir de `requirements-dev.txt` | árvore final | 179 testes passam |
| `pytest` em cada commit do histórico (um *worktree* por commit) | 19 commits | 18 de 18 commits com testes passam; o commit inicial vazio não tem testes |
| `bandit` 1.9.4 | `scripts/` (~900 linhas) | 0 achados. Os testes (`testes/`) não foram analisados: usam `assert` por desenho |
| `pip-audit` 2.10.1 sobre `requirements-dev.txt` | dependências fixadas | "No known vulnerabilities found" (base de dados de 2026-10-12) |
| `detect-secrets` 1.5.0 | todos os ficheiros rastreados | 0 achados |
| Procura de padrões de segredos (`AKIA…`, `ghp_…`, `github_pat_…`, `sk-…`, `xox…`, chaves privadas PEM, `api_key=…`, `password=…`, `token=…`) | blobs de **todos** os commits | 0 ocorrências |
| Procura de termos privados (nomes, e-mails, telefones, empregadores e identificadores da pessoa; lista mantida fora do repositório) | blobs, mensagens, autores, *committers* e nomes de ficheiros de **todos** os commits, e árvore de trabalho | só ocorrem `linkedin.com` em URLs de teste genéricos e o identificador público do dono no GitHub (`README.md` e autoria dos commits) |
| Guarda de privacidade (`verificar_privacidade`) sobre a árvore | todos os ficheiros de texto | passa (teste `test_repo_sem_dados_pessoais`) |
| Procura de chamadas perigosas em `scripts/` | `os.system`, `eval`, `exec`, `yaml.load`, `shell=True`, `__import__`, `input` | nenhuma; o YAML é lido só com `yaml.safe_load` (e `yaml.parse` com `SafeLoader` para recusar aliases) |
| Procura de acesso à rede em `scripts/` | importações de `requests`, `urllib.request`, `urllib3`, `http`, `socket`, `ssl`, `smtplib`, `ftplib`, `httpx`, `aiohttp`, `subprocess`, `ctypes`, `pickle` | nenhuma. O único `urllib` é `urllib.parse`, usado para normalizar o texto de URLs sem abri-las: os scripts não fazem pedidos de rede nem enviam dados |
| Sondagem de ReDoS e de entradas hostis (linhas de 30 000 a 1 000 000 de caracteres, todas processadas em menos de 0,4 s depois das correções; bomba de aliases, delimitador de CSV errado, front matter malformado) | guarda de privacidade, conferidor, validador, registo | os casos que falhavam foram corrigidos (A1–A3); os restantes terminam com mensagem de erro e sem *traceback* |
| Revisão manual de escrita em ficheiros | `registrar`, `gerar_funil`, `gerar_adaptador_claude`, `instalar_hooks.sh` | `registrar` escreve de forma atómica (ficheiro temporário + `os.replace`) e recusa `log.csv` com cabeçalho inesperado; o adaptador deriva caminhos de nomes de pastas, sem *path traversal* |
| Teste funcional dos hooks num clone de ensaio | `pre-commit`, `commit-msg` | e-mail real, telefone real (também em ficheiro renomeado) e mensagem fora do padrão são recusados; commit limpo passa |
| Higiene do repositório | tipos e modos de ficheiros | só texto; sem ligações simbólicas; só os 3 *scripts* de shell são executáveis; sem ficheiros `.pdf`, `.docx`, `.env`, chaves |
| Workflows e CI | `.github/` | não existe: não há permissões de CI a rever (e também não há CI; ver *Limites*) |

Os comandos são reproduzíveis: `pip install bandit pip-audit detect-secrets` e executar cada um sobre o repositório.

## Separação entre o motor e os dados privados

- O `.gitignore` bloqueia `carreira-dados/`, `candidaturas/`, `log.csv`, `funil.md`, `cv-mestre.md` e `conquistas.md` na raiz, PDF, DOCX, `.env`, chaves e *tokens*.
- O teste `test_repositorio_publico_nao_rastreia_dados_privados` falha se algum ficheiro desses tipos for rastreado; `test_gitignore_protege_dados_e_segredos` falha se os padrões forem removidos.
- O hook de pré-commit corre a guarda de privacidade sobre os ficheiros em *stage*.
- O `AGENTS.md` obriga a usar sempre caminhos dentro da pasta privada de dados.

## Limites desta auditoria

- **Heurísticas.** A guarda de privacidade reconhece formatos conhecidos de telefone, e-mail e números de documento; não deteta moradas, nomes próprios ou texto reconhecível de cartas.
- **Sem revisão independente.** Foi um único agente de IA com as ferramentas acima. Não houve revisão de terceiros, teste de intrusão, nem *fuzzing* sistemático além das sondagens manuais descritas.
- **Cobertura de ferramentas.** O `bandit` correu só sobre `scripts/`. Não foi usada outra ferramenta de análise estática, e o `pip-audit` só conhece vulnerabilidades já publicadas.
- **Sem CI.** As verificações correm na máquina de quem as executa; nada impede que um *pull request* futuro as ignore.
- **Entradas ainda sem limite de tamanho.** Só a guarda de privacidade limita o tamanho dos ficheiros. Os outros leitores (`mestre`, `conferir_fatos`, `registrar`, `detectar_duplicados`) leem ficheiros inteiros: um ficheiro enorme no repositório privado de dados pode esgotar a memória local (ver *Roadmap*).
- **Integridade dos dados, não segurança.** O CV-mestre aceita hoje `fim` anterior a `inicio` e datas no futuro (ver *Roadmap*).
- **Agentes de IA.** Nenhum código impede por completo que um agente obedeça a instruções escondidas num anúncio. O `AGENTS.md` (regra 8) manda tratar anúncios como dado não confiável e a regra de ouro (nenhum agente envia) limita o dano, mas não o elimina.
- **Plataformas.** Testado em Linux com Python 3.13. Outras plataformas e versões (3.11, 3.12, Windows, macOS) não foram exercitadas.
- **Estado no tempo.** O resultado vale para o commit auditado e para as bases de dados de vulnerabilidades de 2026-10-12.
