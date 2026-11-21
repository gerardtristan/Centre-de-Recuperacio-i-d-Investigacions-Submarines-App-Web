"""Avaluació per pràctica i «El meu progrés» (T-M02-17; RN-M02-17; HU-M02-12 i 14; AC10a; C3).
Portat de la branca aparcada. Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import assessment, enrolment, sessions, states
from apps.activities.models import Enrolment, PracticeAssessment, Session
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import BEFORE_DEADLINE, a_member, a_place, an_open_course, moment

pytestmark = pytest.mark.django_db

R = PracticeAssessment.Result
DAY = datetime.date(2027, 6, 14)


def confirmed(activity, first="Alumna"):
    account = a_member(first)
    row = enrolment.enrol(activity, account.person, channel="account", actor=account,
                          now=BEFORE_DEADLINE)  # fmt: skip
    Enrolment.objects.filter(pk=row.pk).update(status=Enrolment.Status.CONFIRMED)
    row.refresh_from_db()
    return row, account


@pytest.fixture
def course(make_admin):  # noqa: F811
    """Un curs amb una teoria i una pràctica de l'instructor `own`, una pràctica d'un altre
    instructor i dos alumnes confirmats."""
    manager = make_admin(Role.Code.COURSES_MANAGER)
    own, other = make_admin("instructor"), make_admin("instructor")
    place = a_place(manager)
    activity = an_open_course(manager, title="Curs inventat d'avaluació")

    def add(kind, day, hour, teacher, practice):
        return sessions.add_session(
            activity, by=manager, kind=kind, starts_at=moment(2027, 6, day, hour),
            ends_at=moment(2027, 6, day, hour + 2), place=place, is_practice=practice,
            instructors=[teacher.person],
        )  # fmt: skip

    theory = add(Session.Kind.THEORY, 14, 9, own, False)
    practice = add(Session.Kind.POOL, 14, 11, own, True)
    sea = add(Session.Kind.SEA, 15, 9, other, True)
    (student, account), (mate, _) = confirmed(activity), confirmed(activity, "Company")
    states.advance_by_clock(now=moment(2027, 6, 14, 12))
    activity.refresh_from_db()
    return type("Course", (), dict(
        activity=activity, theory=theory, practice=practice, sea=sea, own=own, other=other,
        student=student, account=account, mate=mate,
    ))  # fmt: skip


def test_hu_m02_12_the_instructor_assesses_a_practice_and_can_correct_it(course):
    row = assessment.assess(course.practice, course.student, result=R.NEEDS_REINFORCEMENT,
                            notes="Equilibri per treballar.", by=course.own, today=DAY)  # fmt: skip
    assert (row.result, row.notes, row.recorded_by) == (
        R.NEEDS_REINFORCEMENT,
        "Equilibri per treballar.",
        course.own,
    )
    same = assessment.assess(
        course.practice, course.student, result=R.NEEDS_REINFORCEMENT,
        notes="Equilibri per treballar.", by=course.own, today=DAY,
    )  # fmt: skip
    assert same.pk == row.pk
    assessment.assess(course.practice, course.student, result=R.ACHIEVED, by=course.own, today=DAY)
    entries = AuditEntry.objects.filter(action=assessment.ASSESSED).order_by("pk")
    assert [(e.old_value, e.new_value) for e in entries] == [
        (None, R.NEEDS_REINFORCEMENT), (R.NEEDS_REINFORCEMENT, R.ACHIEVED),
    ]  # fmt: skip
    assert PracticeAssessment.objects.count() == 1


def test_only_who_teaches_the_session_assesses_it(course, make_admin):  # noqa: F811
    for by in (course.other, make_admin("secretary"), course.account):
        with pytest.raises(Http404):
            assessment.assess(course.practice, course.student, result=R.ACHIEVED, by=by, today=DAY)
    assert not PracticeAssessment.objects.exists()


def test_only_practices_from_their_day_and_confirmed_students(course):
    with pytest.raises(ValidationError, match="pràctiques"):
        assessment.assess(
            course.theory, course.student, result=R.ACHIEVED, by=course.own, today=DAY
        )
    with pytest.raises(ValidationError, match="Encara no"):
        assessment.assess(course.practice, course.student, result=R.ACHIEVED, by=course.own,
                          today=DAY - datetime.timedelta(days=1))  # fmt: skip
    Enrolment.objects.filter(pk=course.mate.pk).update(
        status=Enrolment.Status.CANCELLED, cancelled_reason="Inventat"
    )
    with pytest.raises(ValidationError, match="confirmada"):
        assessment.assess(course.practice, course.mate, result=R.ACHIEVED, by=course.own, today=DAY)


def test_notes_are_short_and_the_result_known(course):
    with pytest.raises(ValidationError, match="500"):
        assessment.assess(course.practice, course.student, result=R.ACHIEVED, notes="x" * 501,
                          by=course.own, today=DAY)  # fmt: skip
    with pytest.raises(ValidationError):
        assessment.assess(
            course.practice, course.student, result="excel·lent", by=course.own, today=DAY
        )


def test_nobody_assesses_themselves(course, make_admin):  # noqa: F811
    """M02-4: un instructor inscrit al curs no es pot avaluar a si mateix."""
    own_row = Enrolment.objects.create(
        activity=course.activity, person=course.own.person, status=Enrolment.Status.CONFIRMED,
        channel="desk", price_kind="member", price_cents=0, created_at=BEFORE_DEADLINE,
    )  # fmt: skip
    with pytest.raises(ValidationError, match="pròpia"):
        assessment.assess(course.practice, own_row, result=R.ACHIEVED, by=course.own, today=DAY)
    assert AuditEntry.objects.filter(action=assessment.OWN_REJECTED).count() == 1


def test_the_sheet_and_the_list_of_practices_of_the_instructor(course):
    assessment.assess(course.practice, course.student, result=R.ACHIEVED, by=course.own, today=DAY)
    rows = assessment.sheet(course.practice, viewer=course.own)
    assert [(r.enrolment_id, r.result) for r in rows] == [  # per cognoms i nom
        (course.student.pk, R.ACHIEVED),
        (course.mate.pk, None),
    ]
    assert list(assessment.practice_sessions(course.own)) == [course.practice]
    with pytest.raises(Http404):
        assessment.sheet(course.practice, viewer=course.other)


def test_hu_m02_14_my_progress_shows_only_my_marks(course):
    assessment.assess(course.practice, course.student, result=R.ACHIEVED, notes="Bé.",
                      by=course.own, today=DAY)  # fmt: skip
    assessment.assess(course.practice, course.mate, result=R.NOT_ACHIEVED, by=course.own, today=DAY)

    mine = assessment.progress(course.student)

    assert [(r["session"], r["result"], r["notes"]) for r in mine] == [
        (course.practice, R.ACHIEVED, "Bé."), (course.sea, None, ""),
    ]  # fmt: skip


def test_assessments_are_in_the_gdpr_export_and_notes_go_on_anonymising(course):
    from apps.activities import privacy

    assessment.assess(course.practice, course.student, result=R.ACHIEVED, notes="Bé.",
                      by=course.own, today=DAY)  # fmt: skip
    (row,) = privacy.export(course.student.person)["avaluacions"]
    assert (row["resultat"], row["observacio"]) == ("Assolit", "Bé.")
    privacy.anonymise(course.student.person, by=course.own)
    mark = PracticeAssessment.objects.get()
    assert (mark.result, mark.notes) == (R.ACHIEVED, "")
