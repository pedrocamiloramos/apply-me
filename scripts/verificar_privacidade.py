"""Guarda de privacidade: recusa telefone, e-mail e número de documento reais.

Marcadores fictícios aceites: `+351 900 000 000` e `@exemplo.invalid`.
Uma linha com `privacidade:ignorar` é saltada (usado só em testes do próprio guarda).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from scripts.resultado import Achado, Estado, Resultado, codigo_saida

MARCADOR_IGNORAR = "privacidade:ignorar"
DOMINIO_FICTICIO = "exemplo.invalid"
TELEFONE_FICTICIO = "900000000"
PASTAS_IGNORADAS = {".git", ".superpowers", ".pytest_cache", "__pycache__", ".venv"}

# 9 dígitos em grupos de 3 (com separador) ou com prefixo internacional.
_TELEFONE = re.compile(
    r"(?<![\w+])(?:\+\d{1,3}[\s.-]?)?(\d{3})[\s.-]?(\d{3})[\s.-]?(\d{3})(?![\w])"
)
# Brasil e internacional compacto (exemplos nos testes).  # privacidade:ignorar
_TELEFONE_EXTRA = (
    re.compile(r"(?<![\w+])(?:\+55[\s.-]?)?\(?\d{2}\)?[\s.-]?9\d{4}[\s.-]?\d{4}(?!\w)"),
    re.compile(r"(?<![\w+])(?:00|\+)\d{2,3}\d{9}(?!\w)"),
)
_EMAIL = re.compile(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)")
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
    telefones = [m.span() for m in _TELEFONE.finditer(linha)]
    for m in _DOCUMENTO.finditer(linha):
        dentro_de_telefone = any(s <= m.start() and m.end() <= e for s, e in telefones)
        if not dentro_de_telefone and not any(a.codigo == "TELEFONE" for a in achados):
            achados.append(Achado("DOCUMENTO", "número com formato de documento", local))
    return achados


def verificar_texto(texto: str, caminho: str) -> Resultado:
    achados: list[Achado] = []
    for numero, linha in enumerate(texto.splitlines(), start=1):
        if MARCADOR_IGNORAR in linha:
            continue
        achados.extend(_achados_da_linha(linha, f"{caminho}:{numero}"))
    return Resultado(Estado.REPROVOU if achados else Estado.PASSOU, tuple(achados))


def _ler_texto(caminho: Path) -> str | None:
    """Devolve o texto, ou None para binários e ficheiros ilegíveis."""
    try:
        dados = caminho.read_bytes()
    except OSError:
        return None
    if b"\x00" in dados[:1024]:
        return None
    return dados.decode("utf-8", errors="replace")


def _verificar_ficheiro(caminho: Path, rotulo: str) -> Resultado:
    texto = _ler_texto(caminho)
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
