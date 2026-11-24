"""«Les meves activitats» al navegador (T-M02-22b i 22c): una sòcia inscrita a una sortida en veu
l'estat, el botó per pagar-la i el calendari; una alumna apta obre el seu certificat per imprimir.
Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import datetime

import pytest
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from apps.activities import certificates, enrolment
from apps.activities.models import CertificationLevel, CourseOutcome, Enrolment
from apps.activities.tests.helpers import a_course, a_member, an_open_outing
from apps.activities.tests.test_attendance import a_session, opened
from conftest import PASSWORD

from .conftest import make_admin

pytestmark = pytest.mark.e2e


def log_in(page, live_server, account):
    account.set_password(PASSWORD)
    account.save()
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()


def test_a_member_sees_her_activities(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    outing = an_open_outing(manager, title="Sortida inventada meva", price_member_cents=4500)
    account = a_member("Sòcia")
    with transaction.atomic():
        enrolment.enrol(outing, account.person, channel="account", actor=account)

    log_in(page, live_server, account)
    page.goto(f"{live_server.url}{reverse('activities:mine')}")
    expect(page.get_by_role("heading", name="Sortida inventada meva")).to_be_visible()
    expect(page.get_by_text("Pendent de pagament")).to_be_visible()
    review("meves-activitats")


def test_a_student_opens_her_certificate(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    teacher = make_admin("instructor.prova", "instructor")
    course = opened(a_course(manager, title="Curs inventat de certificat"))
    a_session(manager, course, timezone.localdate(), teacher.person)
    account = a_member("Alumna")
    row = Enrolment.objects.create(
        activity=course, person=account.person, status=Enrolment.Status.CONFIRMED,
        channel="account", price_kind="member", price_cents=4500, created_at=timezone.now(),
    )  # fmt: skip
    certificates.record_outcome(row, result=CourseOutcome.Result.PASS, by=teacher)
    level = CertificationLevel.objects.create(name="Nivell inventat B1", rank=99)
    certificates.issue(row, by=manager, level=level)

    log_in(page, live_server, account)
    page.goto(f"{live_server.url}{reverse('activities:mine')}")
    page.get_by_role("link", name="Mira el certificat").click()
    expect(page.get_by_role("heading", name="Certificat de curs")).to_be_visible()
    expect(page.get_by_text("Nivell inventat B1")).to_be_visible()
    review("certificat-alumna")


def test_a_student_sees_her_schedule(page, live_server, transactional_db, review):
    # T-DX-112 (Horario, C16): les properes sessions del curs on té plaça, per dia.
    manager = make_admin("cursos.prova", "courses_manager")
    course = opened(a_course(manager, title="Curs inventat d'horari"))
    for days in (7, 9):
        a_session(manager, course, timezone.localdate() + datetime.timedelta(days=days))
    account = a_member("Alumna")
    Enrolment.objects.create(
        activity=course, person=account.person, status=Enrolment.Status.CONFIRMED,
        channel="account", price_kind="member", price_cents=4500, created_at=timezone.now(),
    )  # fmt: skip

    log_in(page, live_server, account)
    page.goto(f"{live_server.url}{reverse('activities:mine')}")
    expect(page.get_by_role("heading", name="Horari", exact=True)).to_be_visible()
    expect(page.locator(".horario-acte")).to_have_count(2)
    review("meves-activitats-horari")
