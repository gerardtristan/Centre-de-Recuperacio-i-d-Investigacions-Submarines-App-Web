"""Hook de fi de torn de Claude Code (T-M00-07, CA-M00-07f): quan bloqueja i quan deixa parar.

Amb la decisió 081 (punt 1), `decide` rep el resultat de la comprovació (`None` si no hi ha cap
canvi) i si la verificació completa és pendent. La resta del mecanisme es prova a
`test_verificacio_t_m00_07.py`.
"""

import importlib.util
from pathlib import Path

from django.conf import settings

spec = importlib.util.spec_from_file_location(
    "stop_check", Path(settings.BASE_DIR) / ".claude" / "hooks" / "stop_check.py"
)
stop_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stop_check)


def outcome(status, output=""):
    return {"status": status, "full_required": False, "reasons": [], "output": output}


def test_without_changes_it_says_nothing():
    assert stop_check.decide(False, None, pending_full=False) is None


def test_when_the_checks_pass_it_says_nothing():
    assert stop_check.decide(False, outcome("ok"), pending_full=False) is None


def test_a_first_failure_blocks_with_the_error():
    answer = stop_check.decide(False, outcome("failed", "Ha fallat: ruff check"), False)
    assert answer["decision"] == "block" and "Ha fallat: ruff check" in answer["reason"]


def test_after_blocking_once_it_lets_claude_stop_and_shows_the_error():
    answer = stop_check.decide(True, outcome("failed", "Ha fallat: pytest"), False)
    assert "decision" not in answer and "Ha fallat: pytest" in answer["systemMessage"]
