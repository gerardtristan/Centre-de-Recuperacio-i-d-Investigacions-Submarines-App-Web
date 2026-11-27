"""Inscripció d'un no soci al navegador. Des del web demana el compte personal (T-M02-54;
decisió 108, C.1): sense sessió, «Inscriu-te sense ser soci» porta a entrar i, en entrar, torna a
l'activitat, a la inscripció de l'àrea personal amb el preu de no soci. El responsable n'inscriu
una altra en persona des de la fitxa (T-M02-14). Pantalles a 1280, 390 i 320 px (clar i fosc).
Només dades inventades."""

import datetime
import re

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from apps.activities import catalogue, guests, services, states
from apps.activities.models import Enrolment, OutingType
from apps.activities.tests.helpers import a_personal_account
from apps.core.models import LegalText
from conftest import PASSWORD

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_a_guest_online_and_another_at_the_desk(page, live_server, transactional_db, review):
    LegalText.objects.create(kind="privacy", version=1, content="Política inventada.")
    LegalText.objects.create(kind=guests.ADULT, version=1, content=guests.ADULT_PROPOSAL)
    manager = make_admin("cursos.prova", "courses_manager")
    outing = services.create_outing(
        by=manager, outing_type=OutingType.objects.get(name="Immersió"),
        title="Sortida inventada oberta", starts_on=datetime.date(2027, 6, 14),
        ends_on=datetime.date(2027, 6, 14), max_places=10, responsible=manager.person,
        registration_closes_at=timezone.make_aware(datetime.datetime(2027, 6, 10, 20)),
        price_member_cents=4500, price_non_member_cents=6000, open_to_non_members=True,
        meeting_point="Port inventat", place=catalogue.create_place(by=manager, name="Cala"),
    )  # fmt: skip
    states.publish(outing, by=manager)

    account = a_personal_account()  # una persona no sòcia amb compte personal
    account.set_password(PASSWORD)
    account.save()
    page.goto(f"{live_server.url}{reverse('activities:public_detail', args=[outing.pk])}")
    expect(
        page.get_by_text("Per inscriure't cal entrar amb el teu compte personal.")
    ).to_be_visible()
    review("inscripcio-no-soci-detall")
    page.get_by_role("link", name="Inscriu-te sense ser soci").click()
    expect(page).to_have_url(re.compile(r"/entrar/\?next="))
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    enrol = reverse("activities:member_enrol", args=[outing.pk])
    expect(page).to_have_url(f"{live_server.url}{enrol}")
    expect(page.get_by_role("heading", name="Sortida inventada oberta")).to_be_visible()
    review("inscripcio-no-soci-amb-sessio")

    login_admin(page, live_server.url, manager.login)
    page.goto(f"{live_server.url}{reverse('administration:activity_detail', args=[outing.pk])}")
    heading = page.get_by_role("heading", name="Inscripció presencial d'un convidat")
    section = page.locator("section", has=heading)
    section.get_by_label("Nom", exact=True).fill("Pau")
    section.get_by_label("Cognoms").fill("Presencial Inventat")
    section.get_by_label("Correu electrònic").fill("pau@example.org")
    section.get_by_label("La persona diu que és major d'edat (pregunta-li-ho)").check()
    section.get_by_label("Ha llegit i accepta la política de privacitat").check()
    section.get_by_role("button", name="Inscriu el convidat").click()
    expect(page.get_by_text("Inscripció feta.")).to_be_visible()
    review("inscripcio-presencial")
    assert Enrolment.objects.filter(channel=Enrolment.Channel.DESK).count() == 1
