"""Verificació del codi en tres capes (T-M00-07, CA-M00-07f; decisió 081, punt 1).

1. **Hook de fi de torn** (`.claude/hooks/stop_check.py`): ràpid i amb un límit de 90 s. Mai no
   passa la suite sencera ni deixa res en segon pla.
2. **Verificació completa** (aquest fitxer, `python tools/verifica.py`): explícita, abans del commit
   quan el hook l'ha deixada pendent. Passa tot el que passa el CI.
3. **CI** (`.github/workflows/ci.yml`): sense canvis; és la porta final.

Aquest mòdul té el que comparteixen el hook i la verificació completa:

- **Empremta del contingut** (`snapshot`, `fingerprint`): el SHA-256 de cada fitxer vigilat (els
  de Git i els nous no ignorats). Un resultat només val per a l'empremta exacta que es va
  verificar: qualsevol canvi la fa diferent i el resultat anterior no es reutilitza.
- **Resultats** (`.e2e-captures/.verificacio.json`, fora de Git).
- **Una sola execució alhora** (`Lock`): el hook i la verificació completa fan servir la mateixa
  base de proves, de manera que no poden anar a la vegada. Si el bloqueig és d'un procés viu, no
  es toca: qui arriba després no s'executa i ho diu. Un bloqueig d'un procés que ja no existeix
  s'esborra.
- **Límit de temps** (`run`): cada ordre s'executa en un grup de processos propi. Si s'acaba el
  temps, es mata **només aquest arbre** (el navegador i el servidor de proves que ha obert), mai
  cap altre procés de la màquina, i el resultat és «no conclusiu», mai verd.
"""

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR_NAME = ".e2e-captures"
STATE_NAME = ".verificacio.json"
LOCK_NAME = ".verificacio.lock"
# El que pot canviar el resultat de les proves. La documentació no hi és.
WATCHED = (
    "apps",
    "templates",
    "static",
    "config",
    "design",
    ".claude/hooks",
    "tools",
    ".github/workflows",
    "conftest.py",
    "pyproject.toml",
    "manage.py",
)
KEEP_RESULTS = 20


def python(root: Path = ROOT) -> str:
    for candidate in (root / ".venv" / "Scripts" / "python.exe", root / ".venv" / "bin" / "python"):
        if candidate.exists():
            return str(candidate)
    return sys.executable


# --- Empremta -------------------------------------------------------------------------------------


def watched_files(root: Path = ROOT) -> list[str]:
    """Fitxers vigilats: els de Git i els nous que no estan ignorats, amb camins amb «/»."""
    out = subprocess.run(  # noqa: S603
        ["git", "ls-files", "-co", "--exclude-standard", "-z", "--", *WATCHED],  # noqa: S607
        cwd=root,
        capture_output=True,
        check=False,
    ).stdout
    names = {name.decode("utf-8") for name in out.split(b"\0") if name}
    return sorted(name for name in names if (root / name).is_file())


def snapshot(root: Path = ROOT) -> dict[str, str]:
    """{camí: SHA-256 del contingut} de cada fitxer vigilat."""
    return {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in watched_files(root)
    }


