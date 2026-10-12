"""Valida o ficheiro de saída de cada etapa contra o seu contrato (JSON Schema em YAML).

Uso: python -m scripts.validar_contrato <tipo> <ficheiro>
Código de saída: 0 passou, 1 reprovou, 2 bloqueado.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.frontmatter import separar
from scripts.resultado import Achado, Estado, Resultado, codigo_saida

TIPOS = ("vaga", "gaps", "plano", "rascunho", "qa")
LIMITE_DE_VOLTAS = 2
_CONTRATOS = Path(__file__).resolve().parent.parent / "contratos"


@lru_cache(maxsize=None)
def _validador(tipo: str) -> Draft202012Validator:
    schema = yaml.safe_load((_CONTRATOS / f"{tipo}.schema.yaml").read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _juntar(caminho: str, campo: str) -> str:
    return f"{caminho}.{campo}" if caminho else campo


def validar_contrato(tipo: str, dados: Any) -> Resultado:
    if tipo not in TIPOS:
        return Resultado(
            Estado.REPROVOU,
            (Achado("TIPO_DESCONHECIDO", f"tipo de contrato desconhecido: {tipo}", tipo),),
        )
    achados: list[Achado] = []
    erros = sorted(_validador(tipo).iter_errors(dados), key=lambda e: str(list(e.absolute_path)))
    for erro in erros:
        caminho = ".".join(str(p) for p in erro.absolute_path)
        if erro.validator == "required":
            for campo in erro.validator_value:
                if campo not in erro.instance:
                    achados.append(Achado("CAMPO_EM_FALTA", f"campo obrigatório ausente: {campo}", _juntar(caminho, campo)))
        elif erro.validator == "additionalProperties":
            permitidos = set(erro.schema.get("properties", {}))
            for extra in sorted(set(erro.instance) - permitidos):
                achados.append(Achado("CAMPO_INESPERADO", f"campo não previsto no contrato: {extra}", _juntar(caminho, extra)))
        else:
            achados.append(Achado("CAMPO_INVALIDO", erro.message, caminho or "(raiz)"))
    if achados:
        return Resultado(Estado.REPROVOU, tuple(achados))
    if tipo == "qa" and dados["estado"] == "correcoes" and dados["voltas"] >= LIMITE_DE_VOLTAS:
        return Resultado(
            Estado.BLOQUEADO,
            (Achado("LIMITE_DE_VOLTAS", "2 voltas com correções: o fluxo pára e pergunta à pessoa responsável", "voltas"),),
        )
    return Resultado(Estado.PASSOU)


def validar_ficheiro(tipo: str, caminho: Path) -> Resultado:
    try:
        texto = caminho.read_text(encoding="utf-8-sig")
        if tipo == "rascunho" and caminho.suffix == ".md":
            dados, _ = separar(texto)
        else:
            dados = yaml.safe_load(texto)
    except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as erro:
        return Resultado(Estado.REPROVOU, (Achado("ENTRADA_INVALIDA", str(erro), str(caminho)),))
    return validar_contrato(tipo, dados)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("uso: python -m scripts.validar_contrato <tipo> <ficheiro>", file=sys.stderr)
        return 1
    resultado = validar_ficheiro(argv[0], Path(argv[1]))
    for a in resultado.achados:
        print(f"{a.local}: {a.codigo}: {a.mensagem}", file=sys.stderr)
    return codigo_saida(resultado)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
