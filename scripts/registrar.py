"""Registo idempotente de candidaturas em log.csv (chave: URL da vaga normalizada).

Uso: python -m scripts.registrar <log.csv> campo=valor ...
"""

from __future__ import annotations

import csv
import os
import sys
import tempfile
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

CAMPOS = ("url", "empresa", "vaga", "data", "angulo", "versao_mestre", "tipo_vaga", "status", "resposta")


def normalizar_url(url: str) -> str:
    partes = urlsplit(url.strip())
    consulta = [(k, v) for k, v in parse_qsl(partes.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    return urlunsplit((partes.scheme.lower(), partes.netloc.lower(), partes.path.rstrip("/"), urlencode(consulta), ""))


def _ler(log: Path) -> list[dict[str, str]]:
    if not log.exists():
        return []
    with log.open(encoding="utf-8-sig", newline="") as f:
        return [{c: (linha.get(c) or "") for c in CAMPOS} for linha in csv.DictReader(f)]


def _escrever(log: Path, linhas: list[dict[str, str]]) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=log.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(linhas)
        os.replace(tmp, log)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def registrar(log: Path, linha: dict[str, str]) -> Literal["criada", "atualizada"]:
    desconhecidos = sorted(set(linha) - set(CAMPOS))
    if desconhecidos:
        raise ValueError(f"campo desconhecido: {', '.join(desconhecidos)}")
    if not linha.get("url", "").strip():
        raise ValueError("campo obrigatório em falta: url")
    chave = normalizar_url(linha["url"])
    linhas = _ler(log)
    for existente in linhas:
        if normalizar_url(existente["url"]) == chave:
            existente.update({k: v for k, v in linha.items() if k != "url"})
            _escrever(log, linhas)
            return "atualizada"
    linhas.append({c: linha.get(c, "") for c in CAMPOS})
    _escrever(log, linhas)
    return "criada"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("uso: python -m scripts.registrar <log.csv> campo=valor ...", file=sys.stderr)
        return 1
    pares = [a.partition("=") for a in argv[1:]]
    if any(not sep for _, sep, _ in pares):
        print("argumentos devem ter a forma campo=valor", file=sys.stderr)
        return 1
    try:
        print(registrar(Path(argv[0]), {k: v for k, _, v in pares}))
    except (ValueError, OSError) as erro:
        print(f"entrada inválida: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
