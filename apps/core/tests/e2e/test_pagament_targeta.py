"""Pantalla de pagament amb targeta i els seus estats, al navegador (T-M05b-04; P-M05b-A;
CA-M05b-01, 02 i 08). Proveïdor fals, entorn de proves, només dades inventades.

El soci, des de «Les meves quotes», obre la pantalla de pagament, va a la pàgina del proveïdor
fals i en torna. La tornada només mostra el que diu el servidor, i la consulta amb HTMX canvia
l'estat sense tornar a carregar la pàgina.

Els canvis d'estat que farà el processament de les notificacions (T-M05b-05, una altra tasca)
aquí els fan els serveis: `attempts.transition` per a l'intent fallit i `_Builder.pay` per al
càrrec pagat. La prova del flux sencer de la llesca 2 els farà amb la notificació."""

import re

import pytest
from playwright.sync_api import expect

from apps.core import audit
from apps.core.models import Charge
from apps.payments import attempts
from apps.payments.models import PaymentAttempt, ProviderEvent
from apps.payments.providers import fake
from conftest import PASSWORD

pytestmark = pytest.mark.e2e

EMAIL = "nereida.prova@example.org"
CONFIRMING = "Estem confirmant el pagament"
POLL = 10_000  # la pantalla torna a preguntar cada 3 s


@pytest.fixture
def pending(builder, settings, live_server):
    """Soci amb l'alta aprovada, la quota pendent i el compte personal."""
    settings.PUBLIC_SITE_URL = live_server.url  # on torna el navegador i on arriba l'avís
    fake.reset()
    member = builder.approve(
        builder.submit(
            "Nereida",
            "Prova Inventada",
            EMAIL,
            builder.born(30),
            builder.full,
            privacy=True,
            membership_terms=True,
        )
    )
    builder.personal(member.person)
    yield member.fees.get()
    fake.reset()


def test_ca_m05b_01_02_08_card_payment_screen_and_its_states(
    page, live_server, builder, pending, capture
):
    fee, base_url = pending, live_server.url
    page.goto(f"{base_url}/entrar/")
    page.get_by_label("Correu electrònic").fill(EMAIL)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.get_by_role("navigation", name="Àrea de socis").get_by_role(
        "link", name="Les meves quotes"
    ).click()
    page.get_by_role("link", name=re.compile("^Detall")).click()
    capture("0-detall-de-la-quota")
    page.get_by_role("link", name="Paga ara").click()

    # Pendent: l'import del càrrec i el botó de pagar; cap camp de targeta.
    expect(page.get_by_role("heading", level=1, name=fee.charge.concept)).to_be_visible()
    status = page.locator("#estat-pagament")
    expect(status).to_contain_text("Pendent")
    expect(page.locator("main input:not([type=hidden])")).to_have_count(0)
    capture("1-pendent")

    # CA-M05b-01: l'ordre la crea el servidor i el navegador va a la pàgina del proveïdor.
    page.get_by_role("button", name="Paga amb targeta").click()
    expect(page.get_by_role("heading", name="Pagament de proves")).to_be_visible()
    attempt = PaymentAttempt.objects.get(charge=fee.charge)
    assert attempt.status == PaymentAttempt.Status.IN_PROGRESS
    assert attempt.amount_cents == fee.charge.amount_cents
    capture("2-pagina-del-proveidor")

    # P-83 (opció per defecte): torna sense pagar; l'intent continua en curs i no se n'obre cap.
    page.get_by_role("button", name="Torna sense pagar").click()
    expect(page).to_have_url(re.compile(r"\?tornada=ko$"))
    expect(page.get_by_text(CONFIRMING)).to_be_visible()
    expect(page.get_by_text(re.compile("no en pots començar cap altre"))).to_be_visible()
    expect(page.get_by_role("button", name="Paga amb targeta")).to_have_count(0)
    capture("3-en-curs-deixat-a-mitges")

    # El proveïdor l'acaba com a fallit (T-M05b-05): HTMX ho mostra sense tornar a carregar.
    attempts.transition(attempt, PaymentAttempt.Status.FAILED, by=audit.system("proves"))
    # El text de «en curs» també diu «no s'ha completat»: es busca el de «fallit».
    expect(page.get_by_text("L'últim intent de pagament no s'ha completat")).to_be_visible(
        timeout=POLL
    )
    capture("4-fallit")

    # Es torna a provar i es paga: la notificació signada arriba a la plataforma.
    page.get_by_role("button", name="Paga amb targeta").click()
    page.get_by_role("button", name="Paga", exact=True).click()
    # CA-M05b-02: la tornada «ok» diu que s'està confirmant i el càrrec no canvia.
    expect(page).to_have_url(re.compile(r"\?tornada=ok$"))
    expect(page.get_by_text(CONFIRMING)).to_be_visible()
    capture("5-tornada-ok")
    assert Charge.objects.get(pk=fee.charge.pk).status == Charge.Status.PENDING
    event = ProviderEvent.objects.get()
    assert (event.event_type, event.amount_cents) == ("paid", fee.charge.amount_cents)

    # El càrrec queda pagat al servidor (T-M05b-05): la pantalla ho mostra sola.
    builder.pay(fee)
    expect(status).to_contain_text("Pagat", timeout=POLL)
    expect(page.get_by_text("El pagament s'ha confirmat.")).to_be_visible()
    expect(page.get_by_role("button", name="Paga amb targeta")).to_have_count(0)
    capture("6-pagat")
