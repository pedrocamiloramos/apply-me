from dataclasses import replace
from datetime import date
from pathlib import Path

import yaml

from scripts.conferir_fatos import conferir_rascunho, detectar_idioma, main, parsear_rascunho
from scripts.mestre import Conflito, Experiencia, Fato, Mestre, Status
from scripts.resultado import Estado

HOJE = date(2026, 10, 12)  # a: 51 meses (energia), b: 14 meses (vendas) -> 5 anos no total, 4 em energia


def _fato(id_: str, status: Status = Status.CONFIRMADO) -> Fato:
    return Fato(id_, "a", status, "CV exemplo", ("dados",), {"pt": "texto", "en": "text"})


MESTRE = Mestre(
    versao="1.0",
    contactos={"email": "ana@exemplo.invalid", "telefone": "+351 900 000 000"},
    idiomas={"espanhol": "B2"},
    ferramentas={"Python": "CV exemplo", "Power BI": "CV exemplo"},
    experiencias=(
        Experiencia("a", "Empresa A", "energia", {"pt": ("Analista de Dados",), "en": ("Data Analyst",)},
                    date(2022, 7, 1), None),
        Experiencia("b", "Empresa B", "vendas", {"pt": ("Vendedora",), "en": ("Sales Rep",)},
                    date(2020, 3, 1), date(2021, 5, 1)),
    ),
    fatos=(_fato("f1"), _fato("f2"), _fato("f3"), _fato("est", Status.ESTIMADO), _fato("desc", Status.DESCONHECIDO)),
    conflitos=(),
)
PLANO = {"fatos": ["f1", "f2", "est", "desc"]}


def _rascunho(linhas: list[str], idioma: str = "pt-PT", afirmacoes: list[dict] | None = None):
    meta = {"vaga_url": "u", "idioma": idioma, "versao_mestre": "1.0"}
    if afirmacoes:
        meta["afirmacoes"] = afirmacoes
    return parsear_rascunho("---\n" + yaml.safe_dump(meta) + "---\n" + "\n".join(linhas) + "\n")


def _codigos(r) -> list[str]:
    return [a.codigo for a in r.achados]


def _conferir(linhas, idioma="pt-PT", mestre=MESTRE, plano=PLANO, afirmacoes=None):
    return conferir_rascunho(_rascunho(linhas, idioma, afirmacoes), mestre, plano, HOJE)


def test_parsear_rascunho_separa_frases_e_ignora_linhas_vazias():
    r = _rascunho([">> Dear team,", "", "Fiz análise. [f:f1, f2]", "Sem fato"])
    assert [(f.numero, f.formulaica, f.ids) for f in r.frases] == [(1, True, ()), (2, False, ("f1", "f2")), (3, False, ())]
    assert r.frases[1].texto == "Fiz análise."


def test_frase_sem_fato_reprova():
    r = _conferir(["Sou dedicada ao trabalho"])
    assert r.estado is Estado.REPROVOU and _codigos(r) == ["FRASE_SEM_FATO"]
    assert r.achados[0].local == "frase 1"


def test_formulaica_dispensa_fato():
    assert _conferir([">> Com os melhores cumprimentos,"]).estado is Estado.PASSOU


def test_fato_inexistente_e_fora_do_plano():
    assert _codigos(_conferir(["Fiz algo [f:zzz]"])) == ["FATO_INEXISTENTE"]
    assert _codigos(_conferir(["Fiz algo [f:f3]"])) == ["FATO_FORA_DO_PLANO"]


def test_fato_desconhecido_bloqueia():
    r = _conferir(["Fiz algo [f:desc]"])
    assert r.estado is Estado.BLOQUEADO and _codigos(r) == ["FATO_DESCONHECIDO"]


def test_estimado_exige_aproximacao():
    assert _codigos(_conferir(["Fiz 10 dashboards [f:est]"])) == ["ESTIMADO_SEM_APROXIMACAO"]
    assert _conferir(["Fiz mais de 10 dashboards [f:est]"]).estado is Estado.PASSOU
    assert _conferir(["Built over 10 dashboards [f:est]"], idioma="en").estado is Estado.PASSOU


def test_ferramenta_sem_fonte():
    r = _conferir(["Uso Lean, BPM e Python [f:f1]"])
    assert _codigos(r) == ["FERRAMENTA_SEM_FONTE", "FERRAMENTA_SEM_FONTE"]
    assert {a.mensagem for a in r.achados} == {"ferramenta sem fonte no mestre: Lean", "ferramenta sem fonte no mestre: BPM"}


def test_anos_divergentes():
    assert _codigos(_conferir(["Tenho mais de 6 anos de experiência [f:f1]"])) == ["ANOS_DIVERGENTES"]
    assert _codigos(_conferir(["I have 7 years of experience [f:f1]"], idioma="en")) == ["ANOS_DIVERGENTES"]


def test_anos_coerentes_com_o_total_ou_com_um_setor():
    assert _conferir(["Tenho mais de três anos de experiência [f:f1]"]).estado is Estado.PASSOU
    assert _conferir(["Tenho 5 anos de experiência [f:f1]"]).estado is Estado.PASSOU
    assert _conferir(["Tenho 4 anos em energia [f:f1]"]).estado is Estado.PASSOU
    assert _conferir(["Over three years of experience [f:f1]"], idioma="en").estado is Estado.PASSOU


