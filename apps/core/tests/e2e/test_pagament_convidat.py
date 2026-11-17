"""Pagament d'un convidat amb l'enllaç de la 00, al navegador (T-M05b-08; CA-M05b-09; decisió 021;
CA-02.2, CA-02.4 i CA-02.9 de la 00). Proveïdor fals, entorn de proves, només dades inventades.

El convidat obre l'enllaç del correu sense cap compte, tria «Paga ara», paga amb targeta a la pàgina
del proveïdor fals i en torna: la pantalla diu que s'està confirmant fins que la notificació
verificada (processada per la cua) dona el càrrec per pagat; llavors només l'estat i el rebut."""

import re

import pytest
from playwright.sync_api import expect

from apps.core import audit, charges, guest_links
from apps.core.models import Charge, Department, OutgoingEmail, Person
from apps.payments.models import PaymentAttempt
from apps.payments.providers import fake
from apps.payments.tests.test_processing import run_queue

pytestmark = pytest.mark.e2e

EMAIL = "mar.convidada@example.org"
CONCEPT = "Curs Open Water (prova inventada)"
POLL = 10_000  # la pantalla torna a preguntar cada 3 s


@pytest.fixture
def token(texts, settings, live_server):
    settings.PUBLIC_SITE_URL = live_server.url  # on torna el navegador i on arriba l'avís
    fake.reset()
    person = Person.objects.create(
        first_name="Mar", last_name="Convidada Inventada", origin="web", contact_email=EMAIL
    )
    charge = charges.create_charge(
        person,
        kind=Charge.Kind.ENROLMENT,
        amount_cents=12000,
        concept=CONCEPT,
        origin="proves",
        department=Department.objects.get(name=Department.GENERAL),
        by=audit.system("proves-e2e"),
    )
    guest_links.create(person, charge, by=audit.system("proves-e2e"))
    body = OutgoingEmail.objects.filter(template=guest_links.EMAIL_TEMPLATE).latest("pk").body_text
    yield re.search(r"/convidat/([\w-]+)/", body).group(1)
    fake.reset()


def test_ca_m05b_09_the_guest_pays_by_card_and_sees_the_receipt(page, live_server, token, capture):
    page.goto(f"{live_server.url}/convidat/{token}/")
    page.get_by_role("link", name="Paga ara").click()
    expect(page).to_have_url(f"{live_server.url}/pagaments/convidat/")
    expect(page.get_by_role("heading", level=1, name=CONCEPT)).to_be_visible()
    expect(page.locator("#estat-pagament")).to_contain_text("Pendent")
    assert "Mar" not in page.locator("main").inner_text()  # cap dada personal (CA-02.2)
    capture("1-pendent")

    page.get_by_role("button", name="Paga amb targeta").click()
    expect(page.get_by_role("heading", name="Pagament de proves")).to_be_visible()
    attempt = PaymentAttempt.objects.get()
    assert attempt.guest_link_id and attempt.started_by_id is None
    page.get_by_role("button", name="Paga", exact=True).click()

    # CA-02.9: la tornada diu que s'està confirmant i el càrrec no canvia per aquesta visita.
    expect(page).to_have_url(re.compile(r"/pagaments/convidat/\?tornada=ok$"))
    expect(page.get_by_text("Estem confirmant el pagament")).to_be_visible()
    assert Charge.objects.get().status == Charge.Status.PENDING
    capture("2-tornada-ok")

    # La notificació verificada, a la cua, el dona per pagat: la pantalla ho mostra sola.
    run_queue()
    expect(page.get_by_text("El pagament s'ha confirmat.")).to_be_visible(timeout=POLL)
    expect(page.get_by_role("button", name="Paga amb targeta")).to_have_count(0)
    capture("3-pagat")

    page.get_by_role("link", name="Veure el rebut").click()
    expect(page.get_by_role("heading", name="Rebut")).to_be_visible()
    expect(page.get_by_text(CONCEPT)).to_be_visible()
    capture("4-rebut")
