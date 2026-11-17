#!/usr/bin/env python3
"""Genera la línia cronològica interactiva del projecte (un sol fitxer HTML).

Llegeix una referència de Git del repositori (per defecte, `HEAD`) sense tocar-ne cap fitxer:
`docs/planning.md`, `docs/decisions/`, `docs/diari-de-construccio/`, `docs/preguntes-externes.md`
i el `git log`. No inventa res: el que no troba surt com a «no trobat» a la pàgina.

Ús local (sense xifrar, per obrir-lo amb doble clic):

    python tools/linia-cronologica/generate.py --out CRIS_linia_cronologica.html

Ús al workflow (xifrat; la contrasenya ve de la variable d'entorn `TIMELINE_PASSPHRASE`):

    python tools/linia-cronologica/generate.py --ref origin/master --runs runs.jsonl \
        --encrypt --out public/index.html
"""

from __future__ import annotations

import argparse
import base64
import collections
import datetime
import io
import json
import os
import re
import subprocess  # noqa: S404  (només crida `git` amb arguments fixos)
import sys
import zoneinfo
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK_ID = r"T-[A-Za-z0-9]+-\d+[a-z]?"
MIN_PASSPHRASE = 16
KDF_ITERATIONS = 600_000

MODULE_NAMES = {
    "00": "Base comuna (peces de la 00 i apèndixs comuns)",
    "01": "Socis i carnet digital",
    "04": "Tresoreria, part mínima",
    "05a": "Alta del mètode de pagament i mandats",
    "05b": "Cobraments",
    "06": "Llicències",
    "02": "Activitats (cursos i sortides)",
    "03": "Material",
    "09": "Marge, despeses, ajuts i facturació",
    "07": "Web pública",
    "08": "Dashboard",
    "10": "Missatges i xat per activitat",
    "11": "Departament d'Història i conferències",
    "12": "Idees noves",
    "13": "Botiga en línia",
}
# Ordre de construcció (decisions 024 i 060). Fase 3 = «després»; fase 4 = fora d'abast.
MODULE_ORDER = [
    "00",
    "01",
    "04",
    "05a",
    "05b",
    "06",
    "02",
    "03",
    "09",
    "07",
    "08",
    "10",
    "11",
    "12",
    "13",
]
MODULE_PHASE = dict(zip(MODULE_ORDER, [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 4], strict=True))

STATUS_MARKS = [
    ("feta_part", r"\*\*Feta en part\*\*|\b[Ff]eta en part\b|\*\*Feta per a la 00 i el 01\*\*"),
    ("validacio", r"[Ii]mplementada,? pendent de validació"),
    ("curs", r"\*\*En curs\*\*"),
    ("pendent", r"\*\*No començada"),
    ("feta", r"\*\*Feta\*\*"),
]
# Estat apuntat a docs/estat/ (decisió 089, D1): quatre estats i cap més. Si una tasca hi és,
# el seu estat mana sobre el que diu la fila del pla.
STATUS_DIR = "docs/estat/"
STATUS_FILE_STATES = {
    "feta": "feta",
    "en curs": "curs",
    "per fer": "pendent",
    "bloquejada": "pendent",
}


def status_file_state(state: str) -> str | None:
    """Estat de la pàgina per a l'estat d'una fila de docs/estat/; None si no s'entén.

    A més dels quatre estats del README, les sessions hi escriuen variants («implementada,
    pendent de validació», «feta, pendent de revisió», «feta en part»...): la pàgina ja té
    estats per a aquestes, i ignorar-les feia tornar la tasca a l'estat del pla («per fer»).
    """
    if state in STATUS_FILE_STATES:
        return STATUS_FILE_STATES[state]
    if state.startswith("feta en part"):
        return "feta_part"
    if state.startswith(("implementada", "feta,")):
        return "validacio"
    if state.startswith(("en curs", "esborrany")):
        return "curs"
    if state == "no cal":
        return "retirada"
    return None


BLOCKED_RE = re.compile(
    r"(bloquejad\w* per (?:la|el|les|els) "
    r"(?:P-|Q-|S-|junta|tresorer|banc|gestoria|secretaria|FECDAS|PaynoPain)(?:[^;.)]|\.(?=\d)){0,80}"
    r"|[Cc]ongelad\w*[^;.)]{0,80}"
    r"|no s'implementa\*?\*?\s*fins que[^.]{0,160})"
)
APPENDIX_OWNERS = {
    "preguntes-banc": "Banc",
    "preguntes-paynopain": "PaynoPain",
    "preguntes-tresorer": "Tresorer",
    "preguntes-junta": "Junta",
    "preguntes-gestoria": "Gestoria",
    "preguntes-fecdas": "FECDAS",
    "preguntes-secretaria": "Secretaria",
    "preguntes-informatica": "Informàtica",
    "preguntes-cursos-sortides": "Responsable de cursos i sortides",
    "preguntes-responsable": "Responsable del projecte (tu)",
}
CANONICAL_OWNERS = [
    ("junta", "Junta"),
    ("tresorer", "Tresorer"),
    ("secretaria", "Secretaria"),
    ("gestoria", "Gestoria"),
    ("assessor", "Assessor de protecció de dades"),
    ("banc", "Banc"),
    ("paynopain", "PaynoPain"),
    ("fecdas", "FECDAS"),
    ("informàtica", "Informàtica"),
    ("cursos i sortides", "Responsable de cursos i sortides"),
    ("responsable del projecte", "Responsable del projecte (tu)"),
    ("responsable", "Responsable del projecte (tu)"),
]
THIRD_PARTIES = [
    "PaynoPain",
    "proveïdor",
    "banc",
    "FECDAS",
    "federació",
    "Brevo",
    "gestoria",
    "Verifactu",
    "pain.008",
    "Norma 43",
    "Paylands",
]


