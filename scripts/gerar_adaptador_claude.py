"""Gera os stubs de skill do Claude a partir de skills/*/SKILL.md (fonte única da verdade).

Uso: python -m scripts.gerar_adaptador_claude [raiz]
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from scripts.frontmatter import separar


def gerar(raiz: Path) -> dict[Path, str]:
    saida: dict[Path, str] = {}
    for origem in sorted((raiz / "skills").glob("*/SKILL.md")):
        nome = origem.parent.name
        meta, _ = separar(origem.read_text(encoding="utf-8"))
        cabecalho = yaml.safe_dump(
            {"name": meta["name"], "description": meta["description"]},
            allow_unicode=True, sort_keys=False, width=10_000,
        )
        saida[Path("adaptadores/claude") / nome / "SKILL.md"] = (
            f"---\n{cabecalho}---\n\n"
            "<!-- gerado por scripts/gerar_adaptador_claude.py: não editar -->\n\n"
            f"Siga as instruções de `skills/{nome}/SKILL.md` e as regras de `AGENTS.md`.\n"
            "Os dados pessoais ficam em `carreira-dados/`, nunca neste repositório.\n"
        )
    return saida


def main(argv: list[str]) -> int:
    raiz = Path(argv[0]) if argv else Path(__file__).resolve().parent.parent
    try:
        for caminho, conteudo in gerar(raiz).items():
            destino = raiz / caminho
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(conteudo, encoding="utf-8")
    except (OSError, ValueError, KeyError) as erro:
        print(f"entrada inválida: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
