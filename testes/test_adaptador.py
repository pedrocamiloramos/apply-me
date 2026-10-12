from pathlib import Path

from scripts.frontmatter import separar
from scripts.gerar_adaptador_claude import gerar, main

RAIZ = Path(__file__).resolve().parent.parent
SKILLS = ("ler-vaga", "comparar", "planejar", "redigir", "qa", "registrar", "funil")


def test_gera_um_stub_por_skill():
    stubs = gerar(RAIZ)
    assert set(stubs) == {Path("adaptadores/claude") / s / "SKILL.md" for s in SKILLS}


def test_stub_aponta_para_a_skill_e_agents_md():
    for caminho, conteudo in gerar(RAIZ).items():
        nome = caminho.parent.name
        meta, corpo = separar(conteudo)
        original, _ = separar((RAIZ / "skills" / nome / "SKILL.md").read_text(encoding="utf-8"))
        assert meta == {"name": original["name"], "description": original["description"]}
        assert f"skills/{nome}/SKILL.md" in corpo and "AGENTS.md" in corpo


def test_ficheiros_commitados_estao_em_dia():
    for caminho, conteudo in gerar(RAIZ).items():
        assert (RAIZ / caminho).read_text(encoding="utf-8") == conteudo, f"{caminho} desatualizado: rode python -m scripts.gerar_adaptador_claude"


def test_main_escreve_os_ficheiros(tmp_path):
    (tmp_path / "skills" / "x").mkdir(parents=True)
    (tmp_path / "skills" / "x" / "SKILL.md").write_text("---\nname: x\ndescription: faz x\n---\ncorpo\n", encoding="utf-8")
    assert main([str(tmp_path)]) == 0
    assert (tmp_path / "adaptadores" / "claude" / "x" / "SKILL.md").exists()
