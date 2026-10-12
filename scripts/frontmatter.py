"""Leitura do bloco YAML (front matter) de ficheiros markdown."""

from __future__ import annotations

import re
from typing import Any

import yaml

from scripts.yaml_seguro import carregar

_BLOCO = re.compile(r"\A---\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)


def separar(texto: str) -> tuple[dict[str, Any], str]:
    """Devolve (metadados, corpo). Aceita BOM e CRLF; levanta ValueError se o bloco faltar ou for inválido."""
    texto = texto.lstrip("﻿").replace("\r\n", "\n")
    m = _BLOCO.match(texto)
    if not m:
        raise ValueError("front matter (bloco entre '---') não encontrado")
    try:
        dados = carregar(m.group(1))
    except yaml.YAMLError as erro:
        raise ValueError(f"YAML inválido: {erro}") from erro
    if dados is None:
        dados = {}
    if not isinstance(dados, dict):
        raise ValueError("o front matter deve ser um mapa")
    return dados, texto[m.end():]
