from pathlib import Path

from scripts.mestre import Status, carregar_mestre, validar_mestre
from scripts.resultado import Estado
from scripts.verificar_privacidade import verificar_arvore

RAIZ = Path(__file__).resolve().parent.parent
TEMPLATE = RAIZ / "template-dados"


def test_template_carrega_e_valida():
    mestre = carregar_mestre(TEMPLATE)
    assert validar_mestre(mestre).estado is Estado.PASSOU
    assert mestre.experiencias and mestre.fatos


def test_template_comeca_com_todos_os_factos_desconhecidos():
    assert {f.status for f in carregar_mestre(TEMPLATE).fatos} == {Status.DESCONHECIDO}


def test_template_traz_config_e_gitignore():
    assert (TEMPLATE / "config.yaml").is_file() and (TEMPLATE / ".gitignore").is_file()


def test_repo_sem_dados_pessoais():
    assert verificar_arvore(RAIZ).estado is Estado.PASSOU


def test_readme_cobre_o_essencial():
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    for trecho in ("```mermaid", "template-dados", "carreira-dados", "revisão de tom", "exemplos/ana-exemplo"):
        assert trecho in texto, trecho


def test_spec_nao_foi_copiada_para_o_repositorio():
    assert not list(RAIZ.glob("**/*sistema-agentes-carreira-design*"))