# Marca simple d'ones i corall, només si el logotip del repositori no es pot llegir.
FALLBACK_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 47" fill="none" '
    b'stroke="#0a6583" stroke-width="2.5" stroke-linecap="round">'
    b'<path d="M4 12c6-5 12 5 18 0s12 5 18 0M4 21c6-5 12 5 18 0s12 5 18 0"/>'
    b'<path stroke="#b4470a" d="M22 44V30m0 4c-5-1-7-5-7-9m7 5c5-1 7-4 7-8"/></svg>'
)
FALLBACK_LOGO = "data:image/svg+xml;base64," + base64.b64encode(FALLBACK_SVG).decode()


class Repo:
    """Lectura d'una referència de Git, sense tocar l'arbre de treball."""

    def __init__(self, path: str, ref: str) -> None:
        self.path = path
        self.ref = ref

    def git(self, *args: str, binary: bool = False):
        result = subprocess.run(  # noqa: S603
            ["git", "-C", self.path, *args],  # noqa: S607
            capture_output=True,
            check=False,
        )
        return result.stdout if binary else result.stdout.decode("utf-8", "replace")

    def show(self, path: str) -> str:
        return self.git("show", f"{self.ref}:{path}")

    def show_bytes(self, path: str) -> bytes:
        return self.git("show", f"{self.ref}:{path}", binary=True)

    def ls(self, path: str, recursive: bool = False) -> list[str]:
        args = ["ls-tree", "--name-only"] + (["-r"] if recursive else []) + [self.ref, path]
        return [name for name in self.git(*args).split("\n") if name]


def cells(line: str) -> list[str]:
    """Cel·les d'una fila de taula Markdown; una barra dins de `codi` no separa."""
    out, cur, tick = [], "", False
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    for ch in text:
        if ch == "`":
            tick = not tick
        if ch == "|" and not tick:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def status_hits(text: str) -> list[tuple[int, str, str]]:
    """Marques d'estat d'una cel·la «Feta quan», en ordre; l'última és la vigent.

    No compten les que van darrere d'«Abans:» ni les de després d'«Historial:».
    """
    cut = len(text)
    match = re.search(r"Historial:", text)
    if match:
        cut = match.start()
    hits = []
    for key, pattern in STATUS_MARKS:
        for m in re.finditer(pattern, text[:cut]):
            before = text[max(0, m.start() - 30) : m.start()]
            if re.search(r"Abans[^.;]{0,20}$", before) or re.search(r"«\s*$", before):
                continue
            hits.append((m.start(), key, m.group(0)))
    hits.sort()
    return hits


def task_module(task_id: str) -> str:
    m = re.match(r"T-M(\d\d[ab]?)A?-", task_id)
    return m.group(1) if m and m.group(1) != "00" else "00"


def split_id(task_id: str) -> tuple[str, int]:
    m = re.match(r"(T-[A-Za-z0-9]+-)(\d+)[a-z]?$", task_id)
    return m.group(1), int(m.group(2))


def expand_ids(text: str, all_ids: list[str]) -> list[tuple[str, str]]:
    """Identificadors de tasca d'un text; «T-X-13 a T-X-21» s'expandeix amb les que existeixen."""
    found = []
    for m in re.finditer(rf"({TASK_ID})\s+a\s+(?:la\s+)?({TASK_ID})", text):
        prefix_a, first = split_id(m.group(1))
        prefix_b, last = split_id(m.group(2))
        if prefix_a == prefix_b:
            for tid in all_ids:
                prefix, number = split_id(tid)
                if prefix == prefix_a and first <= number <= last:
                    found.append((tid, "rang"))
    found += [(m.group(0), "directa") for m in re.finditer(TASK_ID, text)]
    seen, out = set(), []
    for tid, kind in found:
        if tid not in seen:
            seen.add(tid)
            out.append((tid, kind))
    return out


def canonical_owners(names) -> list[str]:
    """Normalitza els noms de responsable; el que no es reconeix es descarta."""
    out = []
    for name in names:
        low = name.lower()
        for key, label in CANONICAL_OWNERS:
            if key not in low or (key == "responsable" and "cursos" in low):
                continue
            if label not in out:
                out.append(label)
            if key in ("cursos i sortides", "responsable del projecte"):
                break
    return out


def count_criteria(text: str) -> int:
    """Criteris d'acceptació i punts de checklist citats (els rangs «a» compten sencers)."""
    total = 0
    range_re = r"CA-[\w]+?-?(\d+)(?:\.\w+)?\s+a\s+(?:CA-[\w]+?-?)?(\d+)"
    for m in re.finditer(range_re, text):
        first, last = int(m.group(1)), int(m.group(2))
        if 0 < last - first < 40:
            total += last - first + 1
    rest = re.sub(range_re, "", text)
    total += len(re.findall(r"\bCA-[\w.-]+", rest))
    total += len(re.findall(r"\b[A-H]\d{1,2}\b", rest))
    return total


