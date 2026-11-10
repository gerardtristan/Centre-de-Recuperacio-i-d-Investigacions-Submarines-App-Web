"""Hook de Claude Code en acabar el torn (T-M00-07, CA-M00-07f).

Si el codi d'`apps/`, `templates/` o `static/` ha canviat des de l'última comprovació correcta,
executa `ruff check`, `ruff format --check` i la suite e2e (`pytest -m e2e`), amb un límit total
de 90 s. Si falla, torna l'error a Claude perquè l'arregli abans de parar. Si ja havia bloquejat
una vegada (`stop_hook_active`), deixa parar i ensenya l'error a la persona: cap bucle.

Funciona a Windows i a Linux: només fa servir Python i git. Estat a `.e2e-captures/` (fora de Git).
"""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WATCHED = ("apps", "templates", "static")
STATE = ROOT / ".e2e-captures" / ".hook-state.json"
LIMIT_SECONDS = 90
TAIL_LINES = 40


def python() -> str:
    for candidate in (ROOT / ".venv" / "Scripts" / "python.exe", ROOT / ".venv" / "bin" / "python"):
        if candidate.exists():
            return str(candidate)
    return sys.executable


def git(*args) -> bytes:
    # Arguments fixos d'aquest fitxer; `git` del PATH, com qualsevol ordre del projecte.
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        check=False,
    ).stdout


def fingerprint() -> str:
    """Empremta del codi vigilat: arbres de HEAD, canvis sense desar i fitxers nous."""
    digest = hashlib.sha256()
    for folder in WATCHED:
        digest.update(git("rev-parse", f"HEAD:{folder}"))
    digest.update(git("diff", "HEAD", "--", *WATCHED))
    untracked = git("ls-files", "--others", "--exclude-standard", "-z", *WATCHED)
    for name in sorted(untracked.split(b"\0")):
        if name:
            digest.update(name)
            path = ROOT / name.decode()
            if path.is_file():
                digest.update(path.read_bytes())
    return digest.hexdigest()


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state), encoding="utf-8")


def run_checks(dirty_db: bool) -> tuple[bool, str, bool]:
    """(correcte, sortida, s'ha tallat per temps). Para al primer error."""
    py = python()
    db_flag = "--create-db" if dirty_db else "--reuse-db"
    commands = [
        [py, "-m", "ruff", "check", "."],
        [py, "-m", "ruff", "format", "--check", "."],
        [py, "-m", "pytest", "-m", "e2e", "apps/core/tests/e2e", "-q", "-p", "no:cacheprovider",
         db_flag],
    ]  # fmt: skip
    deadline = time.monotonic() + LIMIT_SECONDS
    for command in commands:
        remaining = deadline - time.monotonic()
        try:
            done = subprocess.run(  # noqa: S603 (ordres fixes d'aquest fitxer)
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max(remaining, 1),
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False, f"Temps esgotat ({LIMIT_SECONDS} s) a: {' '.join(command[2:])}", True
        if done.returncode != 0:
            output = (done.stdout + done.stderr).strip().splitlines()[-TAIL_LINES:]
            return False, f"Ha fallat: {' '.join(command[2:])}\n" + "\n".join(output), False
    return True, "", False


def decide(stop_hook_active: bool, changed: bool, ok: bool | None, output: str) -> dict | None:
    """Resposta per a Claude Code. `None`: no cal dir res (no hi ha canvis o tot és correcte)."""
    if not changed or ok:
        return None
    if stop_hook_active:
        return {
            "systemMessage": "La verificació continua fallant després d'un intent d'arreglar-la."
            " Revisa-ho tu:\n" + output
        }
    return {
        "decision": "block",
        "reason": "La verificació de fi de torn (T-M00-07) ha fallat. Arregla-ho abans de"
        " parar; si no es pot arreglar sense una decisió, explica-ho.\n" + output,
    }


def main() -> int:
    # Bytes en UTF-8 a l'entrada i JSON en ASCII a la sortida: a Windows, la codificació per
    # defecte de les canonades no és UTF-8 i els accents arribarien trencats.
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
    except ValueError:
        event = {}
    state = load_state()
    current = fingerprint()
    changed = current != state.get("passed")
    ok, output = None, ""
    if changed:
        ok, output, timed_out = run_checks(state.get("dirty_db", False))
        # Un pytest tallat pel temps no neteja la base reutilitzada: la propera es torna a crear.
        state["dirty_db"] = timed_out
        if ok:
            state["passed"] = current
        save_state(state)
    answer = decide(bool(event.get("stop_hook_active")), changed, ok, output)
    if answer:
        print(json.dumps(answer))
    return 0


if __name__ == "__main__":
    sys.exit(main())
