"""Leitura de YAML não confiável (vagas, rascunhos, planos): como `yaml.safe_load`, mas sem aliases.

Uma "bomba de aliases" (cada nível referencia o anterior várias vezes) cabe em poucos KB e, ao ser
percorrida ou impressa, expande-se para milhões de elementos. Aliases não são necessários nos contratos.
"""

from __future__ import annotations

from typing import Any

import yaml


class _Carregador(yaml.SafeLoader):
    def compose_node(self, parent, index):  # type: ignore[no-untyped-def]
        if self.check_event(yaml.AliasEvent):
            evento = self.peek_event()
            raise yaml.composer.ComposerError(
                None, None, "aliases YAML (*nome) não são permitidos neste formato", evento.start_mark
            )
        return super().compose_node(parent, index)


def carregar(texto: str) -> Any:
    return yaml.load(texto, Loader=_Carregador)  # noqa: S506 - subclasse de SafeLoader, sem aliases
