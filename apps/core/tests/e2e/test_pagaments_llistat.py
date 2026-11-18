"""Llistat de pagaments i «a revisar» al navegador (T-M05b-16 i 16b; B6). Un intent «a revisar» i un
altre en curs; el tresorer entra, veu el motiu i el pagador, i filtra per estat. Pantalles a 1280,
390 i 320 px (clar i fosc). Només dades inventades.
"""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.core import audit, charges
from apps.core.models import Person
from apps.payments import attempts
from apps.payments.models import PaymentAttempt

from .conftest import login_admin, make_admin, menu_entry

pytestmark = pytest.mark.e2e
S = PaymentAttempt.Status
SYSTEM = audit.system("proves-e2e")


def attempt(person, concept, status):
    charge = charges.create_charge(
        person, kind="fee", amount_cents=9000, concept=concept, origin="members", by=SYSTEM
    )
    found = attempts.create_attempt(charge, PaymentAttempt.Method.CARD)
    found = attempts.transition(found, S.IN_PROGRESS, by=SYSTEM)
    if status == S.TO_REVIEW:
        reason = "L'import de la notificació no quadra (prova)"
        found = attempts.transition(found, S.TO_REVIEW, by=SYSTEM, reason=reason)
    return found


def test_treasurer_sees_what_to_review_and_filters(page, live_server, transactional_db, review):
    person = Person.objects.create(first_name="Pere", last_name="Prova Inventat", origin="web")
    attempt(person, "Quota 2027 (prova)", S.TO_REVIEW)
    attempt(person, "Quota d'un altre soci (prova)", S.IN_PROGRESS)
    treasurer = make_admin("tresoreria.prova", "treasurer")

    login_admin(page, live_server.url, treasurer.login)
    # Hi arriba pel menú (T-DX-47): l'entrada només surt amb B6.
    entry = menu_entry(page, "Pagaments: llistat")
    entry.click()
    expect(page.get_by_role("heading", name="Pagaments i «a revisar»")).to_be_visible()
    expect(page).to_have_url(f"{live_server.url}{reverse('administration:payments_list')}")
    expect(entry).to_have_attribute("aria-current", "page")
    to_review = page.get_by_role("table", name="1 intent de pagament a revisar")
    expect(to_review).to_contain_text("L'import de la notificació no quadra (prova)")
    expect(to_review).to_contain_text("Pere Prova Inventat")
    review("pagaments-a-revisar")

    page.get_by_label("Estat").select_option(label="En curs")
    page.get_by_role("button", name="Filtra").click()
    expect(page.get_by_text("1 intent, del més recent al més antic")).to_be_visible()
    expect(page.get_by_role("cell", name="Quota d'un altre soci (prova)")).to_be_visible()
    review("pagaments-filtrats")


def test_treasurer_closes_an_attempt_to_review(page, live_server, transactional_db, review):
    """T-M05b-16b i 16c: «Tanca», la pàgina de confirmació amb la decisió i la nota obligatòries, i
    l'intent «fallit» passa a «Tancats» sense moure diners."""
    person = Person.objects.create(first_name="Pere", last_name="Prova Inventat", origin="web")
    attempt(person, "Quota 2027 (prova)", S.TO_REVIEW)
    treasurer = make_admin("tresoreria.prova", "treasurer")

    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}{reverse('administration:payments_list')}")
    page.get_by_role("link", name="Tanca").click()
    expect(page.get_by_role("heading", name="Tanca un pagament a revisar")).to_be_visible()
    page.get_by_role("button", name="Sí, tanca'l").click()
    expect(page.get_by_text("Cal una nota per tancar-lo.").first).to_be_visible()
    expect(page.get_by_text("Tria si s'ha pagat o ha fallat.").first).to_be_visible()
    review("tancar-a-revisar")

    page.get_by_label("Fallit: no s'ha cobrat.").check()
    page.get_by_label("Nota").fill("Ordre denegada al proveïdor (prova)")
    page.get_by_role("button", name="Sí, tanca'l").click()
    expect(page.get_by_text("Intent tancat com a fallit. No s'ha mogut cap diner.")).to_be_visible()
    expect(page.get_by_text("No hi ha cap pagament a revisar.")).to_be_visible()
    closed = page.get_by_role(
        "table", name="1 intent a revisar tancat, del més recent al més antic"
    )
    expect(closed).to_contain_text("Ordre denegada al proveïdor (prova)")
    expect(closed).to_contain_text("Fallit")
    expect(closed).to_contain_text("Tresoreria Prova")  # el nom, mai el login
    expect(closed).not_to_contain_text("tresoreria.prova")
    review("a-revisar-tancats")
