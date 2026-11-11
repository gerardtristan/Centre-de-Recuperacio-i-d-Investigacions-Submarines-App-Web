"""Comprova els recorreguts dels wireframes (T-M01-48; decisió 079, A-31: abast petit).

Falla (codi de sortida 1) i diu on, si:
- una àncora no existeix al seu wireframe (cap element amb aquell `id`) o el fitxer no hi és;
- un rol de l'enllaç no és cap dels del selector «veure com» del wireframe;
- una tasca o un codi de permís no surt a cap taula de `docs/planning.md`;
- un distintiu no és dels declarats, o «sense wireframe» porta un wireframe;
- un procés `### P-M01-…` del pla no té recorregut, o un recorregut no és cap procés del pla;
- `dades.js` (la còpia que llegeix `index.html`, perquè amb `file://` no es pot llegir un JSON)
  no coincideix amb `recorreguts.json`.

Ús: `python design/recorreguts/comprova.py [--write]`. Amb `--write` torna a generar `dades.js` a
partir de `recorreguts.json`, que és l'únic fitxer que s'edita. Sense dependències.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WIREFRAMES = ROOT / "design" / "wireframes"
PLAN = ROOT / "docs" / "planning.md"
DATA = HERE / "recorreguts.json"
SCRIPT = HERE / "dades.js"
NO_WIREFRAME = "sense-wireframe"
TASK = re.compile(r"T-[A-Za-z0-9]+-\d+[a-z]?")
PERMISSION = re.compile(r"[PMC]\d+[a-z]?")


def script_text(data) -> str:
    body = json.dumps(data, ensure_ascii=False, indent=2)
    return (
        "// Generat per comprova.py --write a partir de recorreguts.json. No l'editis a mà.\n"
        f"window.RECORREGUTS = {body};\n"
    )


def plan_codes(plan_text) -> set[str]:
    """Primera cel·la de cada fila de les taules del pla: tasques (T-M01-42) i permisos (P7)."""
    return set(re.findall(r"^\| ([A-Za-z0-9-]+) \|", plan_text, flags=re.MULTILINE))


def plan_processes(plan_text) -> set[str]:
    return set(re.findall(r"^### (P-M01-[A-Z]) ", plan_text, flags=re.MULTILINE))


def anchors(html) -> set[str]:
    return set(re.findall(r'\bid="([^"]+)"', html))


def roles(html) -> set[str]:
    select = re.search(r'<select id="veure-com">(.*?)</select>', html, flags=re.DOTALL)
    return set(re.findall(r'<option value="([^"]+)"', select.group(1))) if select else set()


def problems(data, *, plan_text, wireframes_dir) -> list[str]:
    found = []
    codes = plan_codes(plan_text)
    pages = {}

    def page(name):
        if name not in pages:
            path = wireframes_dir / name
            ok = Path(name).name == name and path.is_file()
            pages[name] = path.read_text(encoding="utf-8") if ok else None
        return pages[name]

    journeys = {journey["id"] for journey in data["recorreguts"]}
    processes = plan_processes(plan_text)
    found += [
        f"{code}: el procés del pla no té recorregut" for code in sorted(processes - journeys)
    ]
    found += [
        f"{code}: el recorregut no és cap procés del pla" for code in sorted(journeys - processes)
    ]
    for journey in data["recorreguts"]:
        for step in journey["passos"]:
            where = f"{journey['id']}, pas {step['pas']}"
            task = step["tasca"]
            if not TASK.fullmatch(task) or task not in codes:
                found.append(f"{where}: la tasca {task} no existeix al pla")
            for code in step["permisos"]:
                if not PERMISSION.fullmatch(code) or code not in codes:
                    found.append(f"{where}: el permís {code} no existeix a la matriu del pla")
            badge = step.get("distintiu")
            if badge and badge not in data["distintius"]:
                found.append(f"{where}: el distintiu «{badge}» no està declarat")
            if badge == NO_WIREFRAME and step["wireframes"]:
                found.append(f"{where}: «sense wireframe» amb un wireframe enllaçat")
            for ref in step["wireframes"]:
                target = f"{ref['fitxer']}#{ref['ancora']}"
                html = page(ref["fitxer"])
                if html is None:
                    found.append(f"{where}: el wireframe {ref['fitxer']} no existeix")
                elif ref["ancora"] not in anchors(html):
                    found.append(f"{where}: l'àncora {target} no existeix al wireframe")
                elif "rol" in ref and ref["rol"] not in roles(html):
                    found.append(f"{where}: el rol «{ref['rol']}» no és a {ref['fitxer']}")
    return found


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if "--write" in args:
        SCRIPT.write_text(script_text(data), encoding="utf-8", newline="\n")
    found = problems(data, plan_text=PLAN.read_text(encoding="utf-8"), wireframes_dir=WIREFRAMES)
    if not SCRIPT.is_file() or SCRIPT.read_text(encoding="utf-8") != script_text(data):
        found.append("dades.js no coincideix amb recorreguts.json: executa comprova.py --write")
    steps = sum(len(journey["passos"]) for journey in data["recorreguts"])
    for line in found:
        print(line)
    if not found:
        print(f"Recorreguts correctes: {len(data['recorreguts'])} recorreguts i {steps} passos.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
