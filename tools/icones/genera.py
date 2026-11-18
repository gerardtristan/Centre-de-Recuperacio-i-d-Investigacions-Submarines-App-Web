"""Genera static/img/icones.svg (sprite de <symbol>) a partir de la carpeta `icons/` del paquet
oficial lucide-static, amb només les icones de apps/core/icones.py (T-DX-58).

Ús: python -I tools/icones/genera.py <carpeta icons de lucide-static> <arrel del repositori>
Llegeix els SVG com a text: no executa res del paquet. Treu els atributs de presentació de l'arrel
(color, gruix i extrems del traç els posa el CSS de .icona) i manté els traçats tal com són."""

import re
import sys
from pathlib import Path

ICONS, ROOT = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(ROOT))
from apps.core.icones import LUCIDE_VERSION, NAMES  # noqa: E402

BODY = re.compile(r"<svg[^>]*>(.*)</svg>", re.S)
ALLOWED = re.compile(r"^\s*<(path|circle|rect|line|polyline|polygon|ellipse)\b[^<>]*/>\s*$")

symbols = []
for name in NAMES:
    inner = BODY.search((ICONS / f"{name}.svg").read_text(encoding="utf-8")).group(1)
    shapes = [line.strip() for line in inner.strip().splitlines() if line.strip()]
    if not all(ALLOWED.match(s) for s in shapes):  # només formes, cap script ni enllaç
        sys.exit(f"{name}: element no esperat a l'SVG: {shapes}")
    symbols.append(f'<symbol id="{name}" viewBox="0 0 24 24">{"".join(shapes)}</symbol>')

sprite = (
    f"<!-- Lucide v{LUCIDE_VERSION} (lucide.dev), ISC: static/img/LICENSE-lucide.txt -->\n"
    '<svg xmlns="http://www.w3.org/2000/svg">\n' + "\n".join(symbols) + "\n</svg>\n"
)
(ROOT / "static" / "img" / "icones.svg").write_text(sprite, encoding="utf-8", newline="\n")
print(f"{len(symbols)} icones")
