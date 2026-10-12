"""Correções da revisão final do branch (cada teste reproduz um achado)."""

import csv
import subprocess
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
import yaml

from scripts.conferir_fatos import conferir_rascunho, main as conferir_main, parsear_rascunho
from scripts.detectar_duplicados import encontrar_duplicados, main as dup_main
from scripts.mestre import Fato, Status, carregar_mestre, main as mestre_main
from scripts.registrar import main as reg_main, normalizar_url, registrar
from scripts.resultado import Estado
from scripts.verificar_privacidade import verificar_texto

from testes.test_conferir_fatos import HOJE, MESTRE, PLANO, _codigos, _conferir

RAIZ = Path(__file__).resolve().parent.parent
LOG_CABECALHO = "url,empresa,vaga,data,angulo,versao_mestre,tipo_vaga,status,resposta"


# 1. registrar nunca apaga histórico
def test_registrar_recusa_log_com_delimitador_diferente(tmp_path):
    log = tmp_path / "log.csv"
    original = "url;empresa;status\r\nhttps://a.pt/v/1;A;enviada\r\n"
    log.write_bytes(original.encode("utf-8"))
    with pytest.raises(ValueError, match="cabeçalho"):
        registrar(log, {"url": "https://a.pt/v/3", "status": "enviada"})
    assert log.read_bytes() == original.encode("utf-8")
    assert reg_main([str(log), "url=https://a.pt/v/3"]) == 1


