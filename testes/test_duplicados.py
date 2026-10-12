from scripts.detectar_duplicados import encontrar_duplicados, main, similaridade
from scripts.resultado import Estado

CARTA = "Escrevo para me candidatar à vaga de analista de dados porque trabalho com Python e Power BI todos os dias na minha equipa atual."
OUTRA = "Sou engenheira de formação e procuro uma oportunidade no setor da energia onde possa aplicar modelos estatísticos a problemas reais de operação."


def _cand(raiz, nome, corpo):
    pasta = raiz / nome
    pasta.mkdir(parents=True)
    (pasta / "rascunho.md").write_text(f"---\nvaga_url: u{nome}\nidioma: pt-PT\nversao_mestre: '1.0'\n---\n{corpo}\n", encoding="utf-8")


def test_textos_identicos_tem_similaridade_1():
    assert similaridade(CARTA, CARTA) == 1.0


def test_textos_diferentes_abaixo_do_limiar():
    assert similaridade(CARTA, OUTRA) < 0.8


def test_pasta_com_duas_cartas_identicas_reprova(tmp_path):
    _cand(tmp_path, "empresa-dados", CARTA)
    _cand(tmp_path, "empresa-ia", CARTA)
    r = encontrar_duplicados(tmp_path)
    assert r.estado is Estado.REPROVOU
    assert r.achados[0].codigo == "CARTAS_QUASE_IGUAIS"
    assert "empresa-dados" in r.achados[0].local and "empresa-ia" in r.achados[0].local


def test_pasta_com_cartas_distintas_passa(tmp_path):
    _cand(tmp_path, "a", CARTA)
    _cand(tmp_path, "b", OUTRA)
    assert encontrar_duplicados(tmp_path).estado is Estado.PASSOU


def test_front_matter_e_ignorado(tmp_path):
    _cand(tmp_path, "a", CARTA)
    _cand(tmp_path, "b", OUTRA)
    (tmp_path / "b" / "rascunho.md").write_text(f"---\nvaga_url: x\nidioma: pt-PT\nversao_mestre: '1.0'\n---\n{CARTA}\n", encoding="utf-8")
    assert encontrar_duplicados(tmp_path).estado is Estado.REPROVOU


def test_pasta_inexistente_ou_vazia_passa(tmp_path):
    assert encontrar_duplicados(tmp_path / "nada").estado is Estado.PASSOU
    assert encontrar_duplicados(tmp_path).estado is Estado.PASSOU


def test_cli_le_candidaturas_da_pasta_de_dados(tmp_path):
    _cand(tmp_path / "candidaturas", "a", CARTA)
    _cand(tmp_path / "candidaturas", "b", CARTA)
    assert main([str(tmp_path)]) == 1
