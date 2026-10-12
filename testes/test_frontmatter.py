import pytest

from scripts.frontmatter import separar


def test_separa_meta_e_corpo():
    meta, corpo = separar("---\na: 1\nb: [x, y]\n---\nOlá mundo\nsegunda linha\n")
    assert meta == {"a": 1, "b": ["x", "y"]}
    assert corpo == "Olá mundo\nsegunda linha\n"


def test_aceita_bom_e_crlf():
    meta, corpo = separar("﻿---\r\na: análise\r\n---\r\ncorpo\r\n")
    assert meta == {"a": "análise"}
    assert corpo == "corpo\n"


def test_sem_bloco_levanta_erro():
    with pytest.raises(ValueError, match="front matter"):
        separar("só texto, sem bloco")


def test_yaml_malformado_levanta_erro():
    with pytest.raises(ValueError, match="YAML"):
        separar("---\na: [aberto\n---\ncorpo")


def test_bloco_que_nao_e_mapa_levanta_erro():
    with pytest.raises(ValueError, match="mapa"):
        separar("---\n- a\n- b\n---\ncorpo")
