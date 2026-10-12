"""Verificação determinística de um rascunho contra o CV-mestre.

Formato do rascunho.md: front matter (contrato `rascunho`) + uma frase por linha.
Uma frase factual termina em `[f:id1,id2]`; saudação, fecho e contactos começam por `>> `.

Uso: python -m scripts.conferir_fatos <pasta-dados> <pasta-candidatura>
Código de saída: 0 passou, 1 reprovou, 2 bloqueado.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from scripts.frontmatter import separar
from scripts.mestre import Mestre, Status, anos_experiencia, carregar_mestre
from scripts.resultado import Achado, Estado, Resultado, codigo_saida

BLOQUEANTES = {"FATO_DESCONHECIDO", "CONFLITO_ABERTO"}
_FORMULAICA = ">> "
_IDS = re.compile(r"\s*\[f:([^\]]*)\]\s*$")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_TELEFONE = re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d(?!\w)")

_NUMEROS = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "três": 3, "tres": 3, "quatro": 4, "cinco": 5, "seis": 6,
    "sete": 7, "oito": 8, "nove": 9, "dez": 10, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}
_ANOS = re.compile(
    r"(?<!\w)(?:(mais de|more than|over|cerca de|about|approximately|aproximadamente)\s+)?"
    r"(\d{1,2}|" + "|".join(_NUMEROS) + r")\+?\s+(?:anos|years)(?!\w)",
    re.IGNORECASE,
)
_QUALIFICADOR_MINIMO = {"mais de", "more than", "over"}

_PT = frozenset(
    "de da das dos para com uma que na nas nos por como mais ao os são tem sua seu minha meu foi também "
    "pela pelo entre sobre ser este esta em".split()
)
_EN = frozenset(
    "the of and to in for with an that is on at by from this my our you are was will have has be kind "
    "regards dear sincerely best your i".split()
)
_MARCADORES_PT_PT = frozenset("equipa equipas ficheiro ficheiros telemóvel contacto contactos registo".split())
_MARCADORES_PT_BR = frozenset("equipe equipes arquivo arquivos celular você vocês contato contatos".split())


@dataclass(frozen=True)
class Frase:
    numero: int
    texto: str
    ids: tuple[str, ...]
    formulaica: bool


@dataclass(frozen=True)
class Rascunho:
    meta: dict[str, Any]
    frases: tuple[Frase, ...]


@lru_cache(maxsize=None)
def _vocabulario() -> dict[str, list[str]]:
    caminho = Path(__file__).resolve().parent / "vocabulario.yaml"
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def parsear_rascunho(texto: str) -> Rascunho:
    meta, corpo = separar(texto)
    frases: list[Frase] = []
    for linha in (l for l in corpo.splitlines() if l.strip()):
        numero = len(frases) + 1
        if linha.startswith(_FORMULAICA):
            frases.append(Frase(numero, linha[len(_FORMULAICA):].strip(), (), True))
            continue
        m = _IDS.search(linha)
        ids = tuple(i.strip() for i in m.group(1).split(",") if i.strip()) if m else ()
        frases.append(Frase(numero, (linha[: m.start()] if m else linha).strip(), ids, False))
    return Rascunho(meta, tuple(frases))


def _palavras(texto: str) -> list[str]:
    return re.findall(r"[^\W\d_]+", texto.lower())


def detectar_idioma(texto: str) -> str:
    """'en', 'pt-PT', 'pt-BR', 'pt' (português sem marcador de variante) ou 'indeterminado'."""
    palavras = _palavras(texto)
    br = sum(p in _MARCADORES_PT_BR for p in palavras)
    pt_pt = sum(p in _MARCADORES_PT_PT for p in palavras)
    pt = sum(p in _PT for p in palavras) + br + pt_pt
    en = sum(p in _EN for p in palavras)
    if pt == en:
        return "indeterminado"
    if en > pt:
        return "en"
    if br > pt_pt:
        return "pt-BR"
    if pt_pt > br:
        return "pt-PT"
    return "pt"


def _idioma_incompativel(declarado: str, detectado: str) -> bool:
    if detectado == "indeterminado":
        return False
    if ("en" == declarado) != ("en" == detectado):
        return True
    return detectado in {"pt-PT", "pt-BR"} and detectado != declarado


def _numero(token: str) -> int:
    return int(token) if token.isdigit() else _NUMEROS[token.lower()]


def _anos_aceites(m: Mestre, hoje: date) -> set[int]:
    setores = {e.setor for e in m.experiencias if e.setor}
    return {anos_experiencia(m, hoje)} | {anos_experiencia(m, hoje, setor=s) for s in setores}


def _conferir_frase(f: Frase, r: Rascunho, m: Mestre, plano: dict[str, Any], hoje: date, achados: list[Achado]) -> None:
    local = f"frase {f.numero}"
    fatos = {x.id: x for x in m.fatos}
    if not f.formulaica:
        if not f.ids:
            achados.append(Achado("FRASE_SEM_FATO", "frase sem facto: acrescente [f:id] ou remova", local))
        aproximacoes = "|".join(re.escape(a) for a in _vocabulario()["aproximacoes"])
        tem_aproximacao = re.search(rf"(?<!\w)(?:{aproximacoes})(?!\w)", f.texto, re.IGNORECASE) is not None
        for id_ in f.ids:
            fato = fatos.get(id_)
            if fato is None:
                achados.append(Achado("FATO_INEXISTENTE", f"facto inexistente: {id_}", local))
            elif id_ not in plano.get("fatos", []):
                achados.append(Achado("FATO_FORA_DO_PLANO", f"facto fora do plano: {id_}", local))
            elif fato.status is Status.DESCONHECIDO:
                achados.append(Achado("FATO_DESCONHECIDO", f"facto desconhecido não pode entrar no texto: {id_}", local))
            elif fato.status is Status.ESTIMADO and not tem_aproximacao:
                achados.append(Achado("ESTIMADO_SEM_APROXIMACAO", f"facto estimado exige redação aproximada: {id_}", local))
    conhecidas = {k.lower() for k in m.ferramentas}
    for ferramenta in _vocabulario()["ferramentas"]:
        if ferramenta.lower() in conhecidas:
            continue
        if re.search(rf"(?<!\w){re.escape(ferramenta)}(?!\w)", f.texto, re.IGNORECASE):
            achados.append(Achado("FERRAMENTA_SEM_FONTE", f"ferramenta sem fonte no mestre: {ferramenta}", local))
    aceites = _anos_aceites(m, hoje)
    for qualificador, token in _ANOS.findall(f.texto):
        n, q = _numero(token), qualificador.lower()
        if q in _QUALIFICADOR_MINIMO:
            ok = any(n <= a for a in aceites)
        elif q:
            ok = any(abs(n - a) <= 1 for a in aceites)
        else:
            ok = n in aceites
        if not ok:
            achados.append(Achado("ANOS_DIVERGENTES", f"{n} anos não bate com a linha do tempo ({sorted(aceites)})", local))
    _conferir_contactos(f.texto, m, local, achados)
    declarado = r.meta.get("idioma")
    if declarado and _idioma_incompativel(declarado, detectar_idioma(f.texto)):
        achados.append(Achado("IDIOMA_ERRADO", f"frase fora do idioma declarado ({declarado})", local))


def _conferir_contactos(texto: str, m: Mestre, local: str, achados: list[Achado]) -> None:
    email = m.contactos.get("email", "").lower()
    for encontrado in _EMAIL.findall(texto):
        if encontrado.lower() != email:
            achados.append(Achado("CONTACTO_DIVERGENTE", f"e-mail diferente do mestre: {encontrado}", local))
    telefone = re.sub(r"\D", "", m.contactos.get("telefone", ""))[-9:]
    for candidato in _TELEFONE.findall(texto):
        digitos = re.sub(r"\D", "", candidato)
        if 9 <= len(digitos) <= 13 and digitos[-9:] != telefone:
            achados.append(Achado("CONTACTO_DIVERGENTE", f"telefone diferente do mestre: {candidato.strip()}", local))


def _conferir_afirmacoes(r: Rascunho, m: Mestre, achados: list[Achado]) -> None:
    experiencias = {e.id: e for e in m.experiencias}
    abertos = {c.campo for c in m.conflitos if not c.resolvido}
    lingua = "en" if r.meta.get("idioma") == "en" else "pt"
    for i, a in enumerate(r.meta.get("afirmacoes") or []):
        local = f"afirmacoes[{i}]"
        e = experiencias.get(a["experiencia"])
        if e is None:
            achados.append(Achado("AFIRMACAO_DIVERGENTE", f"experiência inexistente: {a['experiencia']}", local))
            continue
        if f"{e.id}.{a['tipo']}" in abertos:
            achados.append(Achado("CONFLITO_ABERTO", f"{e.id}.{a['tipo']} tem conflito por resolver", local))
            continue
        esperado: tuple[str, ...]
        if a["tipo"] == "cargo":
            esperado = e.titulos.get(lingua, ())
        elif a["tipo"] == "inicio":
            esperado = (e.inicio.strftime("%Y-%m"),)
        else:
            esperado = (e.empregador,)
        if a["valor"] not in esperado:
            achados.append(Achado("AFIRMACAO_DIVERGENTE", f"{a['tipo']} '{a['valor']}' não consta do mestre ({', '.join(esperado)})", local))


def conferir_rascunho(r: Rascunho, m: Mestre, plano: dict[str, Any], hoje: date) -> Resultado:
    achados: list[Achado] = []
    for f in r.frases:
        _conferir_frase(f, r, m, plano, hoje, achados)
    _conferir_afirmacoes(r, m, achados)
    if any(a.codigo in BLOQUEANTES for a in achados):
        return Resultado(Estado.BLOQUEADO, tuple(achados))
    return Resultado(Estado.REPROVOU if achados else Estado.PASSOU, tuple(achados))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("uso: python -m scripts.conferir_fatos <pasta-dados> <pasta-candidatura>", file=sys.stderr)
        return 1
    dados, candidatura = Path(argv[0]), Path(argv[1])
    try:
        mestre = carregar_mestre(dados)
        plano = yaml.safe_load((candidatura / "plano.yaml").read_text(encoding="utf-8-sig")) or {}
        rascunho = parsear_rascunho((candidatura / "rascunho.md").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, KeyError, yaml.YAMLError) as erro:
        print(f"entrada inválida: {erro}", file=sys.stderr)
        return 1
    resultado = conferir_rascunho(rascunho, mestre, plano, date.today())
    for a in resultado.achados:
        print(f"{a.local}: {a.codigo}: {a.mensagem}", file=sys.stderr)
    return codigo_saida(resultado)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
