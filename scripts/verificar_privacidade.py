"""Guarda de privacidade: recusa telefone, e-mail e número de documento reais.

Marcadores fictícios aceites: `+351 900 000 000` e `@exemplo.invalid`.
Uma linha com `privacidade:ignorar` é saltada (usado só em testes do próprio guarda).
"""

from __future__ import annotations

import re
import sys
from bisect import bisect_right
from pathlib import Path

from scripts.resultado import Achado, Estado, Resultado, codigo_saida

MARCADOR_IGNORAR = "privacidade:ignorar"
DOMINIO_FICTICIO = "exemplo.invalid"
TELEFONE_FICTICIO = "900000000"
PASTAS_IGNORADAS = {".git", ".superpowers", ".pytest_cache", "__pycache__", ".venv"}
TAMANHO_MAXIMO = 2 * 1024 * 1024  # bytes; ficheiros de texto maiores são recusados, não lidos

# 9 dígitos em grupos de 3 (com separador) ou com prefixo internacional.
_TELEFONE = re.compile(
    r"(?<![\w+])(?:\+\d{1,3}[\s.-]?)?(\d{3})[\s.-]?(\d{3})[\s.-]?(\d{3})(?![\w])"
)
# Brasil e internacional compacto (exemplos nos testes).  # privacidade:ignorar
_TELEFONE_EXTRA = (
    re.compile(r"(?<![\w+])(?:\+55[\s.-]?)?\(?\d{2}\)?[\s.-]?9\d{4}[\s.-]?\d{4}(?!\w)"),
    re.compile(r"(?<![\w+])(?:00|\+)\d{2,3}\d{9}(?!\w)"),
)
# O lookbehind obriga a começar no início do "token": sem ele o motor tentava todas as posições de
# uma sequência longa e o tempo crescia com o quadrado do tamanho da linha.
_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@([\w-]+(?:\.[\w-]+)+)")
_DOCUMENTO = re.compile(r"(?<![\w.+-])\d{8,9}(?![\w.-])")


def _achados_da_linha(linha: str, local: str) -> list[Achado]:
    achados: list[Achado] = []
    for m in _TELEFONE.finditer(linha):
        if "".join(m.groups()) != TELEFONE_FICTICIO:
            achados.append(Achado("TELEFONE", "número de telefone real", local))
    for padrao in _TELEFONE_EXTRA:
        for m in padrao.finditer(linha):
            if not re.sub(r"\D", "", m.group()).endswith(TELEFONE_FICTICIO):
                achados.append(Achado("TELEFONE", "número de telefone real", local))
    for m in _EMAIL.finditer(linha):
        if m.group(1).lower() != DOMINIO_FICTICIO:
            achados.append(Achado("EMAIL", "endereço de e-mail real", local))
    tem_telefone = any(a.codigo == "TELEFONE" for a in achados)
    if tem_telefone:
        return achados
    inicios, fins = [], []
    for m in _TELEFONE.finditer(linha):
        inicios.append(m.start())
        fins.append(m.end())
    for m in _DOCUMENTO.finditer(linha):
        i = bisect_right(inicios, m.start()) - 1  # último telefone que começa até aqui
        if not (i >= 0 and m.end() <= fins[i]):
            achados.append(Achado("DOCUMENTO", "número com formato de documento", local))
    return achados


def verificar_texto(texto: str, caminho: str) -> Resultado:
    achados: list[Achado] = []
    for numero, linha in enumerate(texto.splitlines(), start=1):
        if MARCADOR_IGNORAR in linha:
            continue
        achados.extend(_achados_da_linha(linha, f"{caminho}:{numero}"))
    return Resultado(Estado.REPROVOU if achados else Estado.PASSOU, tuple(achados))


class _FicheiroGrande(Exception):
    """O ficheiro de texto excede TAMANHO_MAXIMO."""


def _ler_texto(caminho: Path) -> str | None:
    """Devolve o texto, ou None para binários e ficheiros ilegíveis. Lê no máximo TAMANHO_MAXIMO + 1 bytes."""
    try:
        with caminho.open("rb") as f:
            dados = f.read(TAMANHO_MAXIMO + 1)
    except OSError:
        return None
    if b"\x00" in dados[:1024]:
        return None
    if len(dados) > TAMANHO_MAXIMO:
        raise _FicheiroGrande
    return dados.decode("utf-8", errors="replace")


def _verificar_ficheiro(caminho: Path, rotulo: str) -> Resultado:
    try:
        texto = _ler_texto(caminho)
    except _FicheiroGrande:
        return Resultado(Estado.REPROVOU, (Achado(
            "FICHEIRO_GRANDE", f"ficheiro de texto acima de {TAMANHO_MAXIMO} bytes não foi verificado", rotulo),))
    if texto is None:
        return Resultado(Estado.PASSOU)
    return verificar_texto(texto, rotulo)


def verificar_arvore(raiz: Path) -> Resultado:
    achados: list[Achado] = []
    for caminho in sorted(raiz.rglob("*")):
        relativo = caminho.relative_to(raiz)
        if any(parte in PASTAS_IGNORADAS for parte in relativo.parts) or not caminho.is_file():
            continue
        achados.extend(_verificar_ficheiro(caminho, relativo.as_posix()).achados)
    return Resultado(Estado.REPROVOU if achados else Estado.PASSOU, tuple(achados))


def main(argv: list[str]) -> int:
    """Cada argumento é um ficheiro ou uma pasta; sem argumentos verifica a pasta atual."""
    alvos = [Path(a) for a in argv] or [Path(".")]
    achados: list[Achado] = []
    for alvo in alvos:
        r = verificar_arvore(alvo) if alvo.is_dir() else _verificar_ficheiro(alvo, str(alvo))
        achados.extend(r.achados)
    resultado = Resultado(Estado.REPROVOU if achados else Estado.PASSOU, tuple(achados))
    for a in resultado.achados:
        print(f"{a.local}: {a.codigo}: {a.mensagem}", file=sys.stderr)
    return codigo_saida(resultado)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
