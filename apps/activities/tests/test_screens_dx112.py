"""T-DX-112 (Horario al 02): «Les meves activitats» porta l'horari (C16) amb les properes sessions
de les inscripcions vives de la persona, agrupades per dia (agenda d'Horario). Les sessions de cada
inscripció són les del grup i els reforços d'aquell alumne, mai els d'un altre (RN-M02-25), també
al fitxer de calendari, i sense les cancel·lades. Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_PERSONAL
from apps.activities.models import Session
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_place, moment
from .test_certificates import course  # noqa: F401 (fixture)
from .test_my_activities import MINE

pytestmark = pytest.mark.django_db


def _extra(course, **fields):  # noqa: F811
    return Session.objects.create(
        activity=course.activity, kind=Session.Kind.POOL, place=a_place(course.manager), **fields
    )


def test_the_calendar_and_the_agenda_only_have_her_own_sessions(login_as, course):  # noqa: F811
    theirs = _extra(
        course, starts_at=moment(2027, 6, 20, 10), ends_at=moment(2027, 6, 20, 11),
        reinforcement_for=course.mate,
    )  # fmt: skip
    _extra(
        course,
        starts_at=moment(2027, 6, 21, 18),
        ends_at=moment(2027, 6, 21, 19),
        cancelled=True,
        cancellation_reason="Piscina tancada (inventat).",
    )
    student = login_as(Account.objects.get(person=course.student.person), AREA_PERSONAL)
    ics = student.get(reverse("activities:enrolment_calendar", args=[course.student.pk]))
    assert f"sessio-{theirs.pk}@" not in ics.content.decode()  # el reforç d'un company, mai
    page = student.get(MINE).content.decode()
    assert 'class="horario-dies"' in page
    assert page.count('class="horario-acte"') == 1  # la del grup; ni el reforç ni la cancel·lada
