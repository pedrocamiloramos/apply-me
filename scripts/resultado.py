"""Resultado comum a todos os scripts de verificação.

Todo script termina em `passou`, `reprovou` ou `bloqueado`; reprovar é um
resultado esperado, não uma exceção.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Estado(str, Enum):
    PASSOU = "passou"
    REPROVOU = "reprovou"
    BLOQUEADO = "bloqueado"


@dataclass(frozen=True)
class Achado:
    codigo: str
    mensagem: str
    local: str


@dataclass(frozen=True)
class Resultado:
    estado: Estado
    achados: tuple[Achado, ...] = ()


_GRAVIDADE = {Estado.PASSOU: 0, Estado.REPROVOU: 1, Estado.BLOQUEADO: 2}


def codigo_saida(r: Resultado) -> int:
    """0 = passou, 1 = reprovou, 2 = bloqueado."""
    return _GRAVIDADE[r.estado]


def combinar(*rs: Resultado) -> Resultado:
    """O pior estado vence (bloqueado > reprovou > passou); achados concatenados."""
    estado = max((r.estado for r in rs), key=_GRAVIDADE.__getitem__, default=Estado.PASSOU)
    achados = tuple(a for r in rs for a in r.achados)
    return Resultado(estado, achados)
