"""Exportació RGPD amb les notes revisades al navegador (T-M01-22c; 085, A-1; P-416): amb
l'interruptor encès, l'administrador obre l'exportació des de «Més» de la fitxa del soci, revisa
les notes, en deixa una fora amb motiu i la prepara amb la contrasenya i el codi. Pantalles a 1280,
390 i 320 px (clar i fosc). Només dades inventades."""

from datetime import datetime

import pyotp
import pytest
from django.conf import settings
from django.db import transaction
from playwright.sync_api import expect

from apps.core import charges, privacy
from apps.core.models import Charge, Department
from conftest import PASSWORD

from .conftest import TOTP_KEY, login_admin, make_admin

pytestmark = pytest.mark.e2e


@pytest.fixture
def on(settings):
    settings.GDPR_ADMIN_NOTES_EXPORT_ENABLED = True


def test_the_administrator_reviews_the_notes_and_prepares_the_export(
    page, live_server, on, member, secretary, review
):
    for concept, reason in (
        ("Quota inventada 2025", "Anul·lada per un error de l'oficina (nota inventada)."),
        ("Quota inventada 2024", "La Marta Inventada diu que ja la va pagar (nota inventada)."),
    ):
        charge = charges.create_charge(
            member.person,
            kind=Charge.Kind.FEE,
            amount_cents=9000,
            concept=concept,
            department=Department.objects.get(name="General"),
            origin="members",
            by=secretary,
        )
        with transaction.atomic():
            charges.cancel(charge, reason, by=secretary)
    admin = make_admin("administracio.notes", "administrator")
    login_admin(page, live_server.url, admin.login)
    page.goto(f"{live_server.url}/{settings.ADMIN_URL_PATH}/socis/{member.pk}/")
    page.locator("summary", has_text="Més").click()
    page.get_by_role("link", name="Exportació RGPD amb notes…").click()
    expect(
        page.get_by_role("heading", name="Exportació amb notes: Pere Prova Inventat")
    ).to_be_visible()
    review("exportacio-amb-notes")

    page.get_by_label(
        "Deixa-la fora: Anul·lació del càrrec «Quota inventada 2024» (90,00 €)"
    ).check()
    page.get_by_role("button", name="Prepara l'exportació").click()
    expect(page.get_by_text("Cal el motiu per deixar fora alguna nota.")).to_be_visible()
    review("exportacio-amb-notes-sense-motiu")

    page.get_by_label("Motiu per deixar fora les notes marcades").fill("Parla d'un tercer.")
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_label("Codi de l'aplicació d'autenticació").fill(
        pyotp.TOTP(TOTP_KEY).at(datetime.now(), counter_offset=1)
    )
    page.get_by_role("button", name="Prepara l'exportació").click()
    expect(page.get_by_text("Exportació preparada amb les notes revisades.")).to_be_visible()
    review("exportacio-preparada")
    assert privacy.live_export(member.person) is not None
