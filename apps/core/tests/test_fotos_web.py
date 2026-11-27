"""T-M07-31 (decisió 107): les fotos del club a static/img/web passen la comprovació (sense EXIF
ni GPS, 1.600 px com a màxim i totes descrites a fotos.yml), i la comprovació detecta cada
problema."""

import importlib.util
import struct
from pathlib import Path

from django.conf import settings

_spec = importlib.util.spec_from_file_location(
    "comprova_fotos_web", Path(settings.BASE_DIR) / "tools" / "comprova_fotos_web.py"
)
eina = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eina)


def _segment(marca, cos):
    return bytes([0xFF, marca]) + struct.pack(">H", len(cos) + 2) + cos


def _jpeg(amplada=800, alcada=600, app1=None):
    sof = _segment(0xC0, bytes([8]) + struct.pack(">HH", alcada, amplada) + b"\x01\x01\x11\x00")
    extra = _segment(0xE1, app1) if app1 else b""
    app0 = _segment(0xE0, b"JFIF\x00\x01\x01")
    return b"\xff\xd8" + app0 + extra + sof + _segment(0xDA, b"\x00") + b"\xff\xd9"


ENTRADA = (
    "fotos:\n  - fitxer: {nom}\n    autor: C.R.I.S.\n    permis: «Prova»\n    persones: no\n"
    '    alt: "Una foto de prova."\n    origen: Prova\n'
)


def test_the_club_photos_in_the_repository_pass():
    assert eina.comprova(Path(settings.BASE_DIR) / "static" / "img" / "web") == []


def test_it_detects_exif_xmp_and_oversized_photos(tmp_path):
    (tmp_path / "a.jpg").write_bytes(_jpeg(app1=b"Exif\x00\x00GPS"))
    (tmp_path / "b.jpg").write_bytes(_jpeg(app1=b"http://ns.adobe.com/xap/1.0/"))
    (tmp_path / "c.jpg").write_bytes(_jpeg(amplada=2000))
    (tmp_path / "fotos.yml").write_text(
        "".join(ENTRADA.format(nom=n).replace("fotos:\n", "") for n in ("a.jpg", "b.jpg", "c.jpg")),
        encoding="utf-8",
    )
    errors = eina.comprova(tmp_path)
    assert "a.jpg: té EXIF" in errors
    assert "b.jpg: té XMP o altres metadades (APP1)" in errors
    assert "c.jpg: fa 2000 px pel costat llarg (màxim 1600)" in errors


def test_it_requires_every_photo_described_in_fotos_yml(tmp_path):
    (tmp_path / "bona.jpg").write_bytes(_jpeg())
    (tmp_path / "sola.jpg").write_bytes(_jpeg())
    (tmp_path / "fotos.yml").write_text(
        ENTRADA.format(nom="bona.jpg").replace('    alt: "Una foto de prova."\n', "")
        + ENTRADA.format(nom="falta.jpg").replace("fotos:\n", ""),
        encoding="utf-8",
    )
    assert eina.comprova(tmp_path) == [
        "sola.jpg: no és a fotos.yml",
        "fotos.yml: falta.jpg no existeix",
        "fotos.yml: a bona.jpg li falta «alt»",
    ]
