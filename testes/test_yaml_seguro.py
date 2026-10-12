"""YAML vindo de fora (vagas, rascunhos, planos) não pode usar aliases: uma bomba de aliases trava a validação."""

import time

import pytest
import yaml

from scripts.conferir_fatos import main as conferir_main
from scripts.frontmatter import separar
from scripts.resultado import Estado
from scripts.validar_contrato import validar_ficheiro
from scripts.yaml_seguro import carregar


def _bomba(niveis: int = 12) -> str:
    """Cada nível referencia o anterior 9 vezes: expandido, daria 9**niveis elementos."""
    linhas = ["_d0: &a0 [x,x,x,x,x,x,x,x,x]"]
    linhas += [f"_d{i}: &a{i} [{','.join(['*a' + str(i - 1)] * 9)}]" for i in range(1, niveis)]
    return "\n".join(linhas) + "\n"


def test_carregar_aceita_yaml_normal():
    assert carregar("a: 1\nb: [x, y]\n") == {"a": 1, "b": ["x", "y"]}


def test_carregar_recusa_aliases():
    with pytest.raises(yaml.YAMLError, match="alias"):
        carregar("a: &x [1]\nb: *x\n")


def test_vaga_com_bomba_de_aliases_reprova_depressa(tmp_path):
    f = tmp_path / "vaga.yaml"
    f.write_text(_bomba() + "url: u\ntitulo: t\nempresa: e\nidioma: en\nsenioridade: s\nrequisitos: *a11\npalavras_chave: []\n", encoding="utf-8")
    inicio = time.monotonic()
    r = validar_ficheiro("vaga", f)
    assert r.estado is Estado.REPROVOU and r.achados[0].codigo == "ENTRADA_INVALIDA"
    assert time.monotonic() - inicio < 2.0


def test_front_matter_com_aliases_levanta_valueerror():
    with pytest.raises(ValueError, match="alias"):
        separar("---\n" + _bomba(3) + "x: *a2\n---\ncorpo\n")


def test_plano_com_bomba_de_aliases_da_mensagem(tmp_path, capsys):
    dados, cand = tmp_path / "d", tmp_path / "d" / "c"
    cand.mkdir(parents=True)
    (dados / "cv-mestre.md").write_text("---\nversao: '1'\nexperiencias: []\n---\n", encoding="utf-8")
    (dados / "conquistas.md").write_text("---\nfatos: []\n---\n", encoding="utf-8")
    (cand / "plano.yaml").write_text(_bomba() + "frases: *a11\n", encoding="utf-8")
    (cand / "rascunho.md").write_text("---\nvaga_url: u\nidioma: pt-PT\nversao_mestre: '1'\n---\nOlá. [f:x]\n", encoding="utf-8")
    inicio = time.monotonic()
    assert conferir_main([str(dados), str(cand)]) == 1
    assert time.monotonic() - inicio < 2.0
    assert "Traceback" not in capsys.readouterr().err
