"""Enllaços de convidat al navegador (T-M00-02; spec 00, HU-02, CA-02.1 a CA-02.7): la pantalla
d'administració (generar, reenviar i revocar) i la pàgina del convidat (enllaç vàlid, pagat, no
vàlid, bloquejat i petició d'un enllaç nou). Cada pantalla es desa a 1280, 390 i 320 px (clar i
fosc) i es comprova que a 320 px no es desplaça de costat. Enviar l'enllaç des de l'administració
i demanar-ne un de nou es fan només amb el teclat. Només dades inventades.
"""

import re

import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.accounts import limits
from apps.core import audit, charges, guest_links
from apps.core.models import Charge, GuestLink, OutgoingEmail, Payment, Person

from .conftest import login_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH
EMAIL = "mar.convidada@example.org"
CONCEPT = "Curs Open Water (prova inventada)"


def guest_charge(admin):
    person = Person.objects.create(
        first_name="Mar", last_name="Convidada Inventada", origin="web", contact_email=EMAIL
    )
    department = charges.create_department("Cursos", by=admin)
    return charges.create_charge(
        person,
        kind=Charge.Kind.ENROLMENT,
        amount_cents=12000,
        concept=CONCEPT,
        origin="activities",
        department=department,
        by=admin,
    )


def last_token():
    body = OutgoingEmail.objects.filter(template=guest_links.EMAIL_TEMPLATE).latest("pk").body_text
    return re.search(r"/convidat/([\w-]+)/", body).group(1)


def test_admin_sends_the_link_and_the_guest_opens_it(page, live_server, texts, review):
    charge = guest_charge(texts)
    login_admin(page, live_server.url, texts.login)
    page.get_by_role("main").get_by_role("link", name="Enllaços de convidat").click()
    expect(page.get_by_role("heading", name="Enllaços de convidat")).to_be_visible()
    expect(page.get_by_role("rowheader", name="Mar Convidada Inventada")).to_be_visible()
    review("administracio-sense-enllac")

    # Només amb el teclat: el botó de la fila i Intro.
    page.get_by_role("button", name=re.compile("Genera i envia")).focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Enllaç enviat al correu de contacte")).to_be_visible()
    expect(page.get_by_text("Vigent fins al")).to_be_visible()
    review("administracio-enllac-enviat")
    token = last_token()
    assert token not in page.content() and EMAIL not in page.content()

    # El convidat, sense cap sessió: l'adreça queda sense testimoni i només veu el seu càrrec.
    admin_cookies = page.context.cookies()
    page.context.clear_cookies()
    page.goto(f"{live_server.url}/convidat/{token}/")
    expect(page).to_have_url(f"{live_server.url}/convidat/")
    expect(page.get_by_role("heading", name=CONCEPT)).to_be_visible()
    expect(page.get_by_text("120,00 €")).to_be_visible()
    expect(page.get_by_role("link", name="Paga ara")).to_be_visible()  # pantalla del 05b
    assert page.get_by_role("button").count() == 0
    assert "Mar" not in page.locator("main").inner_text()
    review("convidat-pendent")

    # Càrrec pagat (com ho farà el 05b): només l'estat.
    payment = Payment.objects.create(charge=charge, method="card", amount_cents=12000)
    charges.mark_paid(charge, payment, origin="provider", by=audit.system("proves-e2e"))
    page.reload()
    expect(page.get_by_text("Aquest pagament ja està fet")).to_be_visible()
    review("convidat-pagat")

    # L'administració el revoca (segon pas desplegable) i la pàgina oberta deixa de mostrar res.
    # Torna la sessió d'administració d'abans: un codi TOTP no es pot fer servir dues vegades.
    page.context.clear_cookies()
    page.context.add_cookies(admin_cookies)
    page.goto(f"{live_server.url}/{ADMIN}/enllacos-convidat/")
    page.get_by_text("Revoca…").click()
    review("administracio-revoca-oberta")
    page.get_by_role("button", name="Revoca l'enllaç").click()
    expect(page.get_by_text("Enllaç revocat")).to_be_visible()
    review("administracio-revocat")
    assert GuestLink.objects.get().revoked_at is not None
    page.context.clear_cookies()
    page.goto(f"{live_server.url}/convidat/{token}/")
    expect(page.get_by_text("Aquest enllaç no és vàlid o ha caducat.")).to_be_visible()


def test_invalid_link_new_link_request_and_block(page, live_server, texts, review, page_checks):
    charge = guest_charge(texts)
    guest_links.create(charge.person, charge, by=texts)
    old = last_token()

    page.goto(f"{live_server.url}/convidat/testimoni-inventat-de-proves/")
    expect(page).to_have_url(f"{live_server.url}/convidat/")
    expect(page.get_by_text("Aquest enllaç no és vàlid o ha caducat.")).to_be_visible()
    assert CONCEPT not in page.content()
    review("convidat-no-valid")

    # Només amb el teclat: l'enllaç «Demana un enllaç nou», l'adreça i Intro.
    page.get_by_role("link", name="Demana un enllaç nou").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Demana un enllaç nou")).to_be_visible()
    review("enllac-nou")
    page.get_by_label("Correu electrònic").focus()
    page.keyboard.type(EMAIL)
    page.keyboard.press("Enter")
    expect(page.get_by_text("Si aquesta adreça té cap pagament pendent")).to_be_visible()
    review("enllac-nou-demanat")
    new = last_token()
    assert new != old and new not in page.content()

    # El nou funciona i l'anterior ja no (CA-02.5).
    page.goto(f"{live_server.url}/convidat/{new}/")
    expect(page.get_by_role("heading", name=CONCEPT)).to_be_visible()
    page.goto(f"{live_server.url}/convidat/{old}/")
    expect(page.get_by_text("Aquest enllaç no és vàlid o ha caducat.")).to_be_visible()

    # Massa testimonis que no funcionen des del mateix origen (V-02): bloqueig, sense cap dada.
    for _ in range(limits.GUEST_FAILED_WINDOW.max_count - 2):
        page.goto(f"{live_server.url}/convidat/testimoni-inventat-de-proves/")
    page_checks.expect(429, f"/convidat/{new}/")
    page.goto(f"{live_server.url}/convidat/{new}/")
    expect(page.get_by_text("Massa intents seguits")).to_be_visible()
    assert CONCEPT not in page.content()
    review("convidat-bloquejat")
