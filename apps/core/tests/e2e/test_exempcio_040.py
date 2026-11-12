"""Eximir i anul·lar una quota al navegador (T-M01-40; RN-M01-72 i RN-M01-94; CA-M01-65): el
tresorer veu les quotes a la fitxa del soci (dades mínimes), n'eximeix una amb motiu, contrasenya
i codi, i el soci pendent passa a actiu; i n'anul·la una altra. Tot amb el teclat. Pantalles a
1280, 390 i 320 px, en clar i en fosc. Només dades inventades.
"""

from datetime import datetime

import pyotp
import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.core.models import Charge
from apps.members.models import Member
from conftest import PASSWORD

from .conftest import TOTP_KEY, login_admin, make_admin
from .test_accessibilitat_028 import audit, problems

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH
REASON = "Acord de la junta (motiu inventat)."


@pytest.fixture(autouse=True)
def _no_motion(page):
    page.emulate_media(reduced_motion="reduce")


@pytest.fixture
def pending_member(builder):
    """Alta presencial aprovada per la secretaria: soci pendent amb la quota pendent."""
    request = builder.submit(
        "Laia",
        "Prova Inventada",
        "laia.prova@example.org",
        builder.born(35),
        builder.full,
        privacy=True,
        membership_terms=True,
    )
    return builder.approve(request)


def new_code():
    # Un codi d'un interval posterior al de l'entrada: el mateix no es pot fer servir dues vegades.
    return pyotp.TOTP(TOTP_KEY).at(datetime.now(), counter_offset=1)


def confirm(page, button):
    page.get_by_label("Motiu").focus()
    page.keyboard.type(REASON)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_label("Codi de l'aplicació d'autenticació").fill(new_code())
    page.get_by_role("button", name=button).focus()
    page.keyboard.press("Enter")


def test_treasurer_exempts_the_fee_of_a_pending_member(
    page, live_server, pending_member, review, page_checks
):
    member = pending_member
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}/{ADMIN}/socis/{member.pk}/")
    expect(page.get_by_role("heading", name="Quotes")).to_be_visible()
    expect(page.get_by_text("Vista de tresoreria: dades mínimes.")).to_be_visible()
    review("fitxa-quotes")
    # Auditoria automàtica d'accessibilitat (axe i recorregut amb el teclat) de les dues
    # pantalles: l'administrador de la T-M01-28 no té P22 i no les veu amb les accions.
    accessibility = {}
    audit(page, "fitxa-quotes-tresorer", accessibility)

    page.get_by_role("link", name="Eximeix…").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Eximeix la quota")).to_be_visible()
    review("eximeix-quota")
    audit(page, "eximeix-quota", accessibility)
    assert not problems(accessibility), "; ".join(problems(accessibility))

    # Sense motiu ni credencials no canvia res i cada error surt al seu camp.
    page.get_by_role("button", name="Eximeix la quota").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Cal el motiu.")).to_be_visible()
    review("eximeix-quota-errors")
    assert Member.objects.get(pk=member.pk).status == Member.Status.PENDING

    confirm(page, "Eximeix la quota")
    expect(page.get_by_text("Quota eximida. El soci és actiu")).to_be_visible()
    expect(page.get_by_role("link", name="Eximeix…")).to_have_count(0)
    review("fitxa-quota-eximida")
    member.refresh_from_db()
    assert member.status == Member.Status.ACTIVE
    charge = member.fees.get().charge
    assert (charge.status, charge.cancel_category) == (Charge.Status.CANCELLED, "exemption")


def test_treasurer_cancels_a_fee(page, live_server, pending_member, review):
    member = pending_member
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}/{ADMIN}/socis/{member.pk}/")
    page.get_by_role("link", name="Anul·la…").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Anul·la la quota")).to_be_visible()
    review("anulla-quota")

    confirm(page, "Anul·la la quota")
    expect(page.get_by_text("Quota anul·lada. Queda al registre d'activitat.")).to_be_visible()
    member.refresh_from_db()
    assert member.status == Member.Status.PENDING  # anul·lar no dona cap dret
    charge = member.fees.get().charge
    assert (charge.status, charge.cancel_category) == (Charge.Status.CANCELLED, "")
