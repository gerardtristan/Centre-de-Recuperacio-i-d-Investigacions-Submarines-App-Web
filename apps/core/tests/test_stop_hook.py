"""Hook de fi de torn de Claude Code (T-M00-07, CA-M00-07f): quan bloqueja i quan deixa parar."""

import importlib.util
from pathlib import Path

from django.conf import settings

spec = importlib.util.spec_from_file_location(
    "stop_check", Path(settings.BASE_DIR) / ".claude" / "hooks" / "stop_check.py"
)
stop_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stop_check)


def test_without_changes_it_says_nothing():
    assert stop_check.decide(False, changed=False, ok=None, output="") is None


def test_when_the_checks_pass_it_says_nothing():
    assert stop_check.decide(False, changed=True, ok=True, output="") is None


def test_a_first_failure_blocks_with_the_error():
    answer = stop_check.decide(False, changed=True, ok=False, output="Ha fallat: ruff check")
    assert answer["decision"] == "block" and "Ha fallat: ruff check" in answer["reason"]


def test_after_blocking_once_it_lets_claude_stop_and_shows_the_error():
    answer = stop_check.decide(True, changed=True, ok=False, output="Ha fallat: pytest")
    assert "decision" not in answer and "Ha fallat: pytest" in answer["systemMessage"]