# ----------------------------------------------------------------------------- planning.md


def parse_plan(plan: str, report: dict) -> tuple[list[dict], dict, dict, list[str]]:
    lines = plan.split("\n")
    n_lines = len(lines) - (1 if lines and lines[-1] == "" else 0)
    report["planning_lines"] = n_lines
    report["planning_last"] = lines[n_lines - 1][:160] if n_lines else ""
    report["files_read"].append(
        f"docs/planning.md ({n_lines} línies; llegida fins a la línia {n_lines}, l'última)"
    )

    header, header_cells, section = "", [], ""
    tasks, remission_rows = [], []
    for i, line in enumerate(lines, 1):
        if line.startswith(("## ", "# ")):
            section = line.lstrip("#").strip()
        if line.startswith("|") and "---" not in line and not re.match(r"\|\s*\**T-", line):
            header, header_cells = line, cells(line)
        m = re.match(rf"\|\s*\**({TASK_ID})\**\s*\|", line)
        if not m:
            continue
        row = cells(line)
        if "Depèn de" in header:
            needed_by = ""
            if "La necessiten" in header_cells and len(row) > 6:
                needed_by = row[6].split("**")[0].strip()
            tasks.append(
                {
                    "id": m.group(1),
                    "line": i,
                    "title": row[1],
                    "effort": row[2],
                    "files": row[3],
                    "depRaw": row[4],
                    "feta": " | ".join(row[5:]),
                    "neces": needed_by,
                    "sec": section,
                    "mod": task_module(m.group(1)),
                }
            )
        else:
            remission_rows.append(
                {"id": m.group(1), "line": i, "text": " | ".join(row[1:]), "sec": section}
            )
    all_ids = [t["id"] for t in tasks]
    id_set = set(all_ids)

    notes = collections.defaultdict(list)
    extra_deps = collections.defaultdict(list)
    for row in remission_rows:
        notes[row["id"]].append({"line": row["line"], "sec": row["sec"], "text": row["text"]})
    reading_start = next(
        (
            i
            for i, ln in enumerate(lines, 1)
            if ln.startswith("## Lectura de les tasques substituïdes")
        ),
        None,
    )
    for i, line in enumerate(lines, 1):
        if reading_start and i > reading_start and line.startswith("| T-"):
            row = cells(line)
            if len(row) != 3:
                continue
            text = row[1]
            for target, _kind in expand_ids(row[0], all_ids):
                if not any(n["line"] == i for n in notes[target]):
                    notes[target].append(
                        {
                            "line": i,
                            "sec": "Lectura de les tasques substituïdes",
                            "text": f"{text} · Font: {row[2]}",
                        }
                    )
                if re.search(r"[Dd]ep[eè]n\w* de|Després de", text):
                    for dep, _k in expand_ids(text, all_ids):
                        if dep != target and dep in id_set:
                            extra_deps[target].append(
                                {"id": dep, "line": i, "src": "Lectura: " + text[:120]}
                            )
        if line.startswith("**Tasques afectades:**"):
            for m in re.finditer(rf"({TASK_ID}) \(([^)]*)\)", line):
                notes[m.group(1)].append({"line": i, "sec": section, "text": m.group(2)})

    module_status = {}
    for line in lines:
        if line.startswith('<a id="primer-modul"'):
            break
        m = re.match(r"\| \*\*(\w+)\*\* \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \|", line)
        if m:
            module_status[m.group(1)] = {
                "estat": re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", m.group(6))
            }

    appendix_questions, owner = [], None
    for i, line in enumerate(lines, 1):
        m = re.match(r'<a id="(preguntes-[a-z-]+)"></a>', line)
        if m:
            owner = APPENDIX_OWNERS.get(m.group(1))
        if line.startswith('<a id="ordre-del-dia-junta"'):
            owner = None
        if owner and line.startswith("| ") and not line.startswith("| ID") and "---" not in line:
            row = cells(line)
            if len(row) >= 3:
                appendix_questions.append(
                    {"line": i, "owner": owner, "ids": row[0], "q": row[1], "blocks": row[2]}
                )
    return (
        tasks,
        {"notes": notes, "extra_deps": extra_deps, "appq": appendix_questions},
        module_status,
        all_ids,
    )


# ----------------------------------------------------------------------------- git i CI


