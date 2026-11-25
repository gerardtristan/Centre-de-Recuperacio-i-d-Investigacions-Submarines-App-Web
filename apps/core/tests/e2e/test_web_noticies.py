"""T-M07-08 (P-M07-B; CA-M07-01 per a notícies, RN-M07-05): un visitant veu les notícies
publicades i el detall d'una amb foto; l'esborrany no hi surt. Les notícies es fan amb el servei
(les pantalles de WP2 esperen el torn del nucli). Dades inventades."""

import datetime
import struct
import zlib

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from playwright.sync_api import expect

from apps.core.models import Setting
from apps.website import media, news

from .conftest import make_admin

pytestmark = pytest.mark.e2e


def _png(width=480, height=270) -> bytes:
    """Una foto inventada d'un sol color, PNG vàlid per al navegador."""

    def chunk(kind, data):
        crc = struct.pack(">I", zlib.crc32(kind + data))
        return struct.pack(">I", len(data)) + kind + data + crc

    rows = b"".join(bytes([0]) + bytes([30, 90, 140]) * width for _ in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    signature = bytes([137]) + b"PNG" + bytes([13, 10, 26, 10])
    body = chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")
    return signature + body


def test_visitor_reads_the_published_news(page, live_server, transactional_db, review):
    Setting.objects.filter(key="website.public_images_enabled").update(initial_value=True)
    editor = make_admin("web.prova", "administrator")
    photo = media.upload(
        SimpleUploadedFile("barca.png", _png()), actor=editor, alt_text="Una barca a les Medes",
        shows_people=False, author="Autora Inventada", licence_note="Cedida al club",
    )  # fmt: skip
    day = datetime.date(2026, 11, 20)
    item = news.save_news(
        None, actor=editor, title="Comença la temporada de sortides", slug="temporada",
        date=day, body="Primera sortida a les Medes.\n\nInscripcions obertes.", image=photo,
    )  # fmt: skip
    news.publish(item, actor=editor)
    news.save_news(
        None, actor=editor, title="Esborrany amagat", slug="amagat", date=day, body="No surt."
    )

    page.goto(f"{live_server.url}/noticies/")
    expect(page.get_by_role("heading", name="Notícies")).to_be_visible()
    expect(page.locator("main")).not_to_contain_text("Esborrany amagat")
    review("noticies-llista")
    page.get_by_role("link", name="Comença la temporada de sortides").click()
    expect(page.get_by_role("img", name="Una barca a les Medes")).to_be_visible()
    expect(page.get_by_text("Foto: Autora Inventada")).to_be_visible()
    review("noticies-detall")
