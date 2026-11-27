"""Comprova les fotos de la web (decisió 107, T-M07-31): sense metadades, 1.600 px com a màxim
i totes descrites a fotos.yml.

    python tools/comprova_fotos_web.py [carpeta]   (per defecte, static/img/web)

Falla (sortida 1) si una foto té EXIF, GPS, XMP o IPTC, si el costat llarg passa de 1.600 px, si
no és a fotos.yml (o fotos.yml en cita una que no hi és) o si en falta un camp. Només llegeix els
bytes: no fa servir Pillow i no canvia res. Mira la carpeta, no les subcarpetes (cris1954/ té el
seu fotos.yml).
"""

import struct
import sys
from pathlib import Path

MAX_PX = 1600
CAMPS = ("autor", "permis", "persones", "alt", "origen")
FOTOS = (".jpg", ".jpeg", ".png")


def problemes_jpeg(data):
    if data[:2] != b"\xff\xd8":
        return ["no és un JPEG"]
    errors, i, mida = [], 2, None
    while i + 4 <= len(data) and data[i] == 0xFF:
        marca, llarg = data[i + 1], struct.unpack(">H", data[i + 2 : i + 4])[0]
        cos = data[i + 4 : i + 2 + llarg]
        if marca == 0xE1:  # APP1: EXIF (amb el GPS) o XMP
            exif = cos.startswith(b"Exif")
            errors.append("té EXIF" if exif else "té XMP o altres metadades (APP1)")
        elif marca == 0xED:  # APP13: IPTC
            errors.append("té IPTC (APP13)")
        elif 0xC0 <= marca <= 0xCF and marca not in (0xC4, 0xC8, 0xCC):  # SOFn: alçada i amplada
            mida = struct.unpack(">HH", cos[1:5])
        elif marca == 0xDA:  # comencen les dades de la imatge
            break
        i += 2 + llarg
    return errors + _mida(mida)


def problemes_png(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return ["no és un PNG"]
    errors, i, mida = [], 8, None
    while i + 8 <= len(data):
        llarg, tipus = struct.unpack(">I4s", data[i : i + 8])
        if tipus == b"IHDR":
            mida = struct.unpack(">II", data[i + 8 : i + 16])[::-1]
        elif tipus in (b"eXIf", b"tEXt", b"iTXt", b"zTXt"):
            errors.append(f"té metadades ({tipus.decode()})")
        elif tipus == b"IEND":
            break
        i += 12 + llarg
    return errors + _mida(mida)


def _mida(mida):
    if mida is None:
        return ["no se'n troba la mida"]
    return [f"fa {max(mida)} px pel costat llarg (màxim {MAX_PX})"] if max(mida) > MAX_PX else []


def llegeix_fotos_yml(path):
    """El YAML de fotos.yml: una llista `fotos:` de camps `clau: valor` d'una sola línia."""
    entrades = []
    for linia in path.read_text(encoding="utf-8").splitlines():
        if linia.startswith("  - fitxer:"):
            entrades.append({"fitxer": linia.split(":", 1)[1].strip()})
        elif linia.startswith("    ") and ":" in linia and entrades:
            clau, valor = linia.strip().split(":", 1)
            entrades[-1][clau] = valor.strip().strip('"')
    return entrades


def comprova(carpeta):
    carpeta = Path(carpeta)
    fitxers = {p.name for p in carpeta.iterdir() if p.suffix.lower() in FOTOS}
    yml = carpeta / "fotos.yml"
    entrades = llegeix_fotos_yml(yml) if yml.exists() else []
    errors = []
    if fitxers and not yml.exists():
        errors.append("fotos.yml: no hi és")
    citats = {e["fitxer"] for e in entrades}
    errors += [f"{nom}: no és a fotos.yml" for nom in sorted(fitxers - citats)]
    errors += [f"fotos.yml: {nom} no existeix" for nom in sorted(citats - fitxers)]
    for e in entrades:
        errors += [f"fotos.yml: a {e['fitxer']} li falta «{c}»" for c in CAMPS if not e.get(c)]
        if e.get("persones") not in (None, "sí", "no"):
            errors.append(f"fotos.yml: {e['fitxer']}: «persones» ha de ser sí o no")
    for nom in sorted(fitxers):
        data = (carpeta / nom).read_bytes()
        mira = problemes_png if nom.lower().endswith(".png") else problemes_jpeg
        errors += [f"{nom}: {p}" for p in mira(data)]
    return errors


if __name__ == "__main__":
    per_defecte = Path(__file__).resolve().parent.parent / "static" / "img" / "web"
    carpeta = sys.argv[1] if len(sys.argv) > 1 else per_defecte
    errors = comprova(carpeta)
    print("\n".join(errors) or "Totes les fotos són correctes.")
    sys.exit(1 if errors else 0)
