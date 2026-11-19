"""Genera l'esquema de funcionalitats a partir de `funcionalitats.json` i de `docs/estat/`.

1. Calcula l'estat de cada node amb les files de les seves tasques a `docs/estat/`:
   totes «feta» → feta; alguna «feta» → a mitges; cap → per fer (també si no en té cap).
   Les tasques de `no_compten` (validació del propietari, proves en un mòbil real…) no hi compten.
2. Desa l'estat calculat a `funcionalitats.json`.
3. Incrusta les dades i les fonts a `esquema.html` (un sol fitxer, sense servidor).
4. Fa `esquema.png` (A3 apaïsat a 300 ppp) amb Playwright, si no es passa `--sense-png`.

Ús, des de l'arrel del repositori: python docs/esquema-funcionalitats/genera.py [--sense-png]
"""

import base64
import datetime
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ARREL = AQUI.parents[1]
DADES = AQUI / "funcionalitats.json"
HTML = AQUI / "esquema.html"
PNG = AQUI / "esquema.png"
ESTATS = {"feta", "en curs", "per fer", "bloquejada"}
FONTS = [
    ("Barlow Condensed", 600, "barlow-condensed/BarlowCondensed-SemiBold.woff2"),
    ("Source Sans 3", 400, "source-sans-3/SourceSans3-Regular.ttf.woff2"),
    ("Source Sans 3", 600, "source-sans-3/SourceSans3-Semibold.ttf.woff2"),
]
AMPLADA_A3_300PPP = 4961


def estat_de_les_tasques():
    """{identificador: estat} de totes les files de `docs/estat/*.md` (format del seu README)."""
    estats = {}
    for fitxer in sorted((ARREL / "docs" / "estat").glob("*.md")):
        for linia in fitxer.read_text(encoding="utf-8").splitlines():
            cel = [c.strip() for c in linia.split("|")]
            if len(cel) > 3 and cel[2] in ESTATS and cel[1]:
                estats[cel[1].split()[0]] = cel[2]
    return estats


def calcula(node, estats):
    if node.get("tipus") in ("fora", "proposta"):
        return node["tipus"], []
    tasques = node.get("tasques", [])
    desconegudes = [t for t in tasques + node.get("no_compten", []) if t not in estats]
    if desconegudes:
        sys.exit(f"{node['id']}: tasques que no són a docs/estat/: {', '.join(desconegudes)}")
    pendents = [[t, estats[t]] for t in tasques if estats[t] != "feta"]
    if not tasques or len(pendents) == len(tasques):
        return "perfer", pendents
    return ("mitges" if pendents else "feta"), pendents


def comprova(dades):
    errors = []
    ids = [n["id"] for n in dades["nodes"]]
    if len(ids) != len(set(ids)):
        errors.append("hi ha identificadors de node repetits")
    blocs, moduls = {b["id"] for b in dades["blocs"]}, {m["id"] for m in dades["moduls"]}
    errors += [
        f"bloc o mòdul desconegut a {n['id']}"
        for n in dades["nodes"]
        if n["bloc"] not in blocs or n["modul"] not in moduls
    ]
    errors += [
        f"connexió amb un node que no existeix: {o} → {d}"
        for o, d, _ in dades["connexions"]
        if o not in ids or d not in ids
    ]
    if errors:
        sys.exit("\n".join(errors))


def desa_json(dades):
    """Un bloc, un mòdul i un node per línia, i quatre connexions per línia (diffs curts)."""
    linia = lambda x: json.dumps(x, ensure_ascii=False)  # noqa: E731
    parts = [
        f" {linia(k)}: {linia(v)}"
        for k, v in dades.items()
        if k not in ("blocs", "moduls", "nodes", "connexions")
    ]
    for clau in ("blocs", "moduls", "nodes"):
        parts.append(f' "{clau}": [\n' + ",\n".join(linia(x) for x in dades[clau]) + "\n ]")
    connexions = dades["connexions"]
    files = [
        ", ".join(linia(c) for c in connexions[i : i + 4]) for i in range(0, len(connexions), 4)
    ]
    parts.append(' "connexions": [\n' + ",\n".join(files) + "\n ]")
    DADES.write_text("{\n" + ",\n".join(parts) + "\n}\n", encoding="utf-8")


def font_css(familia, pes, ruta):
    dades = base64.b64encode((ARREL / "static" / "fonts" / ruta).read_bytes()).decode()
    return (
        f'@font-face{{font-family:"{familia}";font-weight:{pes};font-display:block;'
        f'src:url(data:font/woff2;base64,{dades}) format("woff2")}}'
    )


def substitueix(html, obertura, tancament, contingut):
    patro = re.escape(obertura) + ".*?" + re.escape(tancament)
    return re.sub(patro, lambda _: obertura + contingut + tancament, html, count=1, flags=re.S)


def incrusta(dades):
    html = HTML.read_text(encoding="utf-8")
    html = substitueix(html, '<style id="fonts">', "</style>", "".join(font_css(*f) for f in FONTS))
    json_html = json.dumps(dades, ensure_ascii=False).replace("</", "<\\/")
    html = substitueix(html, '<script type="application/json" id="dades">', "</script>", json_html)
    HTML.write_text(html, encoding="utf-8")


def imatge():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page()
        pagina.goto(HTML.as_uri() + "?imatge")
        pagina.wait_for_function("window.esquemaLlest === true")
        amplada, alcada = pagina.evaluate("[document.body.scrollWidth, document.body.scrollHeight]")
        escala = AMPLADA_A3_300PPP / amplada
        pagina = navegador.new_page(
            viewport={"width": amplada, "height": alcada}, device_scale_factor=escala
        )
        pagina.goto(HTML.as_uri() + "?imatge")
        pagina.wait_for_function("window.esquemaLlest === true")
        pagina.screenshot(path=str(PNG), full_page=True)
        navegador.close()


def main():
    dades = json.loads(DADES.read_text(encoding="utf-8"))
    comprova(dades)
    estats = estat_de_les_tasques()
    for node in dades["nodes"]:
        node["estat"], node["pendents"] = calcula(node, estats)
    dades["actualitzat"] = datetime.date.today().strftime("%d/%m/%Y")
    desa_json(dades)
    incrusta(dades)
    for bloc in dades["blocs"]:
        compten = [
            n
            for n in dades["nodes"]
            if n["bloc"] == bloc["id"] and n["estat"] not in ("fora", "proposta")
        ]
        fetes = sum(n["estat"] == "feta" for n in compten)
        mitges = sum(n["estat"] == "mitges" for n in compten)
        print(f"{bloc['nom']}: {fetes} de {len(compten)} fetes, {mitges} a mitges")
    if "--sense-png" not in sys.argv:
        imatge()
        print(f"Imatge: {PNG.relative_to(ARREL)}")


if __name__ == "__main__":
    main()