def test_cargo_fora_das_variantes_oficiais():
    errada = [{"tipo": "cargo", "experiencia": "a", "valor": "Cientista de Dados"}]
    certa = [{"tipo": "cargo", "experiencia": "a", "valor": "Analista de Dados"}]
    assert _codigos(_conferir(["Fiz algo [f:f1]"], afirmacoes=errada)) == ["AFIRMACAO_DIVERGENTE"]
    assert _conferir(["Fiz algo [f:f1]"], afirmacoes=certa).estado is Estado.PASSOU


def test_inicio_e_empregador_divergentes():
    afirmacoes = [
        {"tipo": "inicio", "experiencia": "a", "valor": "2022-03"},
        {"tipo": "empregador", "experiencia": "a", "valor": "Outra Empresa"},
        {"tipo": "empregador", "experiencia": "inexistente", "valor": "X"},
    ]
    assert _codigos(_conferir(["Fiz algo [f:f1]"], afirmacoes=afirmacoes)) == ["AFIRMACAO_DIVERGENTE"] * 3


def test_inicio_correto_passa():
    afirmacoes = [{"tipo": "inicio", "experiencia": "a", "valor": "2022-07"}]
    assert _conferir(["Fiz algo [f:f1]"], afirmacoes=afirmacoes).estado is Estado.PASSOU


def test_conflito_aberto_na_afirmacao_bloqueia():
    mestre = replace(MESTRE, conflitos=(Conflito("a.inicio", ("2022-03", "2022-07"), False),))
    afirmacoes = [{"tipo": "inicio", "experiencia": "a", "valor": "2022-07"}]
    r = _conferir(["Fiz algo [f:f1]"], mestre=mestre, afirmacoes=afirmacoes)
    assert r.estado is Estado.BLOQUEADO and _codigos(r) == ["CONFLITO_ABERTO"]


def test_contacto_diferente_do_mestre():
    assert _codigos(_conferir([">> outra@exemplo.invalid"])) == ["CONTACTO_DIVERGENTE"]
    assert _codigos(_conferir([">> +351 900 000 111"])) == ["CONTACTO_DIVERGENTE"]  # privacidade:ignorar
    assert _conferir([">> ana@exemplo.invalid", ">> +351 900 000 000"]).estado is Estado.PASSOU


def test_idioma_do_fecho_diferente_reprova():
    r = _conferir(["Fiz análise de dados para a equipe [f:f1]", ">> Kind regards,"], idioma="pt-BR")
    assert _codigos(r) == ["IDIOMA_ERRADO"] and r.achados[0].local == "frase 2"


def test_variante_do_portugues_diferente_reprova():
    r = _conferir(["Atualmente lidero a equipe de dados [f:f1]"], idioma="pt-PT")
    assert _codigos(r) == ["IDIOMA_ERRADO"]


def test_detectar_idioma():
    assert detectar_idioma("Kind regards,") == "en"
    assert detectar_idioma("Dear Hiring Team,") == "en"
    assert detectar_idioma("Prezada Equipe de Recrutamento,") == "pt-BR"
    assert detectar_idioma("Prezada equipa de recrutamento para o ficheiro") == "pt-PT"
    assert detectar_idioma("Fiz análise de dados para a vaga") == "pt"
    assert detectar_idioma("Ana Exemplo") == "indeterminado"


def test_rascunho_valido_completo_passa():
    linhas = [
        ">> Prezada equipa de recrutamento,",
        "Lidero a análise de dados com Python e Power BI desde 2022. [f:f1]",
        "Construí mais de 10 dashboards para a equipa. [f:est]",
        ">> Com os melhores cumprimentos,",
        ">> ana@exemplo.invalid",
    ]
    afirmacoes = [{"tipo": "cargo", "experiencia": "a", "valor": "Analista de Dados"}]
    assert _conferir(linhas, afirmacoes=afirmacoes).estado is Estado.PASSOU


def _pasta_cli(tmp_path: Path, plano_fatos: list[str]) -> tuple[Path, Path]:
    dados, cand = tmp_path / "dados", tmp_path / "dados" / "candidaturas" / "x"
    cand.mkdir(parents=True)
    (dados / "cv-mestre.md").write_text(
        "---\nversao: '1.0'\ncontactos: {email: ana@exemplo.invalid}\nferramentas: {Python: CV}\n"
        "experiencias:\n  - {id: a, empregador: Empresa A, setor: energia, titulos: {pt: [Analista]}, inicio: '2022-07', fim: null}\n"
        "conflitos: []\n---\n", encoding="utf-8")
    (dados / "conquistas.md").write_text(
        "---\nfatos:\n  - {id: f1, experiencia: a, status: confirmado, fonte: CV, etiquetas: [], texto: {pt: x}}\n---\n",
        encoding="utf-8")
    (cand / "plano.yaml").write_text(yaml.safe_dump({"fatos": plano_fatos}), encoding="utf-8")
    (cand / "rascunho.md").write_text(
        "---\nvaga_url: u\nidioma: pt-PT\nversao_mestre: '1.0'\n---\nFiz análise de dados. [f:f1]\n", encoding="utf-8")
    return dados, cand


def test_cli_devolve_codigo_de_saida(tmp_path):
    dados, cand = _pasta_cli(tmp_path / "ok", ["f1"])
    assert main([str(dados), str(cand)]) == 0
    dados, cand = _pasta_cli(tmp_path / "fora", [])
    assert main([str(dados), str(cand)]) == 1
