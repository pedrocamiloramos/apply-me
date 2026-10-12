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


STATUS = ("rascunho", "enviada", "resposta", "entrevista", "oferta", "rejeitada")
_RASTREIO = {"trk", "refid", "trackingid", "gclid", "fbclid", "tracking", "ref", "src"}


def normalizar_url(url: str) -> str:
    """Chave estável de uma vaga: https, host sem www/porta padrão, sem rastreio, parâmetros ordenados, sem fragmento."""
    partes = urlsplit(url.strip())
    host = (partes.hostname or "").lower().removeprefix("www.")
    if partes.port and partes.port not in (80, 443):
        host = f"{host}:{partes.port}"
    consulta = sorted(
        (k, v) for k, v in parse_qsl(partes.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in _RASTREIO
    )
    esquema = "https" if partes.scheme.lower() in ("http", "https") else partes.scheme.lower()
    return urlunsplit((esquema, host, partes.path.rstrip("/"), urlencode(consulta), ""))


def _ler_completo(log: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Devolve (colunas, linhas) com todas as colunas; recusa ficheiros que não são o log esperado."""
    if not log.exists() or log.stat().st_size == 0:
        return list(CAMPOS), []
    with log.open(encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        colunas = list(leitor.fieldnames or [])
        em_falta = [c for c in CAMPOS if c not in colunas]
        if em_falta:
            raise ValueError(
                f"cabeçalho de {log.name} inválido (falta {', '.join(em_falta)}; delimitador deve ser vírgula): nada foi alterado"
            )
        return colunas, [{c: (l.get(c) or "") for c in colunas} for l in leitor]


def _ler(log: Path) -> list[dict[str, str]]:
    _, linhas = _ler_completo(log)
    return [{c: l[c] for c in CAMPOS} for l in linhas]


def _escrever(log: Path, linhas: list[dict[str, str]], colunas: list[str]) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=log.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=colunas)
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
    if "status" in linha:
        linha = {**linha, "status": linha["status"].strip().lower()}
        if linha["status"] and linha["status"] not in STATUS:
            raise ValueError(f"status inválido '{linha['status']}'; use um de: {', '.join(STATUS)}")
    chave = normalizar_url(linha["url"])
    colunas, linhas = _ler_completo(log)
    for existente in linhas:
        if normalizar_url(existente["url"]) == chave:
            existente.update({k: v for k, v in linha.items() if k != "url"})
            _escrever(log, linhas, colunas)
            return "atualizada"
    linhas.append({c: linha.get(c, "") for c in colunas})
    _escrever(log, linhas, colunas)
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
