"""La comprovació de desplegament de `tools/verifica.py` defineix les mateixes variables que el pas
«Comprovació de desplegament» del CI (T-F1-01). Si en falta una, la verificació local falla on
el CI passa (com `MANDATE_ENCRYPTION_KEYS`, que el CI exporta i `deploy_env` no tenia)."""

import importlib.util
import re
from pathlib import Path

from django.conf import settings

ROOT = Path(settings.BASE_DIR)


def _verifica():
    spec = importlib.util.spec_from_file_location("verifica_t", ROOT / "tools" / "verifica.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ci_deploy_variables() -> set[str]:
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    step = ci.split("- name: Comprovació de desplegament", 1)[1].split("\n  e2e:", 1)[0]
    exported = set(re.findall(r"export ([A-Z_]+)=", step))
    declared = set(re.findall(r"^\s{10}([A-Z_]+):", step, re.MULTILINE))
    return exported | declared


def test_deploy_env_te_totes_les_variables_del_ci(monkeypatch):
    expected = _ci_deploy_variables()
    for name in expected:  # sense les de l'entorn de qui executa (les proves en defineixen)
        monkeypatch.delenv(name, raising=False)
    assert "MANDATE_ENCRYPTION_KEYS" in expected  # el patró llegeix el pas de veritat
    assert expected - set(_verifica().deploy_env()) == set()
