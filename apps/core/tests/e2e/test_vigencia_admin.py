"""Vigencia a l'administració (T-DX-14): a la fitxa del soci, cada llicència amb caducitat
confirmada diu els dies que queden; una de vençuda surt en vermell i una declarada pel soci, pendent
de confirmar, no en mostra cap."""

import re
from datetime import timedelta

import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.members.fee_rules import local_today
from apps.members.models import LicenceRecord

from .conftest import login_admin

pytestmark = pytest.mark.e2e


def licence(member, kind, days, *, declared=False):
    return LicenceRecord.objects.create(
        member=member,
        licence_type=kind,
        issued_on=local_today() - timedelta(days=300),
        expires_on=local_today() + timedelta(days=days),
        expiry_declared=declared,
        source=LicenceRecord.Source.MANUAL,
    )


def test_member_page_shows_the_days_left_of_each_licence(
    page, live_server, secretary, member, review, page_checks
):
    licence(member, "Anual FECDAS", 40)
    licence(member, "Assegurança antiga", -3)
    licence(member, "Declarada pel soci", 100, declared=True)
    login_admin(page, live_server.url, secretary.login)
    page.goto(f"{live_server.url}/{settings.ADMIN_URL_PATH}/socis/{member.pk}/")

    rows = page.locator("#llicencia-titol + table tbody tr")
    expect(rows.filter(has_text="Anual FECDAS").locator(".vigencia-dies")).to_have_text(
        "Queden 40 dies"
    )
    expired = rows.filter(has_text="Assegurança antiga").locator(".vigencia")
    expect(expired).to_have_class(re.compile(r"vigencia-error"))
    expect(expired).to_contain_text("Va caducar fa 3 dies")
    expect(rows.filter(has_text="Declarada pel soci").locator(".vigencia")).to_have_count(0)
    review("fitxa-llicencies")
