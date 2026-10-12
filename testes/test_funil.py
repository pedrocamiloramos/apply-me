from datetime import date

from scripts.gerar_funil import CABECALHO, gerar_funil, main
from scripts.registrar import registrar

HOJE = date(2026, 10, 12)


def _log(tmp_path, linhas):
    log = tmp_path / "log.csv"
    for i, l in enumerate(linhas):
        registrar(log, {"url": f"https://e.com/{i}", **l})
    return log


def test_taxa_de_resposta_por_angulo(tmp_path):
    log = _log(tmp_path, [
        {"angulo": "dados", "tipo_vaga": "analista", "status": "resposta"},
        {"angulo": "dados", "tipo_vaga": "analista", "status": "enviada"},
        {"angulo": "dados", "tipo_vaga": "analista", "status": "enviada"},
    ])
    texto = gerar_funil(log, HOJE)
    assert "33%" in texto and "dados" in texto


def test_amostra_pequena_e_sinalizada(tmp_path):
    log = _log(tmp_path, [{"angulo": "ia", "tipo_vaga": "x", "status": "enviada"}])
    assert "amostra pequena" in gerar_funil(log, HOJE)


def test_amostra_grande_nao_e_sinalizada(tmp_path):
    log = _log(tmp_path, [{"angulo": "ia", "tipo_vaga": "x", "status": "enviada"}] * 0
               + [{"angulo": "ia", "tipo_vaga": "x", "status": s} for s in ["enviada"] * 4 + ["entrevista"]])
    assert "amostra pequena" not in gerar_funil(log, HOJE)


def test_rascunhos_nao_contam_como_enviados(tmp_path):
    log = _log(tmp_path, [{"angulo": "a", "tipo_vaga": "t", "status": "rascunho"},
                          {"angulo": "a", "tipo_vaga": "t", "status": ""}])
    texto = gerar_funil(log, HOJE)
    assert "Enviadas: 0" in texto and "Rascunhos: 2" in texto


def test_log_so_com_cabecalho_nao_divide_por_zero(tmp_path):
    log = tmp_path / "log.csv"
    log.write_text("url,empresa,vaga,data,angulo,versao_mestre,tipo_vaga,status,resposta\n", encoding="utf-8")
    assert "Enviadas: 0" in gerar_funil(log, HOJE)


def test_log_inexistente_gera_funil_vazio(tmp_path):
    assert "Enviadas: 0" in gerar_funil(tmp_path / "nada.csv", HOJE)


def test_angulo_vazio_vira_sem_angulo(tmp_path):
    log = _log(tmp_path, [{"status": "enviada"}])
    assert "(sem ângulo)" in gerar_funil(log, HOJE)


def test_cabecalho_de_gerado(tmp_path):
    log = _log(tmp_path, [{"angulo": "a", "status": "enviada"}])
    out = tmp_path / "funil.md"
    assert main([str(log), str(out)]) == 0
    assert out.read_text(encoding="utf-8").startswith(CABECALHO)
    assert CABECALHO == "<!-- gerado: não editar -->"
