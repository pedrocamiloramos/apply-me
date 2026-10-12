from datetime import date
from pathlib import Path

import pytest

from scripts.mestre import Status, anos_experiencia, carregar_mestre, main, validar_mestre
from scripts.resultado import Estado

HOJE = date(2026, 10, 12)


def _cv(experiencias: str, conflitos: str = "conflitos: []") -> str:
    return f"""---
versao: "1.0"
contactos:
  email: ana@exemplo.invalid
  telefone: "+351 900 000 000"
idiomas:
  espanhol: B2
ferramentas:
  Python: CV exemplo
experiencias:
{experiencias}
{conflitos}
---
# CV-mestre fictício
"""


def _fatos(*itens: str) -> str:
    return "---\nfatos:\n" + "\n".join(itens) + "\n---\n"


def _fato(id_: str, exp: str = "a", status: str = "confirmado") -> str:
    return f"""  - id: {id_}
    experiencia: {exp}
    status: {status}
    fonte: CV exemplo
    etiquetas: [dados]
    texto:
      pt: "Fiz análise de dados"
      en: "Did data analysis"
"""


def _exp(id_: str, inicio: str, fim: str = "null", setor: str = "energia") -> str:
    return f"""  - id: {id_}
    empregador: Empresa {id_}
    setor: {setor}
    titulos:
      pt: ["Analista"]
      en: ["Analyst"]
    inicio: "{inicio}"
    fim: {fim if fim == "null" else f'"{fim}"'}
"""


def _pasta(tmp_path: Path, cv: str, conquistas: str, eol: str = "\n", bom: bool = False) -> Path:
    prefixo = b"\xef\xbb\xbf" if bom else b""
    tmp_path.mkdir(parents=True, exist_ok=True)
    for nome, texto in (("cv-mestre.md", cv), ("conquistas.md", conquistas)):
        (tmp_path / nome).write_bytes(prefixo + texto.replace("\n", eol).encode("utf-8"))
    return tmp_path


def _basico(tmp_path: Path, **kw) -> Path:
    return _pasta(tmp_path, _cv(_exp("a", "2020-03", "2021-05")), _fatos(_fato("f1")), **kw)


def test_carrega_mestre_com_crlf_e_bom(tmp_path):
    lf = carregar_mestre(_basico(tmp_path / "lf"))
    crlf = carregar_mestre(_basico(tmp_path / "crlf", eol="\r\n", bom=True))
    assert crlf == lf
    assert crlf.fatos[0].texto["pt"] == "Fiz análise de dados"
    assert crlf.fatos[0].status is Status.CONFIRMADO
    assert crlf.experiencias[0].inicio == date(2020, 3, 1)
    assert crlf.experiencias[0].fim == date(2021, 5, 1)


def test_conflito_aberto_bloqueia(tmp_path):
    conflito = 'conflitos:\n  - {campo: a.inicio, valores: ["2020-03", "2020-04"], resolvido: false}'
    pasta = _pasta(tmp_path, _cv(_exp("a", "2020-03"), conflito), _fatos(_fato("f1")))
    r = validar_mestre(carregar_mestre(pasta))
    assert r.estado is Estado.BLOQUEADO
    assert r.achados[0].codigo == "CONFLITO_ABERTO"


def test_conflito_resolvido_passa(tmp_path):
    conflito = 'conflitos:\n  - {campo: a.inicio, valores: ["2020-03", "2020-04"], resolvido: true}'
    pasta = _pasta(tmp_path, _cv(_exp("a", "2020-03"), conflito), _fatos(_fato("f1")))
    assert validar_mestre(carregar_mestre(pasta)).estado is Estado.PASSOU


def test_ids_duplicados_reprovam(tmp_path):
    pasta = _pasta(tmp_path, _cv(_exp("a", "2020-03")), _fatos(_fato("f1"), _fato("f1")))
    r = validar_mestre(carregar_mestre(pasta))
    assert r.estado is Estado.REPROVOU
    assert r.achados[0].codigo == "ID_DUPLICADO"


def test_fato_sem_experiencia_reprova(tmp_path):
    pasta = _pasta(tmp_path, _cv(_exp("a", "2020-03")), _fatos(_fato("f1", exp="inexistente")))
    r = validar_mestre(carregar_mestre(pasta))
    assert r.estado is Estado.REPROVOU
    assert r.achados[0].codigo == "FATO_SEM_EXPERIENCIA"


def test_status_invalido_levanta_erro_com_o_id_do_fato(tmp_path):
    pasta = _pasta(tmp_path, _cv(_exp("a", "2020-03")), _fatos(_fato("f1", status="talvez")))
    with pytest.raises(ValueError, match="f1"):
        carregar_mestre(pasta)


def test_anos_com_emprego_atual_e_intervalo_sem_atividade(tmp_path):
    exps = _exp("a", "2020-03", "2021-05") + _exp("b", "2022-07")
    m = carregar_mestre(_pasta(tmp_path, _cv(exps), _fatos(_fato("f1"))))
    assert anos_experiencia(m, HOJE) == 5  # 14 + 51 meses


def test_anos_nao_contam_sobreposicao_duas_vezes(tmp_path):
    exps = _exp("a", "2020-01", "2022-01") + _exp("b", "2021-01", "2023-01")
    m = carregar_mestre(_pasta(tmp_path, _cv(exps), _fatos(_fato("f1"))))
    assert anos_experiencia(m, HOJE) == 3  # união = 36 meses; somar daria 4


def test_anos_filtrados_por_setor(tmp_path):
    exps = _exp("a", "2020-03", "2021-05", setor="vendas") + _exp("b", "2023-06", setor="energia")
    m = carregar_mestre(_pasta(tmp_path, _cv(exps), _fatos(_fato("f1", exp="b"))))
    assert anos_experiencia(m, HOJE, setor="energia") == 3  # 40 meses
    assert anos_experiencia(m, HOJE) == 4  # 54 meses


def test_cli_devolve_codigo_de_saida(tmp_path):
    assert main([str(_basico(tmp_path / "ok"))]) == 0
    conflito = 'conflitos:\n  - {campo: a.inicio, valores: ["2020-03", "2020-04"], resolvido: false}'
    aberto = _pasta(tmp_path / "aberto", _cv(_exp("a", "2020-03"), conflito), _fatos(_fato("f1")))
    assert main([str(aberto)]) == 2
