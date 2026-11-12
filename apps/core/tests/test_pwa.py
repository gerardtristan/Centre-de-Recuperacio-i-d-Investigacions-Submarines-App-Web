"""T-M01-21: web instal·lable (manifest, service worker) i carnet sense connexió (CA-M01-17).

Aquí es prova la part del servidor: el manifest i les icones, la ruta i les capçaleres del
service worker, que les rutes del fitxer coincideixen amb les de Django, que l'única pàgina
que guarda és el carnet, que la pàgina del carnet porta l'avís «pot no estar al dia» que la
còpia mostra i que ni el carnet ni l'administració es poden desar a la memòria cau HTTP. El
funcionament sense connexió dins d'un navegador es comprova a mà (diari de la T-M01-21).
"""

import json
import re
import struct
import zlib

import pytest
from django.conf import settings
from django.contrib.staticfiles import finders
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.core.views.pwa import SOURCE
from apps.members import cards
from apps.members.tests.test_cards import SYSTEM, account_for, paid_member

SW = SOURCE.read_text(encoding="utf-8")


def js_string(name):
    return re.search(rf"var {name} = '([^']*)';", SW).group(1)


def manifest():
    with open(finders.find("manifest.json"), encoding="utf-8") as source:
        return json.load(source)


def png_size(path):
    with open(path, "rb") as image:
        header = image.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    return "{}x{}".format(*struct.unpack(">II", header[16:24]))


# --- Manifest ---------------------------------------------------------------------------------


def test_manifest_and_icons():
    data = manifest()
    assert data["name"] == "C.R.I.S." and data["lang"] == "ca"
    assert data["start_url"] == data["scope"] == "/"
    assert data["display"] == "standalone"
    sizes = set()
    for icon in data["icons"]:
        assert icon["src"].startswith(settings.STATIC_URL)
        path = finders.find(icon["src"].removeprefix(settings.STATIC_URL))
        assert path and png_size(path) == icon["sizes"]
        sizes.add(icon["sizes"])
    # Mides que demanen els navegadors per instal·lar-la.
    assert {"192x192", "512x512"} <= sizes


def test_base_template_links_the_manifest_and_registers_the_worker(client):
    html = client.get(reverse("accounts:login")).content.decode()
    assert f'<link rel="manifest" href="{settings.STATIC_URL}manifest.json">' in html
    assert f'href="{settings.STATIC_URL}img/icones/cris-180.png"' in html
    assert finders.find("img/icones/cris-180.png")
    assert (
        f'<script src="{settings.STATIC_URL}js/pwa.js" '
        f'data-service-worker="{reverse("core:service_worker")}" defer></script>'
    ) in html


# --- Ruta i capçaleres del service worker -------------------------------------------------------


def test_service_worker_is_public_at_the_root_and_always_revalidated(client, db):
    response = client.get(reverse("core:service_worker"))
    assert reverse("core:service_worker") == "/service-worker.js"  # abast: tot el lloc
    assert response.status_code == 200
    assert response["Content-Type"] == "text/javascript; charset=utf-8"
    assert response["Cache-Control"] == "no-cache"
    assert response.content == SOURCE.read_bytes()


def test_service_worker_only_answers_get(client, db):
    assert client.post(reverse("core:service_worker")).status_code == 405


# --- Què guarda el service worker ----------------------------------------------------------------


def test_worker_paths_match_django():
    assert js_string("CARNET") == reverse("members:card")
    assert js_string("INICI") == manifest()["start_url"]


def test_worker_only_stores_the_card_page_and_the_styles():
    # Una sola pàgina es desa (el carnet); la resta de memòria són els estils, sense dades.
    assert re.findall(r"\.put\(([^,]+),", SW) == ["CARNET"]
    assert re.findall(r"\.addAll\(([^)]+)\)", SW) == ["ESTILS"]
    for path in re.search(r"var ESTILS = \[([^\]]*)\]", SW).group(1).split(","):
        path = path.strip().strip("'")
        assert path.startswith(settings.STATIC_URL) and finders.find(
            path.removeprefix(settings.STATIC_URL)
        )
    assert f"/{settings.ADMIN_URL_PATH}/" not in SW


@pytest.mark.parametrize(
    "name",
    [
        "accounts:login",
        "accounts:login_totp",
        "accounts:logout",
        "administration:login",
        "administration:login_totp",
        "administration:logout",
    ],
)
def test_entering_or_leaving_either_area_wipes_the_card_copy(name):
    pattern = re.search(r"var ENTRAR_O_SORTIR = /(.+)/;", SW).group(1).replace("\\/", "/")
    assert re.search(pattern, reverse(name))


def test_worker_never_stores_a_copy_without_the_offline_notice():
    assert "if (copia === html) return esborraCarnet();" in SW


