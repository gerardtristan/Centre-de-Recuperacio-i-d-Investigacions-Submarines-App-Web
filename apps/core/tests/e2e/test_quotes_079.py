"""«Quotes i impagats» al navegador (T-M01-18; 079, RN-M01-86 i RN-M01-91): l'estat de la quota
del llistat i el de la revisió són el mateix, i la marca d'impagat amb motiu. Les pantalles es
desen a 1280, 390 i 320 px (clar i fosc).
"""

import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.members.models import Member

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH


def test_fee_review_and_manual_unpaid_mark(page, live_server, builder, member, review):
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}/{ADMIN}/quotes/")
    expect(page.get_by_role("heading", name="Quotes i impagats")).to_be_visible()
    expect(page.get_by_text("Pagada fins al")).to_be_visible()
    review("quotes")

    # El mateix estat al llistat de socis (un sol càlcul).
    page.goto(f"{live_server.url}/{ADMIN}/socis/")
    expect(page.get_by_text("Pagada fins al")).to_be_visible()
    review("llistat-amb-quota")

    page.goto(f"{live_server.url}/{ADMIN}/quotes/")
    page.get_by_text("Marca impagat…").click()
    review("marca-impagat-oberta")
    # Només amb el teclat: motiu i enviar. La data ja és la d'avui i no admet futures.
    page.get_by_label("Motiu").focus()
    page.keyboard.type("Rebut retornat (prova inventada)")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Marca com a impagat")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_text("queda marcat com a impagat")).to_be_visible()
    review("marcat-impagat")
    assert Member.objects.get(pk=member.pk).status == Member.Status.UNPAID


def test_payment_of_a_left_member_is_reviewed(page, live_server, builder, member, review):
    """079 (A-17, RN-M01-89; CA-M01-98): el pagament d'un soci de baixa surt a «Pagaments per
    revisar» i el tresorer el marca com a revisat amb una nota, només amb el teclat."""
    from apps.core import audit
    from apps.members import fees, services
    from apps.members.models import AnnualFee

    Member.objects.filter(pk=member.pk).update(status=Member.Status.LEFT, left_on="2026-11-01")
    fee = AnnualFee.objects.filter(member=member).first()
    audit.record(services.FEE_PAID_AFTER_LEAVING, actor=audit.system("proves-e2e"), target=fee)
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}/{ADMIN}/quotes/")
    expect(page.get_by_role("heading", name="Pagaments per revisar")).to_be_visible()
    page.get_by_text("Marca com a revisat…").click()
    review("pagaments-per-revisar")
    page.get_by_label("Nota").focus()
    page.keyboard.type("Es retorna per transferència (prova inventada)")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Marca com a revisat", exact=True)).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Pagament marcat com a revisat.")).to_be_visible()
    expect(page.get_by_role("heading", name="Pagaments per revisar")).to_be_hidden()
    review("pagament-revisat")
    assert fees.payments_to_review() == []


def test_renewal_notice_without_address_is_listed(page, live_server, builder, review):
    """T-M01-43d: la secretaria veu a «Quotes i impagats» els socis de ple dret a qui toca l'avís
    de renovació i no tenen cap adreça, amb l'enllaç a la fitxa per afegir-n'hi una."""
    from datetime import timedelta

    from django.utils import timezone

    from apps.members.tests.test_cards import make_member
    from apps.members.tests.test_downgrade_073 import pay_annual_fee

    absent = make_member("Jordi", number=2401, document="00000023T")  # sense cap adreça
    pay_annual_fee(absent, timezone.now() - timedelta(days=355))  # renova d'aquí a 10 dies
    secretary = make_admin("secretaria.avis", "secretary")
    login_admin(page, live_server.url, secretary.login)
    page.goto(f"{live_server.url}/{ADMIN}/quotes/")
    heading = page.get_by_role("heading", name="Avís de renovació sense adreça")
    expect(heading).to_be_visible()
    review("avis-renovacio-sense-adreca")
    page.get_by_role("link", name="Jordi Prova").click()
    expect(page.get_by_role("heading", name="Jordi Prova")).to_be_visible()
