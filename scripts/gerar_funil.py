"""Gera funil.md (totais e taxa de resposta por ângulo e por tipo de vaga) a partir de log.csv.

Uso: python -m scripts.gerar_funil <log.csv> <funil.md>
"""

from __future__ import annotations

import sys
from collections import Counter
from datetime import date
from pathlib import Path

from scripts.registrar import _ler

CABECALHO = "<!-- gerado: não editar -->"
RESPOSTAS = {"resposta", "entrevista", "oferta"}
NAO_ENVIADAS = {"", "rascunho"}
AMOSTRA_MINIMA = 5


def _status(l: dict[str, str]) -> str:
    return l["status"].strip().lower()


def _teve_resposta(l: dict[str, str]) -> bool:
    """Resposta = status de resposta/entrevista/oferta, ou a coluna `resposta` preenchida (sobrevive a mudanças de status)."""
    return _status(l) in RESPOSTAS or bool(l["resposta"].strip())


def _tabela(titulo: str, linhas: list[dict[str, str]], campo: str) -> list[str]:
    enviadas: Counter[str] = Counter()
    respostas: Counter[str] = Counter()
    for l in linhas:
        if _status(l) in NAO_ENVIADAS:
            continue
        grupo = l[campo] or f"(sem {titulo.lower()})"
        enviadas[grupo] += 1
        respostas[grupo] += _teve_resposta(l)
    saida = [f"## Por {titulo.lower()}", "", f"| {titulo} | Enviadas | Respostas | Taxa | Nota |", "|---|---|---|---|---|"]
    for grupo in sorted(enviadas):
        taxa = f"{round(100 * respostas[grupo] / enviadas[grupo])}%"
        nota = "amostra pequena" if enviadas[grupo] < AMOSTRA_MINIMA else ""
        saida.append(f"| {grupo} | {enviadas[grupo]} | {respostas[grupo]} | {taxa} | {nota} |")
    if not enviadas:
        saida.append("| — | 0 | 0 | — | |")
    return saida + [""]


def gerar_funil(log: Path, hoje: date) -> str:
    linhas = _ler(log)
    enviadas = [l for l in linhas if _status(l) not in NAO_ENVIADAS]
    com_resposta = sum(_teve_resposta(l) for l in enviadas)
    partes = [
        CABECALHO,
        f"# Funil de candidaturas ({hoje.isoformat()})",
        "",
        f"- Rascunhos: {len(linhas) - len(enviadas)}",
        f"- Enviadas: {len(enviadas)}",
        f"- Com resposta: {com_resposta}",
        "",
    ]
    partes += _tabela("Ângulo", linhas, "angulo")
    partes += _tabela("Tipo de vaga", linhas, "tipo_vaga")
    return "\n".join(partes)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("uso: python -m scripts.gerar_funil <log.csv> <funil.md>", file=sys.stderr)
        return 1
    try:
        texto = gerar_funil(Path(argv[0]), date.today())
        Path(argv[1]).write_text(texto, encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError) as erro:
        print(f"entrada inválida: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
