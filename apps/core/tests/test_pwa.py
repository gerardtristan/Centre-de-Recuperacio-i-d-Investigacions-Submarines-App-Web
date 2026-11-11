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
