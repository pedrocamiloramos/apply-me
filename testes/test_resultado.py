from scripts.resultado import Estado, Resultado, codigo_saida, combinar


def test_codigo_saida_e_combinar():
    assert codigo_saida(Resultado(Estado.PASSOU)) == 0
    assert codigo_saida(Resultado(Estado.REPROVOU)) == 1
    assert codigo_saida(Resultado(Estado.BLOQUEADO)) == 2
    assert combinar(Resultado(Estado.REPROVOU), Resultado(Estado.BLOQUEADO)).estado is Estado.BLOQUEADO
