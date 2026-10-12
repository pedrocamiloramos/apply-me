import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.resultado import Estado
from scripts.verificar_commit import main, verificar_commit

RAIZ = Path(__file__).resolve().parent.parent


def test_commit_valido():
    assert verificar_commit("feat(scripts): add x").estado is Estado.PASSOU
    assert verificar_commit("fix!: break api\n\ncorpo\n\nCo-Authored-By: X <x@exemplo.invalid>").estado is Estado.PASSOU
    assert verificar_commit("Merge branch 'x'").estado is Estado.PASSOU


def test_commit_invalido_reprova():
    r = verificar_commit("updated stuff")
    assert r.estado is Estado.REPROVOU and r.achados[0].codigo == "COMMIT_FORA_DO_PADRAO"


@pytest.mark.parametrize("msg", ["", "\n\n", "feat:sem espaço", "feat(): vazio", "Feat: maiúscula", "feat: "])
def test_mensagens_mal_formadas_reprovam(msg):
    assert verificar_commit(msg).estado is Estado.REPROVOU


def test_comentarios_do_git_sao_ignorados():
    assert verificar_commit("# comentário do editor\nfeat: add y\n").estado is Estado.PASSOU


def test_main_le_o_ficheiro_da_mensagem(tmp_path):
    ok, mau = tmp_path / "ok", tmp_path / "mau"
    ok.write_text("docs: update readme\n", encoding="utf-8")
    mau.write_text("coisas\n", encoding="utf-8")
    assert main([str(ok)]) == 0 and main([str(mau)]) == 1 and main([]) == 1


def test_hook_commit_msg_existe_e_e_instalado_pelo_script():
    hook = RAIZ / "scripts" / "hooks" / "commit-msg"
    assert hook.exists() and os.access(hook, os.X_OK)
    assert "scripts.verificar_commit" in hook.read_text(encoding="utf-8")


def test_hook_recusa_mensagem_invalida(tmp_path):
    msg = tmp_path / "msg"
    msg.write_text("coisas\n", encoding="utf-8")
    env = {**os.environ, "PYTHON": sys.executable}
    r = subprocess.run([str(RAIZ / "scripts" / "hooks" / "commit-msg"), str(msg)], cwd=RAIZ, env=env, capture_output=True)
    assert r.returncode == 1
