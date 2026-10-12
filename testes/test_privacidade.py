from scripts.resultado import Estado
from scripts.verificar_privacidade import verificar_arvore, verificar_texto


def test_bloqueia_telefone_email_documento():
    assert verificar_texto("ligue +351 911 222 333", "x.md").achados[0].codigo == "TELEFONE"  # privacidade:ignorar
    assert verificar_texto("911 222 333", "x.md").achados[0].codigo == "TELEFONE"  # privacidade:ignorar
    assert verificar_texto("alguem@example.org", "x.md").achados[0].codigo == "EMAIL"  # privacidade:ignorar
    assert verificar_texto("doc 12345678", "x.md").achados[0].codigo == "DOCUMENTO"  # privacidade:ignorar


def test_aceita_marcadores_ficticios():
    ok = "+351 900 000 000 e ana@exemplo.invalid, data 2026-10-12"
    assert verificar_texto(ok, "x.md").estado is Estado.PASSOU


def test_ignora_binarios(tmp_path):
    (tmp_path / "a.png").write_bytes(b"\x89PNG\x00\xff 911222333")  # privacidade:ignorar
    assert verificar_arvore(tmp_path).estado is Estado.PASSOU


def test_marcador_ignorar_so_vale_na_propria_linha():
    texto = "911 222 333 # privacidade:ignorar\n911 222 334"  # privacidade:ignorar
    r = verificar_texto(texto, "x.md")
    assert r.estado is Estado.REPROVOU
    assert [a.local for a in r.achados] == ["x.md:2"]


def test_local_indica_ficheiro_e_linha():
    r = verificar_texto("ok\nalguem@example.org", "carta.md")  # privacidade:ignorar
    assert r.achados[0].local == "carta.md:2"
