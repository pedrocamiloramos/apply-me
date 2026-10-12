import shutil
from datetime import date
from pathlib import Path

import yaml

from scripts.conferir_fatos import conferir_rascunho, parsear_rascunho
from scripts.detectar_duplicados import encontrar_duplicados
from scripts.gerar_funil import gerar_funil
from scripts.mestre import Status, carregar_mestre, validar_mestre
from scripts.registrar import registrar
from scripts.resultado import Estado
from scripts.validar_contrato import validar_ficheiro
from scripts.verificar_privacidade import verificar_arvore

RAIZ = Path(__file__).resolve().parent.parent
ANA = RAIZ / "exemplos" / "ana-exemplo"
CAND = ANA / "candidaturas" / "empresa-exemplo-analista"
URL = "https://empresa-exemplo.invalid/vagas/analista-dados"


def test_candidatura_exemplo_percorre_o_fluxo(tmp_path):
    for tipo, nome in (("vaga", "vaga.yaml"), ("gaps", "gaps.yaml"), ("plano", "plano.yaml"),
                       ("rascunho", "rascunho.md"), ("qa", "qa.yaml")):
        r = validar_ficheiro(tipo, CAND / nome)
        assert r.estado is Estado.PASSOU, (nome, r.achados)

    mestre = carregar_mestre(ANA)
    assert validar_mestre(mestre).estado is Estado.PASSOU
    assert len(mestre.experiencias) == 3 and len(mestre.fatos) == 8
    assert {f.status for f in mestre.fatos} == {Status.CONFIRMADO, Status.ESTIMADO, Status.DESCONHECIDO}

    plano = yaml.safe_load((CAND / "plano.yaml").read_text(encoding="utf-8"))
    rascunho = parsear_rascunho((CAND / "rascunho.md").read_text(encoding="utf-8"))
    r = conferir_rascunho(rascunho, mestre, plano, date(2026, 10, 12))
    assert r.estado is Estado.PASSOU, r.achados

    desconhecidos = {f.id for f in mestre.fatos if f.status is Status.DESCONHECIDO}
    assert desconhecidos and not desconhecidos & {i for f in rascunho.frases for i in f.ids}

    copia = tmp_path / "candidaturas"
    shutil.copytree(ANA / "candidaturas", copia)
    assert encontrar_duplicados(copia).estado is Estado.PASSOU

    log = tmp_path / "log.csv"
    shutil.copy(ANA / "log.csv", log)
    assert registrar(log, {"url": "HTTPS://Empresa-Exemplo.invalid/vagas/analista-dados/?utm_source=x", "status": "enviada"}) == "atualizada"
    assert registrar(log, {"url": URL, "status": "enviada"}) == "atualizada"
    assert "dados-energia" in gerar_funil(log, date(2026, 10, 12))

    assert verificar_arvore(RAIZ).estado is Estado.PASSOU