class History:
    def __init__(self, repo: Repo, runs: list[dict]) -> None:
        self.repo = repo
        self.commits = {}
        for line in repo.git("log", repo.ref, "--format=%H|%h|%ci|%s").strip().split("\n"):
            if line.count("|") >= 3:
                full, short, date, subject = line.split("|", 3)
                self.commits[full] = {"H": full, "h": short, "d": date, "s": subject}
        self.runs = sorted(runs, key=lambda r: r["n"])
        self._ancestors = {}

    def find(self, short: str) -> dict | None:
        return next((c for full, c in self.commits.items() if full.startswith(short)), None)

    def find_pr(self, reference: str) -> dict | None:
        """El commit d'una PR fusionada per aixafament: el títol acaba amb «(#N)»."""
        m = re.search(r"#(\d+)", reference or "")
        if not m:
            return None
        tail = f"(#{m.group(1)})"
        return next((c for c in self.commits.values() if c["s"].endswith(tail)), None)

    def ancestors(self, sha: str) -> set[str]:
        if sha not in self._ancestors:
            self._ancestors[sha] = set(self.repo.git("rev-list", sha).split())
        return self._ancestors[sha]

    @staticmethod
    def _brief(run: dict) -> dict:
        return {"n": run["n"], "ev": run["ev"], "c": run["c"], "sha": run["sha"][:7], "t": run["t"]}

    def ci_for(self, sha: str) -> dict:
        """Execucions sobre el commit; si no n'hi ha, la primera que l'inclou; i l'última."""
        last = next((r for r in reversed(self.runs) if sha in self.ancestors(r["sha"])), None)
        direct = [r for r in self.runs if r["sha"] == sha]
        if direct:
            kind, shown = "directa", direct
        else:
            first = next((r for r in self.runs if sha in self.ancestors(r["sha"])), None)
            kind = "inclosa" if first else "cap"
            shown = [r for r in self.runs if first and r["sha"] == first["sha"]]
        return {
            "kind": kind,
            "runs": [self._brief(r) for r in shown],
            "last": self._brief(last) if last else None,
            "commit": sha[:7],
        }


def load_runs(path: str | None) -> list[dict]:
    """Execucions del CI en JSON Lines: una per línia, amb n, sha, ev, c i t."""
    if not path or not os.path.exists(path):
        return []
    runs = []
    with open(path, encoding="utf-8") as handle:
        text = handle.read().strip()
    if text.startswith("["):
        return json.loads(text)
    for line in text.split("\n"):
        if line.strip():
            runs.append(json.loads(line))
    return runs


# ----------------------------------------------------------------------------- altres fonts


def parse_diary(repo: Repo, report: dict) -> tuple[dict, dict]:
    index = collections.defaultdict(list)
    for line in repo.show("docs/diari-de-construccio/README.md").split("\n"):
        m = re.match(r"\| \[(T-[^\]]+)\]\(([^)]+)\) \|", line)
        if m:
            row = cells(line)
            index[m.group(1)].append(
                {
                    "title": row[1],
                    "date": row[2],
                    "commit": row[3],
                    "tests": row[4],
                    "ci": row[5] if len(row) > 5 else "",
                }
            )
    entries = {}
    for path in repo.ls("docs/diari-de-construccio/"):
        name = os.path.basename(path)
        if not name.endswith(".md") or name in ("README.md", "_plantilla.md"):
            continue
        m = re.search(r"\*\*Estat:?\s*([^*]+)\*\*", repo.show(path))
        entries[name[:-3]] = {"file": path, "estat": m.group(1).strip() if m else ""}
    report["files_read"].append("docs/diari-de-construccio/README.md (índex)")
    report["files_read"].append(f"docs/diari-de-construccio/: {len(entries)} entrades")
    return index, entries


def parse_status_files(repo: Repo, report: dict) -> dict:
    """Files de docs/estat/<mòdul>.md: tasca, estat, data, PR i bloqueig o nota."""
    entries = {}
    for path in sorted(repo.ls(STATUS_DIR)):
        if not path.endswith(".md") or os.path.basename(path) == "README.md":
            continue
        count = 0
        for number, line in enumerate(repo.show(path).split("\n"), 1):
            m = re.match(rf"\|\s*\**({TASK_ID})\b", line)
            if not m:
                continue
            row = cells(line)
            state = row[1].strip("* ").lower() if len(row) > 1 else ""
            if len(row) < 4 or status_file_state(state) is None:
                report["files_missing"].append(
                    f"{path}:{number}: fila no vàlida (calen tasca, estat, data, PR i nota; "
                    "estats: per fer, en curs, feta, bloquejada)."
                )
                continue
            entries[m.group(1)] = {
                "state": state,
                "date": row[2],
                "pr": row[3],
                "note": row[4] if len(row) > 4 else "",
                "src": f"{path}:{number}",
            }
            count += 1
        report["files_read"].append(f"{path} ({count} tasques)")
    return entries


def diary_status(title: str) -> str | None:
    low = title.lower()
    if "feta en part" in low or re.search(r"\ben part\b", low):
        return "feta_part"
    if "implementada, pendent de validació" in low:
        return "validacio"
    if re.search(r"\bfeta\b", low):
        return "feta"
    return None


def parse_pending(repo: Repo, report: dict) -> tuple[dict, list[dict]]:
    text = repo.show("docs/decisions/pendents.md")
    report["files_read"].append("docs/decisions/pendents.md")
    pending, batch, section = {}, [], ""
    for i, line in enumerate(text.split("\n"), 1):
        if line.startswith("## "):
            section = line[3:].strip()
        m = re.match(r"\| (P-\d+|Q-\d+ / S-M01-16) \|", line)
        if m and section in ("Oberts", "Resolts"):
            row = cells(line)
            pid = m.group(1).split(" ")[0]
            item = pending.setdefault(
                pid, {"id": pid, "tema": row[1], "open": None, "resolved": None}
            )
            if section == "Oberts":
                item["open"] = {"line": i, "text": " | ".join(row[2:])}
            else:
                item["resolved"] = {
                    "line": i,
                    "text": row[2],
                    "date": row[3] if len(row) > 3 else "",
                    "dec": row[4] if len(row) > 4 else "",
                }
        is_batch = section.startswith("Preguntes de la tanda") and line.startswith("| ")
        if is_batch and "---" not in line and not line.startswith("| Responsable | Pregunta"):
            row = cells(line)
            if len(row) >= 4:
                batch.append(
                    {
                        "n": len(batch) + 1,
                        "line": i,
                        "resp": row[0],
                        "q": row[1],
                        "opts": row[2],
                        "task": row[3],
                        "sec": section,
                    }
                )
    return pending, batch


