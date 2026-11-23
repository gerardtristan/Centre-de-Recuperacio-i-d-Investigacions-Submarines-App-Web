"""T-M02-16c: inscripcions i assistència a l'exportació i a l'anonimització RGPD del 02 (L-M02-07;
decisió 028). L'exportació d'una persona no porta cap dada d'una altra. Només dades inventades."""

import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder

from apps.activities import attendance, privacy
from apps.activities.models import Enrolment
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .test_attendance import DAY, course, enrolled, manager  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db


def test_l_m02_07_export_has_own_enrolments_and_attendance_only(course):  # noqa: F811
    other = enrolled(course.activity, "Altra")
    attendance.mark(course.student, course.first, present=True, by=course.own, today=DAY)
    attendance.mark(other, course.first, present=False, by=course.own, today=DAY)
    data = privacy.export(course.student.person)
    (row,) = data["inscripcions"]
    assert (row["activitat"], row["estat"], row["preu_centims"]) == (
        course.activity.title, "Confirmada", 4500,
    )  # fmt: skip
    assert data["assistencia"] == [{"activitat": course.activity.title, "dia": DAY, "hi_era": True}]
    dumped = json.dumps(data, cls=DjangoJSONEncoder)
    assert "Altra" not in dumped and "Pendent" not in dumped  # cap altra persona


def test_anonymise_replaces_only_the_cancellation_reason_of_that_person(course):  # noqa: F811
    Enrolment.objects.filter(pk=course.unpaid.pk).update(
        status=Enrolment.Status.CANCELLED, cancelled_reason="Motiu personal (inventat)."
    )
    other = enrolled(course.activity, "Altra")
    Enrolment.objects.filter(pk=other.pk).update(
        status=Enrolment.Status.CANCELLED, cancelled_reason="Un altre motiu (inventat)."
    )
    privacy.anonymise(course.unpaid.person, by=course.own)
    course.unpaid.refresh_from_db()
    other.refresh_from_db()
    assert course.unpaid.status == "cancelled"
    assert course.unpaid.cancelled_reason == "Esborrat RGPD de la persona."
    assert other.cancelled_reason == "Un altre motiu (inventat)."
