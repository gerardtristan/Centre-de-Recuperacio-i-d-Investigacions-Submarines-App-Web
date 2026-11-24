"""Primera estrella al navegador (T-M02-45b i T-M02-49; RN-M02-52 i 58; RN-M06-28): un alumne apte
d'un curs amb nivell oficial surt a «Titulacions i llicències per tramitar» amb «Cal llicència», i
la secretaria en demana la primera llicència. Captures a 1280, 1024, 390 i 320 px, en clar i en
fosc (amb E2E_CAPTURES_ALL=1). Només dades inventades."""

import datetime
import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities import catalogue, states
from apps.activities.models import Session, TrainingCatalogueEntry
from apps.activities.tests.helpers import a_place, an_entry, an_open_course, moment
from apps.activities.tests.test_certificates import confirmed
from apps.activities.tests.test_first_star import pass_and_issue
from apps.licences.models import LicencePrice, LicenceType, ValidityRule

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_first_star_until_the_licence_is_requested(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    teacher = make_admin("instructor.prova", "instructor")
    catalogue.create_level(by=manager, name="Nivell inventat B1", rank=10)
    star = catalogue.create_level(by=manager, name="Una estrella (inventat)", rank=20)
    entry = an_entry(manager, level="Nivell inventat B1")
    TrainingCatalogueEntry.objects.filter(pk=entry.pk).update(official_level=star)
    activity = an_open_course(manager, entry, title="Curs inventat d'una estrella")
    # Directament, com les altres e2e del 02: l'instructor inventat no és soci (RN-M02-26).
    _session = Session.objects.create(
        activity=activity,
        kind=Session.Kind.SEA,
        starts_at=moment(2027, 6, 14, 9),
        ends_at=moment(2027, 6, 14, 11),
        place=a_place(manager),
        is_practice=True,
    )
    _session.instructors.set([teacher.person])
    student = confirmed(activity)
    states.advance_by_clock(now=moment(2027, 6, 14, 12))
    pass_and_issue(type("Course", (), {"teacher": teacher, "manager": manager}), student)
    kind = LicenceType.objects.create(
        name="Aficionat (inventat)", category=LicenceType.Category.AMATEUR,
        validity_rule=ValidityRule.CALENDAR_YEAR,
    )  # fmt: skip
    LicencePrice.objects.create(
        licence_type=kind, federation_cost_cents=4000, non_member_surcharge_cents=1000,
        valid_from=datetime.date(2026, 1, 1), note="Preu inventat.", created_by=manager,
    )  # fmt: skip
    login_admin(page, live_server.url, make_admin("secretaria.prova", "secretary").login)

    page.goto(f"{live_server.url}{reverse('administration:course_filings')}")
    expect(
        page.get_by_role("heading", name="Titulacions i llicències per tramitar")
    ).to_be_visible()
    expect(page.locator("td").get_by_text("Cal llicència")).to_be_visible()
    review("primera-estrella-cal-llicencia")
    page.get_by_label("Tipus de llicència").select_option(label=kind.name)
    page.get_by_role("button", name=re.compile(r"^Demana la primera llicència")).click()
    expect(page.get_by_text("Primera llicència demanada, amb el seu càrrec.")).to_be_visible()
    review("primera-estrella-demanada")