def parse_external(repo: Repo, report: dict) -> list[dict]:
    text = repo.show("docs/preguntes-externes.md")
    report["files_read"].append("docs/preguntes-externes.md")
    sections, current = [], None
    for i, line in enumerate(text.split("\n"), 1):
        m = re.match(r"## (\d+)\. (.+)", line)
        if m:
            current = {"owner": m.group(2).strip(), "line": i, "ids": set(), "estat": ""}
            sections.append(current)
        elif current:
            current["ids"].update(re.findall(r"\b(P-\d+|S-M\w+-\d+|Q-\d+|RN-T\d+)\b", line))
            if line.startswith("**Estat"):
                current["estat"] = line
    for item in sections:
        item["ids"] = sorted(item["ids"])
    return sections


def parse_decisions(repo: Repo, report: dict, all_ids: list[str]) -> list[dict]:
    readme = {}
    for line in repo.show("docs/decisions/README.md").split("\n"):
        m = re.match(r"\| \[(\d{3})\]\([^)]+\) \| (.+?) \| (.+?) \|\s*$", line)
        if m:
            readme[m.group(1)] = {"estat": m.group(3)}
    decisions = []
    id_set = set(all_ids)
    for path in sorted(p for p in repo.ls("docs/decisions/") if re.search(r"/\d{3}-", p)):
        text = repo.show(path)
        number = os.path.basename(path)[:3]
        title = re.search(r"^# (.+)$", text, re.M)
        date = re.search(r"\*\*Data:\*\*\s*(.+)", text)
        state = re.search(r"\*\*Estat:\*\*\s*(.+)", text)
        decisions.append(
            {
                "num": number,
                "file": path.replace("docs/", ""),
                "title": title.group(1) if title else "",
                "date": date.group(1).strip() if date else "no trobat",
                "estat": state.group(1).strip() if state else "no trobat",
                "readme": readme.get(number),
                "tasks": sorted(set(re.findall(TASK_ID, text)) & id_set, key=all_ids.index),
                "pend": sorted(set(re.findall(r"\bP-\d+\b", text))),
            }
        )
    numbers = [int(d["num"]) for d in decisions]
    if numbers:
        report["files_read"].append(
            f"docs/decisions/: {len(decisions)} decisions ({min(numbers):03d}–{max(numbers):03d})"
        )
        report["decisions_missing"] = [
            f"{n:03d}" for n in range(1, max(numbers) + 1) if n not in numbers
        ]
    else:
        report["decisions_missing"] = []
    report["files_read"].append("docs/decisions/README.md")
    return decisions


# ----------------------------------------------------------------------------- per tasca


