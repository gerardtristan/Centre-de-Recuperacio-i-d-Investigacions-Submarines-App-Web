"""Passar llista al mòbil (T-M02-16b; P-M02-E; CA-M02-17): l'instructor marca un alumne, perd la
cobertura, la marca queda «Pendent d'enviar» i s'envia sola en tornar. Pantalles a 1280, 390 i
320 px. Només dades inventades."""

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from apps.activities.models import Attendance, PracticeAssessment, Session
from apps.activities.tests.helpers import a_course
from apps.activities.tests.test_attendance import a_session, enrolled, opened

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_instructor_marks_offline_and_it_is_sent_later(
    page, live_server, transactional_db, review, page_checks
):
    manager = make_admin("cursos.prova", "courses_manager")
    teacher = make_admin("instructor.prova", "instructor")
    activity = opened(a_course(manager))
    session = a_session(manager, activity, timezone.localdate(), teacher.person)
    enrolled(activity, "Alumna")
    login_admin(page, live_server.url, teacher.login)
    page.set_viewport_size({"width": 390, "height": 844})

    page.goto(f"{live_server.url}{reverse('administration:attendance_sessions')}")
    review("passar-llista-sessions")
    page.get_by_role("link", name="Obre la llista").click()
    expect(page.get_by_role("heading", name=activity.title)).to_be_visible()

    page_checks.ignore("ERR_INTERNET_DISCONNECTED")  # la prova talla la connexió a propòsit
    page.context.set_offline(True)
    page.get_by_role("button", name="Hi és").first.click()
    expect(page.locator("[data-estat]").get_by_text("Pendent d'enviar")).to_be_visible()
    review("passar-llista-pendent")
    page.context.set_offline(False)
    page.evaluate("window.dispatchEvent(new Event('online'))")
    expect(page.locator("[data-estat]").get_by_text("Hi és")).to_be_visible()
    review("passar-llista")
    assert Attendance.objects.get(session=session).present is True


def test_the_instructor_assesses_a_practice(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    teacher = make_admin("instructor.prova", "instructor")
    activity = opened(a_course(manager))
    session = a_session(manager, activity, timezone.localdate(), teacher.person)
    Session.objects.filter(pk=session.pk).update(is_practice=True)
    enrolled(activity, "Alumna")
    login_admin(page, live_server.url, teacher.login)

    roll = reverse("administration:attendance_roll_session", args=[activity.pk, session.pk])
    page.goto(f"{live_server.url}{roll}")
    page.get_by_role("link", name="Avalua la pràctica").click()
    expect(page.get_by_role("heading", name="Alumna Prova")).to_be_visible()
    page.get_by_text("Necessita reforç").click()
    page.get_by_label("Observació").fill("Cal practicar la flotabilitat.")
    review("avaluacio-formulari")
    page.get_by_role("button", name="Desa l'avaluació").click()
    expect(page.get_by_text("Avaluació desada.")).to_be_visible()
    review("avaluacio")
    assert PracticeAssessment.objects.get().result == "needs_reinforcement"
