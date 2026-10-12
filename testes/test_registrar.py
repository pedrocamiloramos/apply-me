import csv

import pytest

from scripts.registrar import CAMPOS, main, normalizar_url, registrar


def _linhas(log):
    with log.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_cria_ficheiro_e_linha(tmp_path):
    log = tmp_path / "log.csv"
    assert registrar(log, {"url": "https://empresa.com/vaga", "empresa": "Empresa"}) == "criada"
    linhas = _linhas(log)
    assert len(linhas) == 1 and list(linhas[0]) == list(CAMPOS)
    assert linhas[0]["empresa"] == "Empresa" and linhas[0]["status"] == ""


def test_mesma_url_atualiza_sem_duplicar(tmp_path):
    log = tmp_path / "log.csv"
    registrar(log, {"url": "https://empresa.com/vaga", "empresa": "Empresa", "status": "rascunho"})
    assert registrar(log, {"url": "https://empresa.com/vaga", "status": "enviada"}) == "atualizada"
    linhas = _linhas(log)
    assert len(linhas) == 1
    assert linhas[0]["status"] == "enviada" and linhas[0]["empresa"] == "Empresa"


def test_url_com_barra_maiuscula_e_utm_e_a_mesma(tmp_path):
    log = tmp_path / "log.csv"
    registrar(log, {"url": "HTTPS://Empresa.com/vaga/?utm_source=x#topo"})
    assert registrar(log, {"url": "https://empresa.com/vaga"}) == "atualizada"
    assert len(_linhas(log)) == 1


def test_duas_vagas_distintas_ficam_separadas(tmp_path):
    log = tmp_path / "log.csv"
    registrar(log, {"url": "https://empresa.com/vaga?id=1"})
    registrar(log, {"url": "https://empresa.com/vaga?id=2"})
    assert len(_linhas(log)) == 2


def test_campo_desconhecido_e_rejeitado(tmp_path):
    with pytest.raises(ValueError, match="salario"):
        registrar(tmp_path / "log.csv", {"url": "https://a.com/x", "salario": "1"})
    assert not (tmp_path / "log.csv").exists()


def test_url_em_falta_e_rejeitada(tmp_path):
    with pytest.raises(ValueError, match="url"):
        registrar(tmp_path / "log.csv", {"empresa": "X"})


def test_atualizacao_nao_altera_outras_linhas(tmp_path):
    log = tmp_path / "log.csv"
    registrar(log, {"url": "https://a.com/1", "empresa": "A"})
    registrar(log, {"url": "https://b.com/2", "empresa": "B"})
    registrar(log, {"url": "https://a.com/1", "status": "enviada"})
    linhas = _linhas(log)
    assert [l["empresa"] for l in linhas] == ["A", "B"] and linhas[1]["status"] == ""


def test_normalizar_url():
    assert normalizar_url("HTTPS://Empresa.com/Vaga/?utm_medium=a&id=3#x") == "https://empresa.com/Vaga?id=3"
    assert normalizar_url("  https://empresa.com/  ") == "https://empresa.com"


def test_cli_cria_e_atualiza(tmp_path, capsys):
    log = tmp_path / "log.csv"
    assert main([str(log), "url=https://a.com/1", "empresa=A"]) == 0
    assert "criada" in capsys.readouterr().out
    assert main([str(log), "url=https://a.com/1", "status=enviada"]) == 0
    assert main([str(log), "sem-igual"]) == 1
    assert main([str(log), "url=https://a.com/1", "xx=1"]) == 1