def enrich_task(
    task: dict, plan_extra: dict, history: History, diary, all_ids: list[str], filed=None
) -> None:
    """`filed`: la fila de la tasca a docs/estat/, si n'hi ha (decisió 089, D1)."""
    index, entries = diary
    id_set = set(all_ids)
    feta = task["feta"]
    notes = plan_extra["notes"].get(task["id"], [])
    hits = status_hits(feta)
    position, status, quote = hits[-1] if hits else (None, "pendent", "")
    task.update(status=status, statusQuote=quote, phase=MODULE_PHASE[task["mod"]], notes=notes)
    if filed:
        task.update(
            planStatus=status,
            status=status_file_state(filed["state"]),
            statusQuote=f"«{filed['state']}» a {filed['src']}",
            statusFile=filed,
        )
        if filed["state"] == "bloquejada":
            task["blocked"] = {"quote": filed["note"] or "Bloquejada", "line": task["line"]}
    if quote.startswith("**Feta per a la"):
        task["statusNote"] = (
            "El pla diu literalment «Feta per a la 00 i el 01»: es mostra com a «feta en part»."
        )
    for note in notes:
        if note["text"].startswith("Retirada"):
            task["status"] = "retirada"
            task["statusQuote"] = f"Retirada (lectura, línia {note['line']})"
        if note["text"].startswith("Congelada"):
            task["blocked"] = {"quote": note["text"], "line": note["line"]}
        if re.search(r"fora del camí crític", note["text"]):
            task["offcrit"] = f"Fora del camí crític, segons el pla (línia {note['line']})."
    m = BLOCKED_RE.search(feta)
    if m and "blocked" not in task:
        task["blocked"] = {"quote": m.group(1), "line": task["line"]}

    segment = feta[position:] if position is not None else ""
    task["criteria"] = feta[: hits[0][0]] if hits else feta
    date = re.search(r"(\d{2}/\d{2}/\d{4})", segment)
    if not date and hits:
        date = re.search(r"(\d{2}/\d{2}/\d{4})", feta[hits[0][0] :])
    task["date"] = date.group(1) if date else ""
    if filed and re.fullmatch(r"\d{2}/\d{2}/\d{4}", filed["date"]):
        task["date"] = filed["date"]

    commits = []
    for source in (segment, feta if hits else ""):
        for m in re.finditer(r"(?<![0-9a-f])([0-9a-f]{7,40})(?![0-9a-f])", source):
            commit = history.find(m.group(1))
            if commit and commit not in commits:
                commits.append(commit)
        if commits:
            break
    merged = history.find_pr(filed["pr"]) if filed else None
    if merged:
        commits = [merged] + [c for c in commits if c is not merged]
    task["commits"] = [{"h": c["h"], "d": c["d"][:16], "s": c["s"]} for c in commits[:6]]
    task["commitsAll"] = len(commits)
    if commits:
        task["ciGithub"] = history.ci_for(commits[0]["H"])

    declared = []
    ci_re = (
        r"(\*\*CI[^*]{0,80}\*\*[^.;]{0,140}"
        r"|CI (?:verd|vermell|de referència|\[A comprovar\]|: no comprovat|: pendent)[^.;]{0,140}"
        r"|CI \[A comprovar\])"
    )
    for m in re.finditer(ci_re, segment):
        if m.group(1).strip() not in declared:
            declared.append(m.group(1).strip())
    if merged and filed["state"] == "feta":
        declared.append("CI verd: la PR és a `master`, que està protegida (decisió 089)")
    task["ciDeclared"] = declared[-4:]

    open_items = []
    current = re.split(r"Historial:|\bAbans:", segment)[0]
    for label in (r"No tanca[^*]*", r"Queda[^*]*", r"Pendent:?"):
        pattern = r"\*\*(" + label + r")\*\*\s*(.{0,900}?)(?=\*\*[A-ZÀ-Ú]|$)"
        for m in re.finditer(pattern, current, re.S):
            open_items.append(m.group(1).strip(" :") + ": " + m.group(2).strip())
        if open_items:
            break
    if (
        filed
        and filed["state"] != "feta"
        and not filed["note"].startswith(("—", "(pla,"))
        and filed["note"]
        and not open_items
    ):
        open_items.append("Nota: " + filed["note"])
    task["noTanca"] = open_items[-3:]

    rows = index.get(task["id"], [])
    task["diari"] = rows[-1] if rows else None
    task["diariCount"] = len(rows)
    task["diariEntry"] = entries.get(task["id"])
    conflicts = []
    if rows:
        other = diary_status(rows[-1]["title"])
        if filed and task["status"] == "curs":  # el traspàs del 13/11 hi va posar «en curs»
            other = {"feta_part": "curs", "validacio": "curs"}.get(other, other)
        if other and other != task["status"]:
            conflicts.append(
                {
                    "kind": "estat",
                    "plan": task["status"],
                    "other": other,
                    "src": "Índex del diari de construcció: «" + rows[-1]["title"][:220] + "»",
                }
            )
    if task["status"] == "feta":
        said = " ".join(task["ciDeclared"] + ([rows[-1]["ci"]] if rows else []))
        if "verd" not in said and re.search(r"comprovar|no comprovat|pendent", said):
            conflicts.append(
                {
                    "kind": "ci",
                    "plan": "feta",
                    "other": "ci",
                    "src": "El CLAUDE.md demana el CI en verd per a «Feta»; "
                    "el pla o el diari diuen: «" + said[:240] + "»",
                }
            )
    task["conflicts"] = conflicts

    deps = [
        {"id": dep, "kind": kind, "src": "Depèn de"}
        for dep, kind in expand_ids(task["depRaw"], all_ids)
    ]
    for extra in plan_extra["extra_deps"].get(task["id"], []):
        if extra["id"] not in [d["id"] for d in deps]:
            deps.append(
                {
                    "id": extra["id"],
                    "kind": "lectura",
                    "src": f"{extra['src']} (línia {extra['line']})",
                }
            )
    task["deps"] = [d for d in deps if d["id"] in id_set or d["kind"] == "directa"]

    everything = " ".join([task["title"], task["depRaw"], feta] + [n["text"] for n in notes])
    task["decisions"] = sorted(
        set(re.findall(r"decisions/(\d{3})-", everything))
        | set(re.findall(r"\*\*(\d{3}) \(", everything))
        | set(re.findall(r"\[(\d{3})\]\(", everything))
    )
    task["pend"] = sorted(set(re.findall(r"\bP-\d+\b", everything)), key=lambda p: int(p[2:]))
    task["qrefs"] = sorted(set(re.findall(r"\b(?:Q-\d+|S-M\w+-\d+|S-AJ-\d+|R2-\d+)\b", everything)))


def estimate_costs(tasks: list[dict], report: dict) -> None:
    """Puntuació relativa i visible a la pàgina; la T-M01-05 és la referència «alt»."""
    for task in tasks:
        effort = task["effort"].strip()
        base = {"S": 1, "M": 2, "L": 4}.get(effort) if len(effort) == 1 else None
        if base is None:
            why = f"Sense mida al pla («{effort or 'buit'}»): no es pot justificar l'estimació."
            task["cost"] = {"level": "sense", "why": why}
            continue
        spec = " ".join([task["title"], task["criteria"], task["files"]])
        criteria = count_criteria(task["criteria"] + " " + task["title"])
        screens = (
            1 if re.search(r"migraci|migrations|pantall|vistes|plantilles|views", spec, re.I) else 0
        )
        third = sorted({w for w in THIRD_PARTIES if re.search(r"\b" + re.escape(w), spec)})
        score = (
            base + 0.5 * min(criteria, 8) + 0.5 * min(len(task["deps"]), 4) + screens + len(third)
        )
        task["cost"] = {
            "score": score,
            "base": base,
            "eff": effort,
            "nca": criteria,
            "nd": len(task["deps"]),
            "mig": screens,
            "third": third,
        }
    reference = next((t["cost"].get("score") for t in tasks if t["id"] == "T-M01-05"), None)
    report["cost_ref"] = reference
    for task in tasks:
        cost = task["cost"]
        if cost.get("level") == "sense":
            continue
        if reference is None:
            task["cost"] = {
                "level": "sense",
                "why": "No s'ha trobat la tasca de referència T-M01-05.",
            }
        elif cost["score"] >= reference:
            cost["level"] = "alt"
        else:
            cost["level"] = "mitja" if cost["score"] >= reference / 2 else "baix"


