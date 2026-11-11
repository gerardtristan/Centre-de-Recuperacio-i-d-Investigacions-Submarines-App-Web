"""Verificació en tres capes (T-M00-07, CA-M00-07f; decisió 081, punt 1): proves del mecanisme.

- El mapa d'e2e és complet i no té patrons morts.
- La selecció: conjunt mínim; fitxers del mapa; compartits, desconeguts o massa llargs deixen la
  verificació completa obligatòria.
- Els resultats van lligats al contingut exacte: un canvi no reutilitza el resultat anterior.
- Un error bloqueja una sola vegada; un temps esgotat és «no conclusiu», mai verd, i no bloqueja.
- Una sola execució alhora, sense tocar mai el procés d'un altre; quan s'acaba el temps, es mata
  només l'arbre de processos propi.

No obre cap navegador: les ordres es substitueixen per un doble, llevat de la prova de l'arbre
de processos, que fa servir processos de Python que només esperen.
"""

import importlib.util
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from django.conf import settings

ROOT = Path(settings.BASE_DIR)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verificacio = _load("verificacio_t", ROOT / "tools" / "verificacio.py")
e2e_map = _load("e2e_map_t", ROOT / ".claude" / "hooks" / "e2e_map.py")
hook = _load("stop_check_t", ROOT / ".claude" / "hooks" / "stop_check.py")


# --- Mapa ----------------------------------------------------------------------------------------


def test_e2e_map_covers_every_e2e_test_file():
    files = {path.name for path in (ROOT / e2e_map.E2E_DIR).glob("test_*.py")}
    assert files == set(e2e_map.MAP)
    assert e2e_map.SMOKE in files


def test_e2e_map_has_no_dead_patterns():
    tracked = verificacio.watched_files(ROOT)
    for test, patterns in e2e_map.MAP.items():
        for pattern in patterns:
            assert any(e2e_map._matches(path, [pattern]) for path in tracked), (test, pattern)


def test_settings_give_the_hook_more_time_than_its_own_limit():
    config = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    [entry] = config["hooks"]["Stop"][0]["hooks"]
    assert entry["timeout"] > hook.LIMIT_SECONDS == 90
    assert "stop_check.py" in entry["command"]


# --- Selecció ------------------------------------------------------------------------------------


def test_a_mapped_file_selects_its_tests_and_the_smoke_set():
    tests, full, _ = e2e_map.plan(["apps/members/policies.py"])
    assert tests == ["test_politiques_079.py", "test_smoke.py"]
    assert full is False


def test_a_changed_e2e_file_runs_itself():
    tests, full, _ = e2e_map.plan([f"{e2e_map.E2E_DIR}/test_rgpd.py"])
    assert tests == ["test_rgpd.py", "test_smoke.py"] and full is False


@pytest.mark.parametrize(
    "path",
    [
        "templates/base.html",
        "static/css/comptes.css",
        "apps/core/models.py",
        "config/settings/base.py",
    ],
)
def test_a_shared_file_runs_only_the_smoke_set_and_requires_the_full_verification(path):
    tests, full, reasons = e2e_map.plan([path])
    assert tests == ["test_smoke.py"] and full is True
    assert reasons == [f"compartit: {path}"]


@pytest.mark.parametrize(
    "path", ["apps/members/tests/test_cards.py", "templates/emails/baixa-efectiva.ca.txt", "x.py"]
)
def test_an_unknown_file_also_requires_the_full_verification(path):
    tests, full, _ = e2e_map.plan([path])
    assert tests == ["test_smoke.py"] and full is True


def test_a_selection_too_long_falls_back_to_the_smoke_set():
    # Una plantilla també necessita l'auditoria d'accessibilitat, que no hi cap.
    tests, full, reasons = e2e_map.plan(["templates/members/fees.html"], budget=70)
    assert tests == ["test_smoke.py"] and full is True
    assert reasons[-1].startswith("selecció massa llarga")
    # Amb els temps mesurats, la mateixa selecció pot cabre.
    durations = {name: 1 for name in e2e_map.MAP}
    tests, full, _ = e2e_map.plan(["templates/members/fees.html"], durations, budget=70)
    assert "test_quotes_079.py" in tests and full is False


# --- Empremta i resultats -------------------------------------------------------------------------


