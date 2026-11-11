"""RGPD al navegador (T-M01-22; P-M01-F): «Les meves dades» del perfil (preparar i descarregar el
fitxer) i les sol·licituds d'esborrat a l'administració (llista, detall, rebuig i aprovació amb
reautenticació). Cada pantalla es desa a 1280, 390 i 320 px (clar i fosc) i es comprova que a
320 px no es desplaça de costat. Els formularis s'envien només amb el teclat.
"""

import json
import time
from pathlib import Path

import pyotp
import pytest
from django.conf import settings
from django.core.files.storage import storages
from playwright.sync_api import expect

from apps.core import erasure
from apps.core.models import ErasureRequest, Person, PrivateFile
from apps.members.models import Member
from conftest import PASSWORD

from .conftest import TOTP_KEY, login_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH


@pytest.fixture
def private_files(transactional_db):
    """Els fitxers privats tenen la clau en UUID: la neteja de les e2e (files noves amb clau
    entera) no els veu. S'esborren aquí, abans, amb el seu contingut."""
    yield
    for file in PrivateFile.objects.all():
        storages["private"].delete(file.storage_key)
    PrivateFile.objects.all().delete()


def login_personal(page, base_url, account):
    page.goto(f"{base_url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page.get_by_role("button", name="Sortir")).to_be_visible()


def test_member_prepares_and_downloads_their_data(
    page, live_server, builder, member, review, private_files, page_checks
):
    page_checks.expect_download("/fitxers/local/")
    account = builder.personal(member.person)
    login_personal(page, live_server.url, account)
    page.goto(f"{live_server.url}/socis/perfil/")
    expect(page.get_by_role("heading", name="Les meves dades")).to_be_visible()
    review("perfil-sense-fitxer")

    # Només amb el teclat: el botó i Intro.
    page.get_by_role("button", name="Prepara el fitxer amb les meves dades").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Hem preparat el fitxer amb les teves dades")).to_be_visible()
    link = page.get_by_role("link", name="Descarrega el fitxer amb les meves dades")
    expect(link).to_be_visible()
    review("perfil-amb-fitxer")

    link.focus()
    with page.expect_download() as download:
        page.keyboard.press("Enter")
    assert download.value.suggested_filename == "les-meves-dades-cris.json"
    data = json.loads(Path(download.value.path()).read_text(encoding="utf-8"))
    assert data["persona"]["nom"] == "Pere"
    assert data["socis"]["soci"]["numero_de_soci"] == member.member_number
    assert "token" not in json.dumps(data).lower()


def test_admin_rejects_and_approves_erasure_requests_with_the_keyboard(
    page, live_server, builder, member, texts, review, private_files
):
    """`texts` és el compte d'administrador (M11). Dues sol·licituds: una es rebutja amb motiu i
    l'altra s'aprova amb la casella, la contrasenya i el codi; primer amb un codi incorrecte."""
    erasure.request_erasure(member.person, by=builder.personal(member.person))
    other = builder.paid_member(
        "Laia",
        "Dorada Inventada",
        "laia.dorada@example.org",
        builder.supporter,
        privacy=True,
        membership_terms=True,
    )
    erasure.request_erasure(other.person, by=builder.personal(other.person))

    login_admin(page, live_server.url, texts.login)
    page.get_by_role("link", name="Sol·licituds RGPD").click()
    expect(page.get_by_role("heading", name="Sol·licituds RGPD")).to_be_visible()
    expect(page.get_by_role("heading", name="Pendents (2)")).to_be_visible()
    review("llista-pendents")

    # --- Rebutjar, només amb el teclat ---
    page.get_by_role("link", name="Obre la sol·licitud: Laia Dorada Inventada").click()
    expect(
        page.get_by_role("heading", name="Esborrat de dades: Laia Dorada Inventada")
    ).to_be_visible()
    review("detall-pendent")
    page.get_by_label("Motiu del rebuig").focus()
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Rebutja")).to_be_focused()
    page.keyboard.press("Enter")  # sense motiu
    expect(page.get_by_text("Aquest camp és obligatori")).to_be_visible()
    review("rebuig-sense-motiu")
    page.get_by_label("Motiu del rebuig").focus()
    page.keyboard.type("Ho ha demanat per error (prova inventada)")
    page.keyboard.press("Tab")
    page.keyboard.press("Enter")
    expect(page.get_by_text("Sol·licitud rebutjada.")).to_be_visible()
    review("rebutjada")
    assert Person.objects.get(pk=other.person.pk).status == Person.Status.ACTIVE

    # --- Aprovar, només amb el teclat ---
    page.goto(f"{live_server.url}/{ADMIN}/rgpd/")
    page.get_by_role("link", name="Obre la sol·licitud: Pere Prova Inventat").click()
    expect(page.get_by_text("passarà a «baixa» avui")).to_be_visible()
    page.get_by_label("Entenc que l'esborrat s'executa ara").focus()
    page.keyboard.press("Space")
    page.keyboard.press("Tab")
    expect(page.get_by_label("Contrasenya")).to_be_focused()
    page.keyboard.type(PASSWORD)
    page.keyboard.press("Tab")
    expect(page.get_by_label("Codi de l'aplicació d'autenticació")).to_be_focused()
    page.keyboard.type("000000")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Aprova i executa l'esborrat")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Codi incorrecte")).to_be_visible()
    review("codi-incorrecte")
    assert Person.objects.get(pk=member.person.pk).status == Person.Status.ACTIVE

    # La casella continua marcada; la contrasenya i el codi es tornen a escriure. El codi de
    # l'entrada ja s'ha fet servir: cal el de l'interval següent.
    page.get_by_label("Contrasenya").focus()
    page.keyboard.type(PASSWORD)
    page.keyboard.press("Tab")
    page.keyboard.type(pyotp.TOTP(TOTP_KEY).at(time.time() + 30))
    page.keyboard.press("Enter")
    expect(page.get_by_text("Esborrat executat")).to_be_visible()
    person = Person.objects.get(pk=member.person.pk)
    assert person.status == Person.Status.ANONYMISED
    expect(
        page.get_by_role("heading", name=f"Esborrat de dades: {person.anonymous_ref}")
    ).to_be_visible()
    expect(page.get_by_text("Pere Prova Inventat")).to_have_count(0)
    review("executada")
    assert Member.objects.get(pk=member.pk).status == Member.Status.LEFT
    assert ErasureRequest.objects.get(person=person).status == ErasureRequest.Status.EXECUTED

    page.goto(f"{live_server.url}/{ADMIN}/rgpd/")
    expect(page.get_by_role("heading", name="Pendents (0)")).to_be_visible()
    expect(page.get_by_text(person.anonymous_ref).first).to_be_visible()
    review("llista-resoltes")
