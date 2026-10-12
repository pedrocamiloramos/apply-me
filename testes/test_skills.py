from pathlib import Path

import pytest

from scripts.frontmatter import separar

RAIZ = Path(__file__).resolve().parent.parent
SKILLS = ("ler-vaga", "comparar", "planejar", "redigir", "qa", "registrar", "funil")
CAMPOS = ("name", "description", "le", "escreve", "contrato_entrada", "contrato_saida")
SECOES = ("## Quando usar", "## Entrada", "## Saída", "## Regras", "## Não faz")
CONTRATOS = {p.name.removesuffix(".schema.yaml") for p in (RAIZ / "contratos").glob("*.schema.yaml")}
CAND = "candidaturas/<empresa-vaga>/"
ESCREVE = {
    "ler-vaga": [CAND + "vaga.yaml"],
    "comparar": [CAND + "gaps.yaml"],
    "planejar": [CAND + "plano.yaml"],
    "redigir": [CAND + "rascunho.md"],
    "qa": [CAND + "qa.yaml"],
    "registrar": ["log.csv"],
    "funil": ["funil.md"],
}


def _skill(nome: str):
    return separar((RAIZ / "skills" / nome / "SKILL.md").read_text(encoding="utf-8"))


@pytest.mark.parametrize("nome", SKILLS)
def test_sete_skills_com_front_matter_completo(nome):
    meta, corpo = _skill(nome)
    assert all(c in meta for c in CAMPOS), meta.keys()
    assert meta["name"] == nome and len(meta["description"]) > 20
    assert isinstance(meta["le"], list) and isinstance(meta["escreve"], list)
    for secao in SECOES:
        assert secao in corpo, f"{nome}: falta {secao}"


@pytest.mark.parametrize("nome", SKILLS)
def test_contratos_referenciados_existem(nome):
    meta, _ = _skill(nome)
    for campo in ("contrato_entrada", "contrato_saida"):
        assert meta[campo] is None or meta[campo] in CONTRATOS


@pytest.mark.parametrize("nome", SKILLS)
def test_nenhuma_skill_escreve_fora_da_candidatura_log_ou_funil(nome):
    meta, _ = _skill(nome)
    assert meta["escreve"] == ESCREVE[nome]
    assert not any(p.startswith("/") or ".." in p for p in meta["escreve"] + meta["le"])


def test_o_contrato_de_saida_bate_com_o_artefato_escrito():
    for nome in ("ler-vaga", "comparar", "planejar", "redigir", "qa"):
        meta, _ = _skill(nome)
        assert Path(meta["escreve"][0]).stem == meta["contrato_saida"]


def test_agents_md_declara_regras_imutaveis():
    texto = (RAIZ / "AGENTS.md").read_text(encoding="utf-8")
    for trecho in ("nenhum agente envia", "2 voltas", "desconhecido", "conferir_fatos", "detectar_duplicados", "gerar_funil"):
        assert trecho in texto, trecho
    for nome in SKILLS:
        assert f"skills/{nome}" in texto


def test_redigir_e_qa_e_planejar_trazem_as_instrucoes_do_brief():
    redigir = _skill("redigir")[1]
    assert "[f:" in redigir and ">> " in redigir
    qa = _skill("qa")[1]
    assert qa.index("conferir_fatos") < qa.index("detectar_duplicados") < qa.lower().index("julgamento")
    assert "bloqueios" in _skill("planejar")[1]
