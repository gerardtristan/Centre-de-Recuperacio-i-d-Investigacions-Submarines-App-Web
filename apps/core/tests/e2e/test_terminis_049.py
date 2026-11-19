"""Pagament a terminis al navegador (T-M01-49; 097, P-61): amb l'ajust encès, el soci veu els
tres terminis a la quota de l'alta i els tria amb el teclat; el tresorer veu el candidat a
«impagat» d'un termini vençut. Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades
inventades.
"""

import re
from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone
from playwright.sync_api import expect

from apps.core.models import Setting
from apps.members import instalments, services
from apps.members import settings as values
from apps.members.models import AnnualFee
from apps.members.tests.test_cards import pay
from conftest import PASSWORD

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e

EMAIL = "marina.prova@example.org"


@pytest.fixture
def pending(builder):
    Setting.objects.filter(key=values.INSTALMENTS_ENABLED).update(initial_value=True)
    member = builder.approve(
        builder.submit(
            "Marina",
            "Prova Inventada",
            EMAIL,
            builder.born(30),
            builder.full,
            privacy=True,
            membership_terms=True,
        )
    )
    account = builder.personal(member.person)
    return member, account


def test_the_member_chooses_three_instalments(page, live_server, pending, review):
    member, _account = pending
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(EMAIL)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}/socis/quotes/{member.fees.get().pk}/")
    expect(page.get_by_role("heading", name="Pagar en tres terminis")).to_be_visible()
    review("quota-amb-terminis")

    page.get_by_role("button", name="Paga en tres terminis").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Has triat pagar la quota en tres terminis.")).to_be_visible()
    expect(page.get_by_role("heading", name=re.compile("termini 1 de 3"))).to_be_visible()
    review("primer-termini")
    page.goto(f"{live_server.url}/socis/quotes/")
    expect(page.get_by_role("rowheader", name=re.compile("termini 3 de 3"))).to_be_visible()
    review("quotes-amb-terminis")
    assert member.fees.filter(kind=AnnualFee.Kind.INSTALMENT).count() == 3


def test_the_treasurer_sees_the_candidate_to_unpaid(page, live_server, pending, review):
    member, account = pending
    first, second, _third = instalments.choose(member.fees.get(), by=account)
    pay(first)
    services.on_fee_paid(first.pk)
    second.due_on = timezone.localdate() - timedelta(days=31)
    second.save()
    login_admin(page, live_server.url, make_admin("tresoreria.prova", "treasurer").login)
    page.goto(f"{live_server.url}/{settings.ADMIN_URL_PATH}/quotes/")
    expect(page.get_by_text("Candidat a impagat: termini vençut")).to_be_visible()
    review("quotes-candidat-impagat")
