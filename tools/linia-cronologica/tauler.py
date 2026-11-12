"""Tauler de preguntes pendents: les dades de l'apartat protegit amb la segona contrasenya.

Parteix de les preguntes obertes que el generador ja ha llegit (pendents.md, l'apèndix de
preguntes del pla i les tandes) i hi afegeix:

- les opcions A a D i la recomanació de Claude de `docs/decisions/tauler-preguntes.yml`;
- les opcions de la columna «Opcions» de les tandes de pendents.md, quan porten «(a) ...; (b) ...»;
- les preguntes noves dels fils («noves» del mateix fitxer);
- quines ja tenen una resposta enviada (un issue obert amb la marca `tauler-id:`), que surten
  apart fins que Claude les incorpora i tanca l'issue.

No escriu res al repositori.
"""

from __future__ import annotations

import re

OPTIONS_FILE = "docs/decisions/tauler-preguntes.yml"
KEYS = ("A", "B", "C", "D")
MARKER_RE = re.compile(r"<!--\s*tauler-id:\s*(.+?)\s*-->")


def load_options(repo, report: dict) -> dict:
    """Llegeix el fitxer d'opcions; si no hi és o no es pot llegir, el tauler surt sense opcions."""
    text = repo.show(OPTIONS_FILE)
    if not text:
        report["files_missing"].append(f"{OPTIONS_FILE}: no trobat (el tauler surt sense opcions).")
        return {"opcions": {}, "noves": {}}
    try:
        import yaml
    except ImportError:
        report["files_missing"].append(f"{OPTIONS_FILE}: cal `pip install pyyaml` per llegir-lo.")
        return {"opcions": {}, "noves": {}}
    data = yaml.safe_load(text) or {}
    report["files_read"].append(OPTIONS_FILE)
    return {"opcions": data.get("opcions") or {}, "noves": data.get("noves") or {}}


def clean_options(entry: dict, where: str, problems: list[str]) -> dict | None:
    """Valida una entrada del fitxer; si no és vàlida, la pregunta surt sense opcions."""
    raw = entry.get("opcions") or {}
    options = [{"k": k, "t": str(raw[k]).strip()} for k in KEYS if raw.get(k)]
    extra = sorted(set(raw) - set(KEYS))
    if extra:
        problems.append(f"{where}: claus d'opció no vàlides ({', '.join(map(str, extra))}).")
    if len(options) < 2:
        problems.append(f"{where}: calen almenys dues opcions.")
        return None
    rec = str(entry.get("recomanada") or "").strip().upper()
    if rec not in [o["k"] for o in options]:
        problems.append(f"{where}: la recomanació «{rec}» no és cap de les opcions.")
        rec = ""
    return {
        "opts": options,
        "rec": rec,
        "why": str(entry.get("perque") or "").strip(),
        "punt": str(entry.get("punt") or "").strip(),
        "recDate": str(entry.get("data") or "").strip(),
    }


def tanda_options(text: str) -> dict | None:
    """«(a) deixar-ho; (b) ... (recomanació)» → opcions A, B... i la recomanada."""
    parts = re.split(r"\(([a-d])\)\s*", text)
    if len(parts) < 5:  # cal (a) i (b) com a mínim
        return None
    options, rec = [], ""
    for letter, body in zip(parts[1::2], parts[2::2], strict=False):
        body = body.strip().rstrip(";").strip()
        if re.search(r"\(recomana", body) or re.search(r"recomanació\)", body):
            rec = letter.upper()
            body = re.sub(r"\s*\((?:la )?recomana(?:ció|da)\)\s*:?\s*", ": ", body)
            body = re.sub(r"\s+", " ", body).strip(" :;")
        options.append({"k": letter.upper(), "t": body})
    return {"opts": options, "rec": rec, "why": "", "punt": "", "recDate": ""}


def parse_answers(issues: list[dict]) -> dict:
    """Issues oberts amb la marca → {clau de la pregunta: issue}."""
    answered = {}
    for issue in issues:
        m = MARKER_RE.search(issue.get("body") or "")
        if m:
            key = m.group(1).strip()
            answered.setdefault(key, {"n": issue.get("number"), "url": issue.get("html_url", "")})
    return answered


def short_key(question: dict) -> str:
    m = re.match(r"Preguntes de la tanda del (\d{2}/\d{2}/\d{4}).*, fila (\d+)$", question["id"])
    if m:
        return f"Tanda {m.group(1)} · {m.group(2)}"
    return question["id"]