def link_everything(tasks, decisions, pending, batch, plan_extra, external, all_ids) -> list[dict]:
    id_set = set(all_ids)
    for decision in decisions:
        extra = [t["id"] for t in tasks if decision["num"] in t["decisions"]]
        decision["tasks"] = sorted(set(decision["tasks"]) | set(extra), key=all_ids.index)

    owner_of = collections.defaultdict(set)
    for question in plan_extra["appq"]:
        for pid in re.findall(r"\b(P-\d+|Q-\d+)\b", question["ids"]):
            source = f"planning.md:{question['line']} (apèndix de preguntes)"
            owner_of[pid].add((question["owner"], source))
    for section in external:
        for pid in section["ids"]:
            if pid.startswith("P-"):
                owner_of[pid].add((section["owner"], f"preguntes-externes.md:{section['line']}"))

    for pid, item in pending.items():
        open_text = (item["open"] or {}).get("text", "")
        text = open_text + " " + (item["resolved"] or {}).get("text", "")
        mentioned = [tid for tid, _k in expand_ids(text, all_ids) if tid in id_set]
        citing = [t["id"] for t in tasks if pid in t["pend"]]
        item["tasks"] = sorted(set(mentioned) | set(citing), key=all_ids.index)
        for m in re.finditer(r"\[A (?:validar|verificar)(?: amb)?:? ([^\]]{3,60})\]", open_text):
            source = f"pendents.md:{item['open']['line']} (marca [A validar/verificar])"
            owner_of[pid].add((m.group(1).strip().capitalize(), source))
        item["owners"] = sorted(owner_of.get(pid, []))
        item["ownersCanon"] = canonical_owners([name for name, _src in item["owners"]])
        item["state"] = "resolt" if item["resolved"] else "obert"
        item["both"] = bool(item["open"] and item["resolved"])
        cited = set(re.findall(r"(\d{3})-[a-z]", text))
        cited |= {d["num"] for d in decisions if pid in d["pend"]}
        item["decisions"] = sorted(cited)

    done = {t["id"]: t["status"] == "feta" for t in tasks}
    questions = []
    for pid, item in pending.items():
        if item["state"] == "obert":
            questions.append(
                {
                    "id": pid,
                    "q": item["tema"],
                    "owners": item["ownersCanon"],
                    "tasks": item["tasks"],
                    "src": f"pendents.md:{item['open']['line']}",
                }
            )
    for question in plan_extra["appq"]:
        if "~~" in question["q"] or "Respost" in question["q"]:
            continue
        linked = {t for t, _k in expand_ids(question["blocks"] + " " + question["q"], all_ids)}
        for ref in re.findall(r"\b(?:S-M\w+-\d+|S-AJ-\d+|Q-\d+)\b", question["ids"]):
            linked |= {t["id"] for t in tasks if ref in t["qrefs"]}
        questions.append(
            {
                "id": question["ids"],
                "q": question["q"],
                "owners": canonical_owners([question["owner"]]),
                "blocks": question["blocks"],
                "tasks": sorted(linked & id_set, key=all_ids.index),
                "src": f"planning.md:{question['line']}",
            }
        )
    for row in batch:
        questions.append(
            {
                "id": f"{row['sec']}, fila {row['n']}",
                "q": row["q"],
                "owners": canonical_owners([row["resp"]]),
                "blocks": row["task"],
                "tasks": [t for t, _k in expand_ids(row["task"], all_ids) if t in id_set],
                "src": f"pendents.md:{row['line']}",
            }
        )
    for question in questions:
        question["unblocks"] = [tid for tid in question["tasks"] if not done[tid]]
    for task in tasks:
        owners = {o for q in questions if task["id"] in q["tasks"] for o in q["owners"]}
        task["owners"] = sorted(owners)
    return questions


# ----------------------------------------------------------------------------- sortida


