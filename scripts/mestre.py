"""Domínio puro: CV-mestre (linha do tempo) e banco de factos.

Dois ficheiros markdown, cada um com um bloco YAML entre `---`:
`cv-mestre.md` (versao, contactos, idiomas, ferramentas, experiencias, conflitos)
e `conquistas.md` (fatos). Datas no formato `AAAA-MM`.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

from scripts.frontmatter import separar
from scripts.resultado import Achado, Estado, Resultado, codigo_saida


class Status(str, Enum):
    CONFIRMADO = "confirmado"
    ESTIMADO = "estimado"
    DESCONHECIDO = "desconhecido"


@dataclass(frozen=True)
class Experiencia:
    id: str
    empregador: str
    setor: str
    titulos: dict[str, tuple[str, ...]]
    inicio: date
    fim: date | None


@dataclass(frozen=True)
class Fato:
    id: str
    experiencia: str
    status: Status
    fonte: str
    etiquetas: tuple[str, ...]
    texto: dict[str, str]


@dataclass(frozen=True)
class Conflito:
    campo: str
    valores: tuple[str, ...]
    resolvido: bool


@dataclass(frozen=True)
class Mestre:
    versao: str
    contactos: dict[str, str]
    idiomas: dict[str, str]
    ferramentas: dict[str, str]
    experiencias: tuple[Experiencia, ...]
    fatos: tuple[Fato, ...]
    conflitos: tuple[Conflito, ...]


_MES = re.compile(r"\A(\d{4})-(\d{2})\Z")


def _front_matter(caminho: Path) -> dict[str, Any]:
    try:
        meta, _ = separar(caminho.read_text(encoding="utf-8-sig"))
    except ValueError as erro:
        raise ValueError(f"{caminho.name}: {erro}") from erro
    return meta


def _data(valor: Any, onde: str) -> date | None:
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor
    m = _MES.match(str(valor))
    if m:
        return date(int(m.group(1)), int(m.group(2)), 1)
    raise ValueError(f"{onde}: data '{valor}' fora do formato AAAA-MM")


def _experiencia(d: dict[str, Any]) -> Experiencia:
    onde = f"experiencia {d['id']}"
    inicio = _data(d["inicio"], onde)
    assert inicio is not None
    return Experiencia(
        id=d["id"],
        empregador=d["empregador"],
        setor=d.get("setor", ""),
        titulos={lingua: tuple(v) for lingua, v in (d.get("titulos") or {}).items()},
        inicio=inicio,
        fim=_data(d.get("fim"), onde),
    )


def _fato(d: dict[str, Any]) -> Fato:
    try:
        status = Status(d["status"])
    except ValueError:
        raise ValueError(f"facto {d['id']}: status inválido '{d['status']}'") from None
    return Fato(
        id=d["id"],
        experiencia=d["experiencia"],
        status=status,
        fonte=d.get("fonte", ""),
        etiquetas=tuple(d.get("etiquetas") or ()),
        texto=dict(d.get("texto") or {}),
    )


def carregar_mestre(pasta: Path) -> Mestre:
    cv = _front_matter(pasta / "cv-mestre.md")
    conquistas = _front_matter(pasta / "conquistas.md")
    return Mestre(
        versao=str(cv.get("versao", "")),
        contactos={k: str(v) for k, v in (cv.get("contactos") or {}).items()},
        idiomas={k: str(v) for k, v in (cv.get("idiomas") or {}).items()},
        ferramentas={k: str(v) for k, v in (cv.get("ferramentas") or {}).items()},
        experiencias=tuple(_experiencia(e) for e in cv.get("experiencias") or ()),
        fatos=tuple(_fato(f) for f in conquistas.get("fatos") or ()),
        conflitos=tuple(
            Conflito(c["campo"], tuple(str(v) for v in c["valores"]), bool(c.get("resolvido", False)))
            for c in cv.get("conflitos") or ()
        ),
    )


def validar_mestre(m: Mestre) -> Resultado:
    achados: list[Achado] = []
    vistos: set[str] = set()
    for f in m.fatos:
        if f.id in vistos:
            achados.append(Achado("ID_DUPLICADO", f"id de facto repetido: {f.id}", f"conquistas.md:{f.id}"))
        vistos.add(f.id)
    ids_experiencia = {e.id for e in m.experiencias}
    for f in m.fatos:
        if f.experiencia not in ids_experiencia:
            achados.append(
                Achado("FATO_SEM_EXPERIENCIA", f"experiência inexistente: {f.experiencia}", f"conquistas.md:{f.id}")
            )
    bloqueios = [
        Achado("CONFLITO_ABERTO", f"decida entre {' e '.join(c.valores)}", f"cv-mestre.md:{c.campo}")
        for c in m.conflitos
        if not c.resolvido
    ]
    if bloqueios:
        return Resultado(Estado.BLOQUEADO, tuple(bloqueios + achados))
    return Resultado(Estado.REPROVOU if achados else Estado.PASSOU, tuple(achados))


def _indice_mes(d: date) -> int:
    return d.year * 12 + d.month - 1


def anos_experiencia(m: Mestre, hoje: date, setor: str | None = None) -> int:
    """Anos completos sobre a união dos intervalos (sem contar sobreposição duas vezes)."""
    intervalos = sorted(
        (_indice_mes(e.inicio), _indice_mes(e.fim or hoje))
        for e in m.experiencias
        if setor is None or e.setor == setor
    )
    meses = 0
    atual: list[int] | None = None
    for inicio, fim in intervalos:
        if atual is None or inicio > atual[1]:
            if atual is not None:
                meses += atual[1] - atual[0]
            atual = [inicio, fim]
        else:
            atual[1] = max(atual[1], fim)
    if atual is not None:
        meses += atual[1] - atual[0]
    return meses // 12


def main(argv: list[str]) -> int:
    pasta = Path(argv[0]) if argv else Path(".")
    try:
        resultado = validar_mestre(carregar_mestre(pasta))
    except (OSError, ValueError, KeyError) as erro:
        print(f"entrada inválida: {erro}", file=sys.stderr)
        return 1
    for a in resultado.achados:
        print(f"{a.local}: {a.codigo}: {a.mensagem}", file=sys.stderr)
    return codigo_saida(resultado)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