def build(questions, pending, batch, tasks, options_file, answered, report) -> dict:
    status = {t["id"]: t for t in tasks}
    problems: list[str] = []
    batch_by_line = {row["line"]: row for row in batch}
    items, seen = [], {}

    for question in questions:
        key = short_key(question)
        same = seen.get(key)
        if same and re.fullmatch(r"P-\d+", key):  # la mateixa P a pendents.md i a l'apèndix
            owners = set(same["owners"] + question["owners"]) - {"Sense responsable"}
            same["owners"] = sorted(owners)
            same["tasks"] = list(dict.fromkeys(same["tasks"] + question["tasks"]))
            same["unblocks"] = list(dict.fromkeys(same["unblocks"] + question["unblocks"]))
            same["blocks"] = bool(same["unblocks"])
            continue
        if same:  # mateix identificador amb dos responsables a l'apèndix
            key = f"{key} · {', '.join(question['owners']) or 'sense responsable'}"
        item = pending.get(question["id"]) if question["id"].startswith("P-") else None
        detail, rec_team, estat = "", "", ""
        if item and item.get("open"):
            cols = item["open"]["text"].split(" | ")
            detail = cols[0] if cols else ""
            rec_team = cols[1] if len(cols) > 1 else ""
            estat = cols[-1] if len(cols) > 3 else ""
            if re.match(r"\**Resolt \(", estat):  # a «Oberts» però marcat com a resolt
                continue
        opts = None
        line = int(question["src"].split(":")[1]) if ":" in question["src"] else 0
        if question["src"].startswith("pendents.md") and line in batch_by_line:
            row = batch_by_line[line]
            opts = tanda_options(row["opts"])
            detail = row["q"]
            if not opts and row["opts"]:
                rec_team = row["opts"]
        entry = options_file["opcions"].get(question["id"]) or options_file["opcions"].get(key)
        if entry:
            opts = clean_options(entry, key, problems) or opts
        mods = sorted({status[t]["mod"] for t in question["tasks"] if t in status})
        items.append(
            {
                "key": key,
                "q": question["q"],
                "detail": detail,
                "recTeam": rec_team,
                "estat": estat,
                "owners": question["owners"] or ["Sense responsable"],
                "tasks": question["tasks"],
                "unblocks": question["unblocks"],
                "blocks": bool(question["unblocks"]),
                "mods": mods,
                "src": question["src"],
                "origin": "pendents" if question["src"].startswith("pendents") else "pla",
                **(opts or {"opts": [], "rec": "", "why": "", "punt": "", "recDate": ""}),
            }
        )
        seen[key] = items[-1]

    for fid, entry in (options_file["noves"] or {}).items():
        where = f"noves.{fid}"
        opts = clean_options(entry, where, problems) if entry.get("opcions") else None
        task_ids = [t for t in entry.get("tasques") or [] if t in status]
        open_tasks = [t for t in task_ids if status[t]["status"] not in ("feta", "retirada")]
        items.append(
            {
                "key": str(fid),
                "q": str(entry.get("pregunta") or "").strip() or "(sense text)",
                "detail": str(entry.get("context") or "").strip(),
                "recTeam": "",
                "estat": "",
                "owners": [str(entry.get("responsable") or "Responsable del projecte (tu)")],
                "tasks": task_ids,
                "unblocks": open_tasks if entry.get("bloqueja") else [],
                "blocks": bool(entry.get("bloqueja")),
                "mods": sorted({status[t]["mod"] for t in task_ids}),
                "src": f"{OPTIONS_FILE} (noves.{fid})",
                "origin": "fil",
                **(opts or {"opts": [], "rec": "", "why": "", "punt": "", "recDate": ""}),
            }
        )

    keys = {i["key"] for i in items} | {q["id"] for q in questions}
    for key in options_file["opcions"]:
        if key not in keys:
            problems.append(f"opcions.{key}: ja no és oberta a cap font (es pot esborrar).")

    # Primer les que aturen una tasca; després, les del responsable i les que tenen opcions.
    me = "Responsable del projecte (tu)"
    items.sort(key=lambda i: (not i["blocks"], me not in i["owners"], not i["opts"]))
    sent = [dict(i, issue=answered[i["key"]]) for i in items if i["key"] in answered]
    todo = [i for i in items if i["key"] not in answered]
    report["tauler"] = {
        "preguntes": len(todo),
        "ambOpcions": sum(1 for i in todo if i["opts"]),
        "enviades": len(sent),
        "avisos": problems,
    }
    return {"items": todo, "sent": sent, "problems": problems}
