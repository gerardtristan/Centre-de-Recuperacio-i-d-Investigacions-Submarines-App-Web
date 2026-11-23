"""Dades inventades del 02 (T-M02-25): «es carreguen amb una ordre», només en desenvolupament, i
tot el que creen és inventat i passa pels serveis."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.activities import demo_data
from apps.activities.models import (
    Activity,
    Attendance,
    CertificationAgency,
    CertificationLevel,
    CourseOutcome,
    Enrolment,
    Place,
    PracticeAssessment,
    Session,
    TrainingCatalogueEntry,
)
from apps.core.models import AuditEntry, OutgoingEmail
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_seed_demo_data import DEV, cluber_path, run  # noqa: F401 (fixture)

from .helpers import a_member, general

pytestmark = pytest.mark.django_db
S = Activity.Status


@pytest.fixture
def created(make_admin):  # noqa: F811
    manager, instructor = make_admin("courses_manager"), make_admin("instructor")
    people = [a_member(f"Persona{n}", account=False) for n in range(4)]
    return demo_data.create(
        manager=manager, instructor=instructor, department=general(), participants=people
    )


def test_it_creates_a_catalogue_places_and_activities_in_every_state(created):
    assert TrainingCatalogueEntry.objects.count() == created.entries == 3
    assert CertificationLevel.objects.count() == created.levels == 2
    assert CertificationAgency.objects.filter(name="Agència de prova").exists()
    assert Place.objects.count() == 2
    assert Activity.objects.count() == created.activities == 5
    assert set(Activity.objects.values_list("status", flat=True)) == {
        S.DRAFT, S.OPEN, S.IN_PROGRESS, S.DONE, S.CANCELLED,
    }  # fmt: skip
    advanced = TrainingCatalogueEntry.objects.get(name="Curs de prova avançat")
    assert advanced.prices.count() == 2  # un canvi de preu que encara ha d'entrar en vigor
    assert created.draft_course.sessions.count() == 2
    assert all(s.instructors.count() == 1 for s in Session.objects.all())
    assert created.open_outing.programme_blocks.count() == 4
    assert created.open_outing.required_specialities.count() == 1
    assert created.cancelled_outing.cancellation_reason


def test_enrolments_assessments_and_the_result(created):
    assert Enrolment.objects.count() == created.enrolments == 4
    assert Enrolment.objects.filter(status="confirmed").count() == 3
    assert Enrolment.objects.filter(status="pending_payment").count() == 1
    assert Attendance.objects.filter(present=True).count() == 2
    assert set(PracticeAssessment.objects.values_list("result", flat=True)) == {
        "achieved", "needs_reinforcement",
    }  # fmt: skip
    (outcome,) = CourseOutcome.objects.all()
    assert outcome.result == "pass" and outcome.certificate_number.startswith("C-")
    assert created.running_course.status == S.IN_PROGRESS


def test_everything_is_invented_and_goes_through_the_services(created):
    for model in (
        TrainingCatalogueEntry,
        CertificationLevel,
        Place,
    ):  # les agències: també les de la migració
        assert all("de prova" in obj.name.lower() for obj in model.objects.all()), model
    assert all("de prova" in a.title.lower() for a in Activity.objects.all())
    assert AuditEntry.objects.filter(action="activities.activity.created").count() == 5
    assert not OutgoingEmail.objects.exists()


def call(*args):
    out = StringIO()
    call_command("seed_activities_demo_data", *args, stdout=out)
    return out.getvalue()


@pytest.mark.parametrize(("module", "debug"), [("config.settings.prod", False), (None, True)])
def test_the_command_refuses_outside_development(module, debug):
    with override_settings(SETTINGS_MODULE=module, DEBUG=debug), pytest.raises(CommandError):
        call()
    assert not Activity.objects.exists()


@DEV
def test_t_m02_25_the_command_loads_the_module_data_once(cluber_path):  # noqa: F811
    with pytest.raises(CommandError, match="seed_demo_data"):
        call()
    run(cluber_path=cluber_path)  # ara ja carrega les del 02 (T-M02-25, nucli)
    with pytest.raises(CommandError, match="només es carreguen un cop"):
        call()
    assert Activity.objects.count() == 5