@pytest.fixture
def repo(tmp_path):
    """Un repositori de Git petit amb fitxers vigilats."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)  # noqa: S607
    (tmp_path / "apps").mkdir()
    (tmp_path / "apps" / "a.py").write_text("A = 1\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "nota.md").write_text("res\n", encoding="utf-8")
    return tmp_path


def test_the_fingerprint_is_the_exact_content(repo):
    first = verificacio.snapshot(repo)
    assert list(first) == ["apps/a.py"]  # la documentació no és vigilada
    (repo / "apps" / "a.py").write_text("A = 2\n", encoding="utf-8")
    second = verificacio.snapshot(repo)
    assert verificacio.fingerprint(first) != verificacio.fingerprint(second)
    assert verificacio.changed_files(first, second) == ["apps/a.py"]
    (repo / "apps" / "a.py").write_text("A = 1\n", encoding="utf-8")
    assert verificacio.fingerprint(verificacio.snapshot(repo)) == verificacio.fingerprint(first)


def test_a_full_result_is_only_reused_for_the_same_content(repo):
    state = verificacio.load_state(repo)
    snap = verificacio.snapshot(repo)
    fp = verificacio.fingerprint(snap)
    verificacio.record_full(state, fp, snap, True, {"pytest": {"ok": True}})
    verificacio.save_state(state, repo)
    assert verificacio.full_ok(verificacio.load_state(repo), fp)
    (repo / "apps" / "a.py").write_text("A = 3\n", encoding="utf-8")
    new_fp = verificacio.fingerprint(verificacio.snapshot(repo))
    assert not verificacio.full_ok(verificacio.load_state(repo), new_fp)


def test_a_red_full_verification_keeps_it_pending(repo):
    state = {"full": {}, "durations": {}, "pending_full": True}
    snap = verificacio.snapshot(repo)
    verificacio.record_full(state, verificacio.fingerprint(snap), snap, False, {})
    assert state["pending_full"] is True and "reference" not in state


# --- Decisions del hook ---------------------------------------------------------------------------


def outcome(status, full=False, output="sortida"):
    return {"status": status, "full_required": full, "reasons": [], "output": output}


def test_a_failure_blocks_once_and_then_only_reports():
    first = hook.decide(False, outcome("failed"), False)
    assert first["decision"] == "block"
    second = hook.decide(True, outcome("failed"), False)
    assert "decision" not in second and "No s'ha donat per verificada" in second["systemMessage"]


def test_a_timeout_is_inconclusive_never_green_and_never_blocks():
    for active in (False, True):
        answer = hook.decide(active, outcome("inconclusive", True), True)
        assert "decision" not in answer
        assert "NO CONCLUSIVA" in answer["systemMessage"]
        assert hook.FULL_COMMAND in answer["systemMessage"]


def test_green_with_the_full_verification_pending_only_reminds():
    assert hook.decide(False, outcome("ok"), True) == {
        "systemMessage": f"Verificació completa pendent abans del commit: {hook.FULL_COMMAND}."
    }
    assert hook.decide(False, outcome("ok"), False) is None


class FakeRunner:
    """Doble de `verificacio.run`: respon segons l'ordre i guarda què s'ha demanat."""

    def __init__(self, e2e="ok"):
        self.e2e, self.calls = e2e, []

    def __call__(self, command, *, cwd, timeout=None, env=None):
        self.calls.append(command)
        if "pytest" in command:
            if self.e2e == "timeout":
                return verificacio.Result(None, "", timeout or 0, timed_out=True)
            return verificacio.Result(0 if self.e2e == "ok" else 1, "1 failed", 1.0)
        return verificacio.Result(0, "", 0.1)


def run_hook(repo, runner, active=False):
    stdin = io.BytesIO(json.dumps({"stop_hook_active": active}).encode())
    return hook.main(root=repo, runner=runner, stdin=stdin)


def test_hook_end_to_end_with_results_tied_to_the_content(repo):
    runner = FakeRunner()
    # Primera vegada: sense referència, tot és nou (desconegut) → mínim i completa pendent.
    answer = run_hook(repo, runner)
    assert answer["systemMessage"].startswith("Verificació completa pendent")
    assert any("test_smoke.py" in " ".join(c) for c in runner.calls)
    state = verificacio.load_state(repo)
    fp = verificacio.fingerprint(verificacio.snapshot(repo))
    assert state["hook_ok"] == fp and state["pending_full"] is True
    # El mateix contingut: no torna a passar res.
    runner.calls.clear()
    run_hook(repo, runner)
    assert runner.calls == []
    # Un canvi: es torna a comprovar.
    (repo / "apps" / "a.py").write_text("A = 9\n", encoding="utf-8")
    run_hook(repo, runner)
    assert runner.calls


def test_hook_failure_is_not_recorded_as_checked(repo):
    answer = run_hook(repo, FakeRunner(e2e="failed"))
    assert answer["decision"] == "block"
    state = verificacio.load_state(repo)
    assert "hook_ok" not in state and "reference" not in state
    again = run_hook(repo, FakeRunner(e2e="failed"), active=True)
    assert "decision" not in again


def test_hook_timeout_is_not_recorded_as_checked_and_recreates_the_db(repo):
    answer = run_hook(repo, FakeRunner(e2e="timeout"))
    assert "NO CONCLUSIVA" in answer["systemMessage"] and "decision" not in answer
    state = verificacio.load_state(repo)
    assert "hook_ok" not in state and state["dirty_db"] is True and state["pending_full"] is True
    runner = FakeRunner()
    run_hook(repo, runner)
    assert "--create-db" in runner.calls[-1]


def test_hook_does_not_touch_another_running_verification(repo):
    other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])  # noqa: S603
    try:
        lock_file = repo / verificacio.STATE_DIR_NAME / verificacio.LOCK_NAME
        lock_file.parent.mkdir(exist_ok=True)
        lock_file.write_text(json.dumps({"pid": other.pid, "what": "altra"}), encoding="utf-8")
        runner = FakeRunner()
        answer = run_hook(repo, runner)
        assert "NO CONCLUSIVA" in answer["systemMessage"]
        assert not any("pytest" in c for c in runner.calls)  # cap e2e
        assert other.poll() is None and lock_file.exists()  # l'altre continua igual
    finally:
        other.kill()
        other.wait()


# --- Bloqueig i arbre de processos ----------------------------------------------------------------


def test_lock_is_single_and_a_stale_one_is_cleaned(repo):
    first = verificacio.Lock("a", "fp", repo).acquire()
    with pytest.raises(verificacio.Busy):
        verificacio.Lock("b", "fp", repo).acquire()
    first.release()
    lock_file = repo / verificacio.STATE_DIR_NAME / verificacio.LOCK_NAME
    lock_file.write_text(json.dumps({"pid": 2**22 + 12345}), encoding="utf-8")  # cap procés
    with verificacio.Lock("c", "fp", repo):
        assert json.loads(lock_file.read_text(encoding="utf-8"))["pid"] == os.getpid()
    assert not lock_file.exists()


def test_a_timeout_kills_only_its_own_process_tree(tmp_path):
    pid_file = tmp_path / "net.pid"
    child = (
        "import subprocess, sys, time; "
        "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
        f"open(r'{pid_file}', 'w').write(str(p.pid)); time.sleep(60)"
    )
    bystander = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])  # noqa: S603
    try:
        result = verificacio.run([sys.executable, "-c", child], cwd=tmp_path, timeout=3)
        assert result.timed_out and not result.ok and result.returncode is None
        grandchild = int(pid_file.read_text())
        for _ in range(50):
            if not verificacio.pid_alive(grandchild):
                break
            time.sleep(0.1)
        assert not verificacio.pid_alive(grandchild)
        assert bystander.poll() is None  # un procés aliè no es toca
    finally:
        bystander.kill()
        bystander.wait()


def test_durations_are_read_per_test_file(tmp_path):
    xml = tmp_path / "j.xml"
    xml.write_text(
        '<testsuites><testsuite><testcase classname="apps.core.tests.e2e.test_rgpd" time="2.5"/>'
        '<testcase classname="apps.core.tests.e2e.test_rgpd" time="1.5"/>'
        '<testcase classname="apps.core.tests.e2e.test_smoke" time="3"/></testsuite></testsuites>',
        encoding="utf-8",
    )
    assert verificacio.durations_from_junit(xml) == {"test_rgpd.py": 4.0, "test_smoke.py": 3.0}
