"""Leitura de YAML não confiável (vagas, rascunhos, planos): como `yaml.safe_load`, mas sem aliases.

Uma "bomba de aliases" (cada nível referencia o anterior várias vezes) cabe em poucos KB e, ao ser
percorrida ou impressa, expande-se para milhões de elementos. Aliases não são necessários nos contratos.
Os eventos do analisador são percorridos antes de construir os objetos, por isso a verificação é linear.
"""

from __future__ import annotations

from typing import Any

import yaml


def carregar(texto: str) -> Any:
    for evento in yaml.parse(texto, Loader=yaml.SafeLoader):
        if isinstance(evento, yaml.AliasEvent):
            raise yaml.composer.ComposerError(
                None, None, "aliases YAML (*nome) não são permitidos neste formato", evento.start_mark
            )
    return yaml.safe_load(texto)
