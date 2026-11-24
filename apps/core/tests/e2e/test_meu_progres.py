"""«El meu progrés» al navegador (T-M02-17b; HU-M02-14): una alumna entra a «Les meves activitats»
i obre el progrés del seu curs amb el resultat de la pràctica. Pantalles a 1280, 390 i 320 px.
Només dades inventades."""

import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities import assessment, states
from apps.activities.models import PracticeAssessment, Session
from apps.activities.tests.helpers import a_place, an_open_course, moment
from apps.activities.tests.test_assessment import DAY, confirmed
from conftest import PASSWORD

from .conftest import make_admin

pytestmark = pytest.mark.e2e


def test_the_student_opens_her_progress(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    teacher = make_admin("instructor.prova", "instructor")
    activity = an_open_course(manager, title="Curs inventat de progrés")
    # Directament, com les altres e2e del 02: l'instructor inventat no és soci (RN-M02-26).
    practice = Session.objects.create(
        activity=activity,
        kind=Session.Kind.POOL,
        starts_at=moment(2027, 6, 14, 9),
        ends_at=moment(2027, 6, 14, 11),
        place=a_place(manager),
        is_practice=True,
    )
    practice.instructors.set([teacher.person])
    enrolment, account = confirmed(activity)
    states.advance_by_clock(now=moment(2027, 6, 14, 12))
    assessment.assess(practice, enrolment, result=PracticeAssessment.Result.ACHIEVED,
                      notes="Bona flotabilitat.", by=teacher, today=DAY)  # fmt: skip
    account.set_password(PASSWORD)
    account.save()

    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}{reverse('activities:mine')}")
    page.get_by_role("link", name=re.compile(r"^El meu progr")).click()
    expect(page.get_by_text("Bona flotabilitat.")).to_be_visible()
    expect(page.get_by_text("Assolit")).to_be_visible()
    review("meu-progres")
