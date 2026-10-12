"""Confere se a mensagem de commit segue Conventional Commits (tipo(escopo)?!?: descrição).

Uso (hook commit-msg): python -m scripts.verificar_commit <ficheiro-da-mensagem>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from scripts.resultado import Achado, Estado, Resultado, codigo_saida

TIPOS = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert")
_PADRAO = re.compile(rf"^(?:{'|'.join(TIPOS)})(?:\([\w./-]+\))?!?: \S")


def verificar_commit(mensagem: str) -> Resultado:
    linhas = [l for l in mensagem.splitlines() if l.strip() and not l.startswith("#")]
    titulo = linhas[0] if linhas else ""
    if titulo.startswith(("Merge ", "Revert ")) or _PADRAO.match(titulo):
        return Resultado(Estado.PASSOU, ())
    achado = Achado(
        "COMMIT_FORA_DO_PADRAO",
        f"use 'tipo(escopo): descrição' com tipo em {', '.join(TIPOS)}; recebido: {titulo!r}",
        "linha 1",
    )
    return Resultado(Estado.REPROVOU, (achado,))


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("uso: python -m scripts.verificar_commit <ficheiro-da-mensagem>", file=sys.stderr)
        return 1
    try:
        resultado = verificar_commit(Path(argv[0]).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as erro:
        print(f"entrada inválida: {erro}", file=sys.stderr)
        return 1
    for a in resultado.achados:
        print(f"{a.local}: {a.codigo}: {a.mensagem}", file=sys.stderr)
    return codigo_saida(resultado)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