def logo_data_uri(repo: Repo, path: str, size: int = 160) -> str:
    """Logotip del repositori reduït i en línia; buit si no hi és o no hi ha Pillow."""
    raw = repo.show_bytes(path)
    if not raw:
        return ""
    try:
        from PIL import Image
    except ImportError:
        return ""
    image = Image.open(io.BytesIO(raw))
    image.thumbnail((size, size))
    buffer = io.BytesIO()
    image.save(buffer, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def encrypt_payload(plain: bytes, passphrase: str) -> dict:
    """AES-256-GCM amb una clau PBKDF2-HMAC-SHA256; el navegador la torna a derivar."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    salt, nonce = os.urandom(16), os.urandom(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=KDF_ITERATIONS)
    key = kdf.derive(passphrase.encode("utf-8"))
    sealed = AESGCM(key).encrypt(nonce, plain, None)

    def b64(value: bytes) -> str:
        return base64.b64encode(value).decode()

    return {"enc": 1, "kdf": "PBKDF2-SHA256", "it": KDF_ITERATIONS, "salt": b64(salt),
            "iv": b64(nonce), "ct": b64(sealed)}  # fmt: skip


def decrypt_payload(box: dict, passphrase: str) -> bytes:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=base64.b64decode(box["salt"]),
        iterations=box["it"],
    )
    key = kdf.derive(passphrase.encode("utf-8"))
    return AESGCM(key).decrypt(base64.b64decode(box["iv"]), base64.b64decode(box["ct"]), None)


def collect(repo: Repo, runs: list[dict]) -> dict:
    report = {"files_read": [], "files_missing": []}
    plan = repo.show("docs/planning.md")
    if not plan:
        sys.exit(f"No s'ha trobat docs/planning.md a la referència {repo.ref}.")
    tasks, plan_extra, module_status, all_ids = parse_plan(plan, report)
    history = History(repo, runs)
    head = repo.git("log", "-1", "--format=%H|%h|%ci|%s", repo.ref).strip().split("|", 3)
    report["head"] = {
        "branch": re.sub(r"^origin/", "", repo.ref),
        "h": head[1],
        "d": head[2],
        "s": head[3],
    }
    report["commits_on_branch"] = len(history.commits)

    diary = parse_diary(repo, report)
    pending, batch = parse_pending(repo, report)
    external = parse_external(repo, report)
    decisions = parse_decisions(repo, report, all_ids)
    round_two = [
        p
        for p in repo.ls("", recursive=True)
        if re.search(r"(?i)(ronda.?2|preguntes.?r2|/r2[-_.])", p)
    ]
    if not round_two:
        report["files_missing"].append(
            "Fitxer de preguntes de la ronda 2 (R2): no trobat al repositori."
        )

    filed = parse_status_files(repo, report)
    for task in tasks:
        enrich_task(task, plan_extra, history, diary, all_ids, filed.get(task["id"]))
    estimate_costs(tasks, report)
    questions = link_everything(tasks, decisions, pending, batch, plan_extra, external, all_ids)

    now = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Madrid"))
    data = {
        "report": report,
        "tasks": tasks,
        "decisions": decisions,
        "pend": list(pending.values()),
        "openq": questions,
        "tanda": batch,
        "ext": external,
        "modname": MODULE_NAMES,
        "phase": MODULE_PHASE,
        "modorder": MODULE_ORDER,
        "moduleStatus": module_status,
        "runs": len(runs),
        "generated": now.strftime("%d/%m/%Y %H:%M"),
        "generatedIso": now.isoformat(timespec="seconds"),
    }
    return data


def seal(payload: str, variable: str) -> str:
    """Xifra amb la contrasenya de la variable d'entorn i comprova que es desxifra igual."""
    passphrase = os.environ.get(variable, "")
    if len(passphrase) < MIN_PASSPHRASE:
        sys.exit(
            f"{variable} ha de tenir {MIN_PASSPHRASE} caràcters o més: "
            "no es publica res sense xifrar ni amb una contrasenya curta."
        )
    box = encrypt_payload(payload.encode("utf-8"), passphrase)
    if decrypt_payload(box, passphrase).decode("utf-8") != payload:
        sys.exit("La comprovació del xifratge ha fallat.")
    return json.dumps(box, separators=(",", ":"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--repo", default=".", help="camí del repositori (per defecte, l'actual)")
    parser.add_argument("--ref", default="HEAD", help="referència de Git que es llegeix")
    parser.add_argument("--runs", help="execucions del CI en JSON Lines (opcional)")
    parser.add_argument("--out", required=True, help="fitxer HTML de sortida")
    parser.add_argument(
        "--encrypt",
        action="store_true",
        help="xifra les dades amb la contrasenya de TIMELINE_PASSPHRASE",
    )
    args = parser.parse_args()

    repo = Repo(args.repo, args.ref)
    data = collect(repo, load_runs(args.runs))
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if args.encrypt:
        payload = seal(payload, "TIMELINE_PASSPHRASE")

    html = (HERE / "template.html").read_text(encoding="utf-8")
    light = logo_data_uri(repo, "assets/marca/CRIS_SenseFons.png") or FALLBACK_LOGO
    dark = logo_data_uri(repo, "assets/marca/CRIS_Blanc_per fons Negre (Blanc).png") or light
    html = html.replace("__LOGODARK__", dark).replace("__LOGO__", light)
    html = html.replace("__DATA__", payload.replace("</", "<\\/"))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    counts = collections.Counter(t["mod"] for t in data["tasks"])
    summary = ", ".join(f"{m}: {counts[m]}" for m in MODULE_ORDER if counts[m])
    mode = "xifrat" if args.encrypt else "sense xifrar"
    print(
        f"{out} ({mode}): {len(data['tasks'])} tasques ({summary}); "
        f"{len(data['decisions'])} decisions; {len(data['pend'])} pendents; "
        f"{data['runs']} execucions del CI."
    )


if __name__ == "__main__":
    main()
