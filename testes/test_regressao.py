"""Regressão: classes de erro cobertas por casos sintéticos, cada uma presa pelo seu código."""

import shutil
from datetime import date
from pathlib import Path

from scripts.conferir_fatos import conferir_rascunho, parsear_rascunho
from scripts.detectar_duplicados import encontrar_duplicados
from scripts.mestre import carregar_mestre
from scripts.resultado import Estado

PASTA = Path(__file__).resolve().parent / "regressao"
HOJE = date(2026, 10, 12)
MESTRE = carregar_mestre(PASTA / "mestre")
PLANO = {"fatos": [f.id for f in MESTRE.fatos]}


def _conferir(texto: str):
    return conferir_rascunho(parsear_rascunho(texto), MESTRE, PLANO, HOJE)


def _carta(nome: str) -> str:
    return (PASTA / nome).read_text(encoding="utf-8")


def _codigos(r) -> set[str]:
    return {a.codigo for a in r.achados}


def test_cartas_identicas_reprovam(tmp_path):
    for pasta, fixture in (("empresa-contrato", "identicas-a.md"), ("empresa-dados", "identicas-b.md")):
        destino = tmp_path / "candidaturas" / pasta
        destino.mkdir(parents=True)
        shutil.copy(PASTA / fixture, destino / "rascunho.md")
    r = encontrar_duplicados(tmp_path / "candidaturas")
    assert r.estado is Estado.REPROVOU
    assert [a.codigo for a in r.achados] == ["CARTAS_QUASE_IGUAIS"]
    assert "empresa-contrato" in r.achados[0].local and "empresa-dados" in r.achados[0].local


def test_fecho_em_ingles_numa_carta_pt_br():
    r = _conferir(_carta("idioma-errado.md"))
    assert r.estado is Estado.REPROVOU and _codigos(r) == {"IDIOMA_ERRADO"}
    assert [a.local for a in r.achados] == ["frase 6"]


def test_corrigir_o_fecho_faz_a_carta_passar():
    corrigida = _carta("idioma-errado.md").replace(">> Kind regards,", ">> Com os melhores cumprimentos,")
    assert _conferir(corrigida).estado is Estado.PASSOU


def test_anos_de_experiencia_divergentes():
    r = _conferir(_carta("anos-divergentes.md"))
    assert r.estado is Estado.REPROVOU and _codigos(r) == {"ANOS_DIVERGENTES"}


def test_ferramentas_sem_fonte_no_cv():
    r = _conferir(_carta("ferramenta-sem-fonte.md"))
    assert r.estado is Estado.REPROVOU and _codigos(r) == {"FERRAMENTA_SEM_FONTE"}
    mensagens = " ".join(a.mensagem for a in r.achados)
    assert all(f in mensagens for f in ("Lean", "BPM", "cloud"))


def test_carta_de_contrato_unica_passa_na_conferencia():
    assert _conferir(_carta("identicas-a.md")).estado is Estado.PASSOU
