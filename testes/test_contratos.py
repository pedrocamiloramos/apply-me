from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.resultado import Estado
from scripts.validar_contrato import main, validar_contrato, validar_ficheiro

TIPOS = ("vaga", "gaps", "plano", "rascunho", "qa")
RAIZ = Path(__file__).resolve().parent.parent

VAGA = {
    "url": "https://empresa.exemplo/vaga/1",
    "titulo": "Analista de Dados",
    "empresa": "Empresa Exemplo",
    "idioma": "pt-PT",
    "senioridade": "pleno",
    "requisitos": ["SQL", "Power BI"],
    "palavras_chave": ["dados", "energia"],
}
QA_OK = {"vaga_url": VAGA["url"], "estado": "aprovado", "correcoes": [], "voltas": 0}


def test_cinco_schemas_existem_e_sao_validos():
    for tipo in TIPOS:
        schema = yaml.safe_load((RAIZ / "contratos" / f"{tipo}.schema.yaml").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_vaga_valida_passa():
    assert validar_contrato("vaga", VAGA).estado is Estado.PASSOU


def test_campo_em_falta_reprova_e_nomeia_o_campo():
    dados = {k: v for k, v in VAGA.items() if k != "empresa"}
    r = validar_contrato("vaga", dados)
    assert r.estado is Estado.REPROVOU
    assert any(a.local == "empresa" for a in r.achados)


def test_idioma_fora_da_lista_reprova():
    r = validar_contrato("vaga", {**VAGA, "idioma": "fr"})
    assert r.estado is Estado.REPROVOU
    assert any(a.local == "idioma" for a in r.achados)


def test_campo_inesperado_reprova():
    r = validar_contrato("vaga", {**VAGA, "salario": "x"})
    assert r.estado is Estado.REPROVOU
    assert any(a.local == "salario" for a in r.achados)


def test_plano_com_decisao_invalida_reprova():
    plano = {
        "vaga_url": VAGA["url"], "decisao": "talvez", "angulo": "dados", "fatos": ["f1"],
        "titulo_variante": "Analista", "idioma": "pt-PT", "versao_mestre": "1.0",
    }
    r = validar_contrato("plano", plano)
    assert r.estado is Estado.REPROVOU and any(a.local == "decisao" for a in r.achados)


def test_gaps_valido_passa():
    gaps = {"vaga_url": VAGA["url"], "fatos_relevantes": ["f1"], "lacunas": [], "bloqueios": []}
    assert validar_contrato("gaps", gaps).estado is Estado.PASSOU


def test_qa_aprovado_passa():
    assert validar_contrato("qa", QA_OK).estado is Estado.PASSOU


def test_qa_com_correcoes_e_duas_voltas_bloqueia():
    qa = {**QA_OK, "estado": "correcoes", "voltas": 2, "correcoes": [{"local": "frase 4", "mensagem": "sem fato"}]}
    r = validar_contrato("qa", qa)
    assert r.estado is Estado.BLOQUEADO
    assert r.achados[0].codigo == "LIMITE_DE_VOLTAS"


def test_qa_com_correcoes_e_uma_volta_e_contrato_valido():
    qa = {**QA_OK, "estado": "correcoes", "voltas": 1, "correcoes": [{"local": "frase 4", "mensagem": "sem fato"}]}
    assert validar_contrato("qa", qa).estado is Estado.PASSOU  # contrato válido; o fluxo decide


def test_qa_com_mais_de_duas_voltas_reprova():
    assert validar_contrato("qa", {**QA_OK, "voltas": 3}).estado is Estado.REPROVOU


def test_afirmacao_com_tipo_desconhecido_reprova():
    meta = {"vaga_url": VAGA["url"], "idioma": "en", "versao_mestre": "1.0",
            "afirmacoes": [{"tipo": "salario", "experiencia": "a", "valor": "x"}]}
    assert validar_contrato("rascunho", meta).estado is Estado.REPROVOU


def test_tipo_desconhecido_reprova():
    r = validar_contrato("curriculo", VAGA)
    assert r.estado is Estado.REPROVOU and r.achados[0].codigo == "TIPO_DESCONHECIDO"


def test_rascunho_md_le_o_front_matter(tmp_path):
    f = tmp_path / "rascunho.md"
    f.write_text("---\nvaga_url: u\nidioma: en\nversao_mestre: '1.0'\n---\nDear team. [f:f1]\n", encoding="utf-8")
    assert validar_ficheiro("rascunho", f).estado is Estado.PASSOU


def test_yaml_malformado_reprova_com_entrada_invalida(tmp_path):
    f = tmp_path / "vaga.yaml"
    f.write_text("url: [aberto\n", encoding="utf-8")
    r = validar_ficheiro("vaga", f)
    assert r.estado is Estado.REPROVOU and r.achados[0].codigo == "ENTRADA_INVALIDA"


def test_ficheiro_inexistente_reprova_com_entrada_invalida(tmp_path):
    r = validar_ficheiro("vaga", tmp_path / "nao-existe.yaml")
    assert r.estado is Estado.REPROVOU and r.achados[0].codigo == "ENTRADA_INVALIDA"


@pytest.mark.parametrize("dados,esperado", [
    (QA_OK, 0),
    ({"vaga_url": "u"}, 1),
    ({**QA_OK, "estado": "correcoes", "voltas": 2, "correcoes": [{"local": "l", "mensagem": "m"}]}, 2),
])
def test_exit_code_da_cli(tmp_path, dados, esperado):
    f = tmp_path / "qa.yaml"
    f.write_text(yaml.safe_dump(dados), encoding="utf-8")
    assert main(["qa", str(f)]) == esperado
