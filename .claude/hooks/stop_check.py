"""Hook de Claude Code en acabar el torn (T-M00-07, CA-M00-07f; decisió 081, punt 1).

Primera de les tres capes de `tools/verificacio.py`: ràpida, amb un límit total de 90 s.

- Si la verificació completa ja és verda per al contingut exacte d'ara, o el hook ja l'havia
  comprovat, no torna a passar res.
- Si hi ha canvis, sempre passa `ruff check` i `ruff format --check`. Després tria les proves e2e
  amb el mapa (`e2e_map.py`): el conjunt mínim i les del mapa per als fitxers canviats. Un fitxer
  compartit, un de desconegut o una selecció que no hi cap passen només el conjunt mínim i deixen
  la **verificació completa obligatòria** abans del commit (`python tools/verifica.py`).
- **Error real:** bloqueja el final del torn una sola vegada perquè Claude ho arregli. Si ja havia
  bloquejat (`stop_hook_active`), deixa parar i mostra l'error: cap bucle, i l'error no s'amaga
  ni es dona per verificat.
- **Temps esgotat:** mata només l'arbre de processos que ha obert (navegador i servidor de
  proves), el resultat és **no conclusiu** (mai verd), no bloqueja, i la verificació completa
  queda obligatòria.
- **Una altra verificació en marxa** (mateixa base de proves): no hi toca, passa només ruff i diu
  que el resultat no és conclusiu.
- Mai no llança res en segon pla.

Funciona a Windows i a Linux: només Python i git. Estat a `.e2e-captures/` (fora de Git).
"""

import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIMIT_SECONDS = 90
E2E_BUDGET_SECONDS = 70
TAIL_LINES = 40
FULL_COMMAND = "python tools/verifica.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verificacio = _load("verificacio", ROOT / "tools" / "verificacio.py")
e2e_map = _load("e2e_map", Path(__file__).with_name("e2e_map.py"))


def _tail(text: str) -> str:
    return "\n".join(text.strip().splitlines()[-TAIL_LINES:])


def _outcome(status, full_required, reasons, output):
    return {"status": status, "full_required": full_required, "reasons": reasons, "output": output}


def check(state: dict, changed: list[str], *, runner=None, root: Path = ROOT, fp: str = "") -> dict:
    """Comprova els canvis i torna el resultat: `status` («ok», «failed» o «inconclusive»),
    `full_required`, `reasons` i `output`. `runner` és `verificacio.run` (a les proves, un
    doble)."""
    runner = runner or verificacio.run
    py = verificacio.python(root)
    deadline = time.monotonic() + LIMIT_SECONDS
    tests, full_required, reasons = e2e_map.plan(
        changed, state.get("durations"), budget=E2E_BUDGET_SECONDS
    )
    for command in (
        [py, "-m", "ruff", "check", "."],
        [py, "-m", "ruff", "format", "--check", "."],
    ):
        result = runner(command, cwd=root, timeout=max(deadline - time.monotonic(), 1))
        what = " ".join(command[2:])
        if result.timed_out:
            return _outcome("inconclusive", True, reasons, f"Temps esgotat a: {what}")
        if not result.ok:
            return _outcome(
                "failed", full_required, reasons, f"Ha fallat: {what}\n{_tail(result.output)}"
            )
    try:
        lock = verificacio.Lock("hook", fp, root).acquire()
    except verificacio.Busy as busy:
        return _outcome(
            "inconclusive",
            True,
            reasons,
            f"Una altra verificació fa servir la base de proves (procés {busy.holder.get('pid')}):"
            " no s'han passat les e2e.",
        )
    junit = root / verificacio.STATE_DIR_NAME / ".hook-junit.xml"
    command = [
        py, "-m", "pytest", "-m", "e2e", "-q", "-p", "no:cacheprovider",
        "--create-db" if state.get("dirty_db") else "--reuse-db",
        f"--junitxml={junit}",
        *(f"{e2e_map.E2E_DIR}/{test}" for test in tests),
    ]  # fmt: skip
    try:
        result = runner(command, cwd=root, timeout=max(deadline - time.monotonic(), 1))
    finally:
        lock.release()
    state["durations"].update(verificacio.durations_from_junit(junit))
    names = ", ".join(tests)
    if result.timed_out:
        # Un pytest aturat no neteja la base reutilitzada: la propera es torna a crear.
        state["dirty_db"] = True
        return _outcome(
            "inconclusive", True, reasons, f"Temps esgotat ({LIMIT_SECONDS} s) a les e2e: {names}"
        )
    state["dirty_db"] = False
    if not result.ok:
        return _outcome(
            "failed",
            full_required,
            reasons,
            f"Han fallat les e2e ({names}):\n{_tail(result.output)}",
        )
    return _outcome("ok", full_required, reasons, f"e2e: {names}")


def decide(stop_hook_active: bool, outcome: dict | None, pending_full: bool) -> dict | None:
    """Resposta per a Claude Code. `None`: no cal dir res."""
    reminder = (
        f"Verificació completa pendent abans del commit: {FULL_COMMAND}." if pending_full else ""
    )
    if outcome is None or outcome["status"] == "ok":
        return {"systemMessage": reminder} if reminder else None
    if outcome["status"] == "inconclusive":
        return {
            "systemMessage": "Verificació de fi de torn NO CONCLUSIVA (no és un resultat verd). "
            + outcome["output"]
            + (f"\n{reminder}" if reminder else "")
        }
    if stop_hook_active:
        return {
            "systemMessage": "La verificació continua fallant després d'un intent d'arreglar-la."
            " No s'ha donat per verificada. Revisa-ho tu:\n" + outcome["output"]
        }
    return {
        "decision": "block",
        "reason": "La verificació de fi de torn (T-M00-07) ha fallat. Arregla-ho abans de"
        " parar; si no es pot arreglar sense una decisió, explica-ho.\n" + outcome["output"],
    }


def main(root: Path = ROOT, runner=None, stdin=None) -> dict | None:
    # Bytes en UTF-8 a l'entrada i JSON en ASCII a la sortida: a Windows, la codificació per
    # defecte de les canonades no és UTF-8 i els accents arribarien trencats.
    raw = (stdin or sys.stdin.buffer).read()
    try:
        event = json.loads(raw.decode("utf-8", "replace") or "{}")
    except ValueError:
        event = {}
    active = bool(event.get("stop_hook_active"))
    state = verificacio.load_state(root)
    snap = verificacio.snapshot(root)
    fp = verificacio.fingerprint(snap)
    if verificacio.full_ok(state, fp) or state.get("hook_ok") == fp:
        return decide(active, None, bool(state.get("pending_full")))
    changed = verificacio.changed_files(state.get("reference"), snap)
    outcome = check(state, changed, runner=runner, root=root, fp=fp) if changed else None
    if outcome is None or outcome["status"] == "ok":
        # Només un resultat verd pot ser la referència dels canvis següents.
        state["hook_ok"] = fp
        state["reference"] = snap
    if outcome and outcome["full_required"]:
        # Només la verificació completa verda la treu (`verificacio.record_full`).
        state["pending_full"] = True
    verificacio.save_state(state, root)
    return decide(active, outcome, bool(state.get("pending_full")))


if __name__ == "__main__":
    answer = main()
    if answer:
        print(json.dumps(answer))
    sys.exit(0)