def test_registrar_preserva_colunas_extra(tmp_path):
    log = tmp_path / "log.csv"
    log.write_text(LOG_CABECALHO + ",notas\nhttps://a.pt/v/1,A,,,,,,enviada,,minha nota\n", encoding="utf-8")
    registrar(log, {"url": "https://a.pt/v/2"})
    with log.open(encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    assert linhas[0]["notas"] == "minha nota" and len(linhas) == 2


# 2. números têm de vir do facto citado
def test_numero_inventado_em_facto_citado_reprova():
    r = _conferir(["Construí 25 dashboards de operação que pouparam 1 milhão de euros. [f:f1]"])
    assert "NUMERO_SEM_FONTE" in _codigos(r)


def test_numero_do_proprio_facto_passa():
    mestre = replace(MESTRE, fatos=tuple(
        replace(f, texto={"pt": "Produzi cerca de 10 modelos", "en": "x"}) if f.id == "est" else f for f in MESTRE.fatos))
    assert _conferir(["Produzi cerca de 10 modelos. [f:est]"], mestre=mestre).estado is Estado.PASSOU
    assert "NUMERO_SEM_FONTE" in _codigos(_conferir(["Produzi mais de 40 modelos. [f:est]"], mestre=mestre))


# 3. anos amarrados ao setor mencionado
def test_anos_no_setor_mencionado():
    # mestre de teste: 5 anos no total, 4 em energia
    assert _conferir(["Tenho 4 anos de experiência em energia. [f:f1]"]).estado is Estado.PASSOU
    assert "ANOS_DIVERGENTES" in _codigos(_conferir(["Tenho 5 anos de experiência em energia. [f:f1]"]))
    assert "ANOS_DIVERGENTES" in _codigos(_conferir(["Tenho 4 anos de experiência no total. [f:f1]"]))


# 7. dados malformados dão mensagem, nunca traceback
def test_conferir_fatos_cli_com_dados_malformados(tmp_path, capsys):
    dados, cand = tmp_path / "d", tmp_path / "d" / "c"
    cand.mkdir(parents=True)
    (dados / "cv-mestre.md").write_text(
        "---\nversao: '1'\nexperiencias:\n  - {id: a, empregador: E, setor: s, titulos: {pt: [X]}, inicio: '2022-07', fim: null}\n---\n", encoding="utf-8")
    (dados / "conquistas.md").write_text("---\nfatos: []\n---\n", encoding="utf-8")
    (cand / "plano.yaml").write_text("- lista\n", encoding="utf-8")
    (cand / "rascunho.md").write_text("---\nvaga_url: u\nidioma: pt-PT\nversao_mestre: '1'\nafirmacoes: oops\n---\nOlá. [f:x]\n", encoding="utf-8")
    assert conferir_main([str(dados), str(cand)]) == 1
    assert "Traceback" not in capsys.readouterr().err


def test_mestre_cli_com_titulos_malformados(tmp_path, capsys):
    (tmp_path / "cv-mestre.md").write_text(
        "---\nversao: '1'\nexperiencias:\n  - {id: a, empregador: E, titulos: Analista, inicio: '2022-07', fim: null}\n---\n", encoding="utf-8")
    (tmp_path / "conquistas.md").write_text("---\nfatos: []\n---\n", encoding="utf-8")
    assert mestre_main([str(tmp_path)]) == 1
    assert "Traceback" not in capsys.readouterr().err


# 8. resolvido tem de ser booleano
def test_resolvido_como_texto_nao_resolve(tmp_path):
    (tmp_path / "cv-mestre.md").write_text(
        "---\nversao: '1'\nexperiencias: []\nconflitos:\n  - {campo: a.inicio, valores: ['2023-05', '2023-06'], resolvido: 'false'}\n---\n", encoding="utf-8")
    (tmp_path / "conquistas.md").write_text("---\nfatos: []\n---\n", encoding="utf-8")
    assert mestre_main([str(tmp_path)]) == 1  # valor inválido, não 'resolvido'


# 9. URLs reais de vagas
@pytest.mark.parametrize("a,b", [
    ("https://pt.linkedin.com/jobs/view/123?refId=x&trackingId=y", "https://pt.linkedin.com/jobs/view/123"),
    ("https://e.com/v?a=1&b=2", "https://e.com/v?b=2&a=1"),
    ("http://www.e.com/v", "https://e.com/v"),
    ("https://e.com:443/v", "https://e.com/v"),
])
def test_urls_equivalentes_normalizam_igual(a, b):
    assert normalizar_url(a) == normalizar_url(b)


# 10. estados validados
def test_status_e_normalizado_e_validado(tmp_path):
    log = tmp_path / "log.csv"
    registrar(log, {"url": "https://a.com/1", "status": " Entrevista "})
    assert list(csv.DictReader(log.open(encoding="utf-8")))[0]["status"] == "entrevista"
    with pytest.raises(ValueError, match="status"):
        registrar(log, {"url": "https://a.com/1", "status": "talvez"})


# 11. duplicados só da candidatura atual
def test_duplicados_antigos_nao_bloqueiam_a_candidatura_nova(tmp_path):
    carta = "Escrevo para me candidatar à vaga de analista de dados porque trabalho com Python e Power BI todos os dias na minha equipa atual."
    nova = "Sou engenheira de formação e procuro uma oportunidade no setor da energia onde possa aplicar modelos estatísticos a problemas reais."
    cands = tmp_path / "candidaturas"
    for nome, corpo in (("velha-1", carta), ("velha-2", carta), ("nova", nova)):
        (cands / nome).mkdir(parents=True)
        (cands / nome / "rascunho.md").write_text(f"---\nvaga_url: u\nidioma: pt-PT\nversao_mestre: '1'\n---\n{corpo}\n", encoding="utf-8")
    assert dup_main([str(tmp_path)]) == 1
    assert dup_main([str(tmp_path), "nova"]) == 0
    assert dup_main([str(tmp_path), "velha-1"]) == 1


# 13. guarda de privacidade
@pytest.mark.parametrize("linha", [  # privacidade:ignorar
    "Tel (11) 98765-4321",  # privacidade:ignorar
    "+55 11 98765-4321",  # privacidade:ignorar
    "Tel 00351912345678",  # privacidade:ignorar
])
def test_telefones_brasileiros_e_compactos(linha):
    assert verificar_texto(linha, "x").estado is Estado.REPROVOU


def test_hook_pre_commit_inclui_renomeados():
    assert "ACMR" in (RAIZ / "scripts" / "hooks" / "pre-commit").read_text(encoding="utf-8")


# --- Auditoria de segurança (v0.1) ---
import time  # noqa: E402

from scripts import conferir_fatos as _cf  # noqa: E402
from scripts import verificar_privacidade as _vp  # noqa: E402


@pytest.mark.parametrize("linha", ["1" * 30_000, "a." * 15_000, "9-" * 15_000, "a" * 30_000 + "@"],
                         ids=["digitos", "pontos", "hifens", "arroba-final"])
def test_linhas_enormes_nao_travam_o_guarda_nem_o_verificador(linha):
    inicio = time.monotonic()
    _vp.verificar_texto(linha, "x")
    list(_cf._EMAIL.finditer(linha))
    assert time.monotonic() - inicio < 2.0  # era quadrático (cerca de 40 s)


def test_muitos_numeros_na_mesma_linha_nao_travam_o_guarda():
    inicio = time.monotonic()
    r = _vp.verificar_texto(" ".join(["900000000"] * 40_000), "x")  # todos fictícios
    assert r.estado is Estado.PASSOU
    assert time.monotonic() - inicio < 2.0


def test_email_continua_a_ser_detetado_no_meio_de_texto():
    assert _vp.verificar_texto("contacto: alguem@example.org.", "x").estado is Estado.REPROVOU  # privacidade:ignorar
    assert _cf._EMAIL.findall("escreva para a.b+c@x.pt, depois") == ["a.b+c@x.pt"]  # privacidade:ignorar


def test_inicio_nulo_no_mestre_da_mensagem_e_nao_traceback(tmp_path, capsys):
    (tmp_path / "cv-mestre.md").write_text(
        "---\nversao: '1'\nexperiencias:\n  - {id: a, empregador: E, titulos: {pt: [X]}, inicio: null, fim: null}\n---\n", encoding="utf-8")
    (tmp_path / "conquistas.md").write_text("---\nfatos: []\n---\n", encoding="utf-8")
    assert mestre_main([str(tmp_path)]) == 1
    err = capsys.readouterr().err
    assert "Traceback" not in err and "inicio" in err


def test_ficheiro_de_texto_enorme_e_recusado_sem_ler_tudo(tmp_path, monkeypatch):
    monkeypatch.setattr(_vp, "TAMANHO_MAXIMO", 1000)
    (tmp_path / "grande.txt").write_text("a\n" * 2000, encoding="utf-8")
    r = _vp.verificar_arvore(tmp_path)
    assert r.estado is Estado.REPROVOU and r.achados[0].codigo == "FICHEIRO_GRANDE"


def test_binario_grande_continua_a_ser_ignorado(tmp_path, monkeypatch):
    monkeypatch.setattr(_vp, "TAMANHO_MAXIMO", 1000)
    (tmp_path / "x.bin").write_bytes(b"\x00" * 5000)
    assert _vp.verificar_arvore(tmp_path).estado is Estado.PASSOU


# --- Higiene do repositório público ---
def _rastreados() -> list[str]:
    saida = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout
    return saida.splitlines()


def test_repositorio_publico_nao_rastreia_dados_privados():
    proibidos = [f for f in _rastreados() if f.startswith("carreira-dados/") or f.endswith((".pdf", ".docx", ".pem", ".key", ".env"))
                 or Path(f).name in {".env", "id_rsa", "credentials.json"}]
    assert proibidos == []


def test_gitignore_protege_dados_e_segredos():
    texto = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    for padrao in ("carreira-dados/", "*.pdf", "*.docx", ".env", "*.pem", "/log.csv", "/funil.md", "/candidaturas/"):
        assert padrao in texto, padrao


# --- CSV: valores vindos de vagas não podem virar fórmulas no Excel/Sheets ---
@pytest.mark.parametrize("perigoso", ['=HYPERLINK("http://x.invalid","a")', "+cmd|' /C calc'!A0", "-2+3", "@SUM(1+1)", "\t=1+1", "\r=1+1"])
def test_registrar_neutraliza_formulas_em_celulas(tmp_path, perigoso):
    log = tmp_path / "log.csv"
    registrar(log, {"url": "https://a.example/v/1", "empresa": perigoso, "resposta": perigoso})
    with log.open(encoding="utf-8", newline="") as f:
        linha = next(csv.DictReader(f))
    assert linha["empresa"] == "'" + perigoso and linha["resposta"] == "'" + perigoso
    registrar(log, {"url": "https://a.example/v/1", "empresa": linha["empresa"]})  # idempotente: não duplica a aspa
    with log.open(encoding="utf-8", newline="") as f:
        assert next(csv.DictReader(f))["empresa"] == "'" + perigoso


def test_registrar_nao_altera_valores_normais(tmp_path):
    log = tmp_path / "log.csv"
    registrar(log, {"url": "https://a.example/v/1", "empresa": "Empresa Exemplo", "data": "2026-10-12", "status": "enviada"})
    with log.open(encoding="utf-8", newline="") as f:
        linha = next(csv.DictReader(f))
    assert (linha["empresa"], linha["data"], linha["url"]) == ("Empresa Exemplo", "2026-10-12", "https://a.example/v/1")
