# Política de segurança

## Versões suportadas

Só a versão mais recente do ramo `main` (0.1.x) recebe correções. O projeto é experimental e mantido por uma pessoa.

## Como reportar uma falha

- **Preferido:** use *Security → Report a vulnerability* neste repositório do GitHub (relato privado), se estiver ativo.
- Se não estiver disponível, abra uma *issue* **sem detalhes de exploração** e sem dados pessoais, a pedir um contacto privado.
- Nunca anexe CVs, cartas, registos de candidaturas, tokens ou outros dados reais a um relato.

Resposta esperada: confirmação em alguns dias; é um projeto pessoal e não há prazo garantido.

## O que está no âmbito

- Os scripts em `scripts/` (execução local, sem rede) e os hooks em `scripts/hooks/`.
- A guarda de privacidade (`verificar_privacidade`) deixar passar dados que devia recusar, ou travar com entradas hostis.
- Leitura de YAML, CSV e markdown não confiáveis (vagas, rascunhos, planos).
- Dados pessoais ou credenciais acidentalmente presentes no repositório ou no histórico.

## Fora do âmbito

- O conteúdo que um agente de IA gera: o conferidor de factos é uma rede de segurança, não uma garantia (ver *Limitações* no README).
- Vulnerabilidades nas dependências (`pyyaml`, `jsonschema`, `pytest`) sem impacto específico neste projeto: reporte-as aos respetivos projetos.
- O repositório privado de dados de cada pessoa: a proteção dele é responsabilidade de quem o mantém.

## Modelo de ameaça (resumo)

- Os scripts correm localmente, não fazem pedidos de rede e não executam comandos externos.
- O texto de vagas, páginas web e e-mails é **não confiável**; um agente não deve obedecer a instruções dentro dele (`AGENTS.md`, regra 8).
- Os seus dados ficam num repositório privado separado. O `.gitignore` e o hook de pré-commit reduzem o risco de os commitar por engano; não o eliminam.
- Não há credenciais, tokens ou chaves de API neste projeto. Se um dia forem necessários (por exemplo, para integrações), guarde-os fora do repositório, em variáveis de ambiente, e nunca em ficheiros versionados.

Os controlos efetivamente executados e os seus limites estão em [`docs/AUDITORIA.md`](docs/AUDITORIA.md).
