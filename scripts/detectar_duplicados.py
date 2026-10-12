"""Deteta cartas quase iguais entre candidaturas (Jaccard sobre grupos de 5 palavras).

Uso: python -m scripts.detectar_duplicados <pasta-dados>   (lê <pasta-dados>/candidaturas/*/rascunho.md)
"""

from __future__ import annotations

import re
import sys
from itertools import combinations
from pathlib import Path

from scripts.frontmatter import separar
from scripts.resultado import Achado, Estado, Resultado, codigo_saida

_GRUPO = 5


def _grupos(texto: str) -> set[tuple[str, ...]]:
    palavras = re.findall(r"\w+", texto.lower())
    if len(palavras) <= _GRUPO:
        return {tuple(palavras)} if palavras else set()
    return {tuple(palavras[i : i + _GRUPO]) for i in range(len(palavras) - _GRUPO + 1)}


def similaridade(a: str, b: str) -> float:
    ga, gb = _grupos(a), _grupos(b)
    if not ga and not gb:
        return 1.0
    return len(ga & gb) / len(ga | gb)


def _corpo(caminho: Path) -> str:
    texto = caminho.read_text(encoding="utf-8-sig")
    try:
        return separar(texto)[1]
    except ValueError:
        return texto


def encontrar_duplicados(pasta_candidaturas: Path, limiar: float = 0.8) -> Resultado:
    if not pasta_candidaturas.is_dir():
        return Resultado(Estado.PASSOU, ())
    cartas = {
        p.parent.name: _corpo(p)
        for p in sorted(pasta_candidaturas.glob("*/rascunho.md"))
    }
    achados = [
        Achado("CARTAS_QUASE_IGUAIS", f"similaridade {s:.0%}: reescreva uma das duas", f"{a} / {b}")
        for (a, ta), (b, tb) in combinations(cartas.items(), 2)
        if (s := similaridade(ta, tb)) >= limiar
    ]
    return Resultado(Estado.REPROVOU if achados else Estado.PASSOU, tuple(achados))


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("uso: python -m scripts.detectar_duplicados <pasta-dados>", file=sys.stderr)
        return 1
    try:
        resultado = encontrar_duplicados(Path(argv[0]) / "candidaturas")
    except (OSError, UnicodeDecodeError) as erro:
        print(f"entrada inválida: {erro}", file=sys.stderr)
        return 1
    for a in resultado.achados:
        print(f"{a.local}: {a.codigo}: {a.mensagem}", file=sys.stderr)
    return codigo_saida(resultado)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