def fingerprint(snap: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for name in sorted(snap):
        digest.update(f"{name}\0{snap[name]}\n".encode())
    return digest.hexdigest()


def changed_files(before: dict[str, str] | None, after: dict[str, str]) -> list[str]:
    """Fitxers nous, modificats o esborrats. Sense referència, tots són nous."""
    before = before or {}
    return sorted(
        {name for name in after if before.get(name) != after[name]} | (set(before) - set(after))
    )


# --- Resultats ------------------------------------------------------------------------------------


def state_path(root: Path = ROOT) -> Path:
    return root / STATE_DIR_NAME / STATE_NAME


def load_state(root: Path = ROOT) -> dict:
    try:
        state = json.loads(state_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    state.setdefault("full", {})
    state.setdefault("durations", {})
    return state


def save_state(state: dict, root: Path = ROOT) -> None:
    full = state.get("full", {})
    if len(full) > KEEP_RESULTS:  # només els més recents
        for old in sorted(full, key=lambda fp: full[fp].get("at", ""))[:-KEEP_RESULTS]:
            del full[old]
    path = state_path(root)
    path.parent.mkdir(exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def full_ok(state: dict, fp: str) -> bool:
    return bool(state.get("full", {}).get(fp, {}).get("ok"))


def record_full(state: dict, fp: str, snap: dict, ok: bool, steps: dict) -> None:
    """Resultat de la verificació completa per a aquesta empremta exacta. Si és verd, també és
    la referència dels canvis següents i treu la marca de pendent."""
    state["full"][fp] = {"ok": ok, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "steps": steps}
    if ok:
        state["reference"] = snap
        state["hook_ok"] = fp
        state["pending_full"] = False
        state["dirty_db"] = False


# --- Una sola execució alhora ---------------------------------------------------------------------


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)  # senyal 0: només comprova; a Windows no s'hi arriba
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class Busy(Exception):  # noqa: N818 (no és un error del programa)
    def __init__(self, holder: dict):
        super().__init__(holder)
        self.holder = holder


class Lock:
    """Bloqueig de fitxer amb el número del procés que el té. No mata mai el procés d'un altre."""

    def __init__(self, what: str, fp: str, root: Path = ROOT):
        self.path = root / STATE_DIR_NAME / LOCK_NAME
        self.data = {"pid": os.getpid(), "what": what, "fingerprint": fp, "at": time.time()}
        self.held = False

    def acquire(self) -> "Lock":
        self.path.parent.mkdir(exist_ok=True)
        for _ in range(2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                holder = self._holder()
                if holder and pid_alive(int(holder.get("pid", 0))):
                    raise Busy(holder) from None
                with suppress(FileNotFoundError):
                    self.path.unlink()  # d'un procés que ja no hi és
                continue
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh)
            self.held = True
            return self
        raise Busy(self._holder() or {})

    def _holder(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def release(self) -> None:
        if self.held and self._holder().get("pid") == os.getpid():
            with suppress(FileNotFoundError):
                self.path.unlink()
        self.held = False

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *exc):
        self.release()


# --- Ordres amb límit de temps --------------------------------------------------------------------


@dataclass
class Result:
    returncode: int | None
    output: str
    seconds: float
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return not self.timed_out and self.returncode == 0


def kill_tree(process: subprocess.Popen) -> None:
    """Mata el procés i tots els seus descendents, i res més."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(  # noqa: S603
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],  # noqa: S607
            capture_output=True,
            check=False,
        )
    else:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    with suppress(subprocess.TimeoutExpired):
        process.wait(timeout=10)


def run(command: list[str], *, cwd: Path = ROOT, timeout: float | None = None, env=None) -> Result:
    """Executa l'ordre en un grup de processos propi. Amb `timeout`, si s'acaba el temps se'n mata
    tot l'arbre i el resultat és «no conclusiu» (`timed_out`)."""
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    start = time.monotonic()
    process = subprocess.Popen(  # noqa: S603 (ordres fixes de qui crida)
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        **kwargs,
    )
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(process)
        output = ""
        with suppress(Exception):
            output = process.communicate(timeout=5)[0] or ""
        return Result(None, output, time.monotonic() - start, timed_out=True)
    except BaseException:
        kill_tree(process)  # Ctrl+C o qualsevol altra interrupció: res abandonat
        raise
    return Result(process.returncode, output, time.monotonic() - start)


def durations_from_junit(path: Path) -> dict[str, float]:
    """Segons per fitxer de prova, a partir del JUnit XML de pytest."""
    import xml.etree.ElementTree as ET  # noqa: S405 (fitxer generat per pytest en aquesta màquina)

    try:
        tree = ET.parse(path)  # noqa: S314
    except (OSError, ET.ParseError):
        return {}
    totals: dict[str, float] = {}
    for case in tree.iter("testcase"):
        classname = case.get("classname", "")
        name = classname.split(".")
        files = [part for part in name if part.startswith("test_")]
        if not files:
            continue
        key = files[0] + ".py"
        totals[key] = totals.get(key, 0.0) + float(case.get("time", 0) or 0)
    return totals