# --- Pàgina del carnet -------------------------------------------------------------------------


@pytest.mark.django_db
def test_card_page_carries_the_hidden_offline_notice(login_as):
    member = paid_member()
    cards.issue_card(member, by=SYSTEM)
    response = login_as(account_for(member), AREA_PERSONAL).get(reverse("members:card"))
    html = response.content.decode()
    assert js_string("AVIS_AMAGAT") in html  # la marca exacta que el service worker canvia
    assert "Sense connexió: aquesta còpia del carnet pot no estar al dia." in html
    assert re.search(r'Comprovat per última vegada: <time datetime="[^"]+">\d\d/\d\d/\d{4}', html)
    # Decisió 081, punt 15: no es presenta com una comprovació en temps real, diu quant dura i
    # porta el «vàlid fins al» que el service worker fa servir per no allargar la vigència.
    assert "No és una comprovació en temps real de l'estat del soci." in html
    assert "es mostra com a màxim 30 dies després d'aquesta comprovació" in html
    validity = cards.validity(cards.load_member(member.pk), cards.active_card(member), None)
    assert f'data-valid-fins="{validity.until:%Y-%m-%d}" data-sense-connexio hidden' in html
    # El navegador no la desa a la memòria cau HTTP: només en queda la còpia del service worker.
    assert "no-store" in response["Cache-Control"] and "private" in response["Cache-Control"]


def test_admin_pages_are_never_stored(login_as, admin_account):
    response = login_as(admin_account, AREA_ADMIN).get(reverse("administration:home"))
    assert response.status_code == 200
    assert "no-store" in response["Cache-Control"]


def test_worker_also_stores_the_fonts_of_the_styles():
    """079, A-28 (RN-M01-96; T-M01-45): sense connexió, el carnet es veu amb la lletra correcta.
    Totes les fonts de fonts.css són a la llista d'estils, i res més que no sigui un estil."""
    css = (settings.BASE_DIR / "static" / "css" / "fonts.css").read_text(encoding="utf-8")
    fonts = {
        f"{settings.STATIC_URL}fonts/{name}"
        for name in re.findall(r'url\("\.\./fonts/([^"]+)"\)', css)
    }
    stored = {
        p.strip().strip("'")
        for p in re.search(r"var ESTILS = \[([^\]]*)\]", SW).group(1).split(",")
    }
    assert len(fonts) == 7 and fonts <= stored
    assert all(p.endswith((".css", ".js", ".woff2")) for p in stored)


# --- Icona adaptable (079, A-28; T-M01-45) ----------------------------------------------------


def png_pixels(path):
    """RGBA de 8 bits sense entrellaçar, com les icones de static/img/icones/."""
    data = open(path, "rb").read()
    pos, idat = 8, b""
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        kind, body = data[pos + 4 : pos + 8], data[pos + 8 : pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, colour, _, _, interlace = struct.unpack(">IIBBBBB", body)
            assert (depth, colour, interlace) == (8, 6, 0)
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    raw, stride, rows, prev = zlib.decompress(idat), width * 4, [], bytearray(width * 4)
    for y in range(height):
        kind, line = (
            raw[y * (stride + 1)],
            bytearray(raw[y * (stride + 1) + 1 : (y + 1) * (stride + 1)]),
        )
        for x in range(stride):
            a, b = (line[x - 4] if x >= 4 else 0), prev[x]
            c = prev[x - 4] if x >= 4 else 0
            p = a + b - c
            predictor = {
                0: 0,
                1: a,
                2: b,
                3: (a + b) // 2,
                4: min((abs(p - a), 0, a), (abs(p - b), 1, b), (abs(p - c), 2, c))[2],
            }[kind]
            line[x] = (line[x] + predictor) & 255
        rows.append(line)
        prev = line
    return width, height, rows


def test_manifest_declares_a_maskable_icon_that_fits_the_safe_zone():
    """La icona adaptable reaprofita les icones que ja hi ha (cap art nou): fons blanc opac fins
    a les vores i el dibuix dins la zona segura (cercle del 80 % del costat)."""
    maskable = {i["sizes"]: i for i in manifest()["icons"] if i["purpose"] == "maskable"}
    assert set(maskable) == {"192x192", "512x512"}
    path = finders.find(maskable["192x192"]["src"].removeprefix(settings.STATIC_URL))
    width, height, rows = png_pixels(path)
    centre, safe = (width - 1) / 2, 0.40 * width
    for y, row in enumerate(rows):
        for x in range(width):
            r, g, b, alpha = row[x * 4 : x * 4 + 4]
            assert alpha == 255  # cap transparència: la màscara no deixa forats
            if min(r, g, b) < 235:  # dibuix (no el fons blanc)
                assert ((x - centre) ** 2 + (y - centre) ** 2) ** 0.5 <= safe, (x, y)
