"""Resultat, certificat i titulació del club (T-M02-19; RN-M02-16 i RN-M02-31; CA-M02-19; AC12 i
AC13). Portat de la branca aparcada. Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.activities import catalogue, certificates, certifications, enrolment, sessions, states
from apps.activities.models import CourseOutcome, DiverCertification, Enrolment, Session
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import BEFORE_DEADLINE, a_member, a_place, an_entry, an_open_course, moment

pytestmark = pytest.mark.django_db

O = CourseOutcome.Result  # noqa: E741
DAY = datetime.date(2027, 6, 20)


def confirmed(activity, first="Alumna"):
    account = a_member(first)
    row = enrolment.enrol(activity, account.person, channel="account", actor=account,
                          now=BEFORE_DEADLINE)  # fmt: skip
    Enrolment.objects.filter(pk=row.pk).update(status=Enrolment.Status.CONFIRMED)
    row.refresh_from_db()
    return row


@pytest.fixture
def course(make_admin):  # noqa: F811
    manager = make_admin(Role.Code.COURSES_MANAGER)
    teacher = make_admin("instructor")
    level = catalogue.create_level(by=manager, name="Nivell inventat B1", rank=10)
    entry = an_entry(manager, level="Nivell inventat B1")
    activity = an_open_course(manager, entry, title="Curs inventat de certificat")
    sessions.add_session(
        activity, by=manager, kind=Session.Kind.SEA, starts_at=moment(2027, 6, 14, 9),
        ends_at=moment(2027, 6, 14, 11), place=a_place(manager), is_practice=True,
        instructors=[teacher.person],
    )  # fmt: skip
    student, mate = confirmed(activity), confirmed(activity, "Company")
    states.advance_by_clock(now=moment(2027, 6, 14, 12))
    activity.refresh_from_db()
    return type("Course", (), dict(
        activity=activity, manager=manager, teacher=teacher, level=level, student=student,
        mate=mate,
    ))  # fmt: skip


def test_ca_m02_19_without_pass_no_certificate_and_with_pass_a_unique_number(course):
    with pytest.raises(ValidationError, match="apte"):
        certificates.issue(course.student, by=course.manager, today=DAY)
    certificates.record_outcome(
        course.mate, result=O.FAIL, reason="Falta pràctica.", by=course.teacher
    )
    with pytest.raises(ValidationError, match="apte"):
        certificates.issue(course.mate, by=course.manager, today=DAY)

    certificates.record_outcome(course.student, result=O.PASS, by=course.teacher)
    first = certificates.issue(course.student, by=course.manager, today=DAY)
    again = certificates.issue(course.student, by=course.manager, today=DAY)

    assert first.certificate_number == again.certificate_number == "C-2027-0001"
    data = certificates.certificate(course.student)
    assert (data["number"], data["grants"], data["issuer"]) == (
        "C-2027-0001",
        "Nivell inventat B1",
        "C.R.I.S.",
    )
    assert certificates.certificate(course.mate) is None
    assert AuditEntry.objects.filter(action=certificates.CERTIFICATE_ISSUED).count() == 1


def test_rn_m02_31_issuing_creates_the_club_certification_linked_to_the_outcome(course):
    certificates.record_outcome(course.student, result=O.PASS, by=course.teacher)
    outcome = certificates.issue(course.student, by=course.manager, today=DAY)

    cert = DiverCertification.objects.get(course_outcome=outcome)
    assert (cert.person, cert.level, cert.source, cert.issuer) == (
        course.student.person, course.level, "club_course", "C.R.I.S.",
    )  # fmt: skip
    assert (cert.certificate_number, cert.issued_on, cert.instructor) == (
        "C-2027-0001", DAY, course.teacher.person,
    )  # fmt: skip
    # CA-M02-33: compta també en mode «bloqueig» (RN-M02-30), sense verificar.
    assert cert.verified_by_id is None and certifications.counts(cert, "block")


def test_numbers_follow_per_year(course):
    for row in (course.student, course.mate):
        certificates.record_outcome(row, result=O.PASS, by=course.teacher)
    certificates.issue(course.student, by=course.manager, today=DAY)
    second = certificates.issue(course.mate, by=course.manager, today=datetime.date(2028, 1, 3))
    assert second.certificate_number == "C-2028-0001"


def test_outcome_rules(course, make_admin):  # noqa: F811
    with pytest.raises(ValidationError, match="motiu"):
        certificates.record_outcome(course.student, result=O.FAIL, by=course.teacher)
    for stranger in (make_admin("instructor"), make_admin("secretary")):
        with pytest.raises(Http404):
            certificates.record_outcome(course.student, result=O.PASS, by=stranger)
    first = certificates.record_outcome(
        course.student, result=O.FAIL, reason="X.", by=course.teacher
    )
    certificates.record_outcome(course.student, result=O.PASS, by=course.teacher)  # es corregeix
    certificates.issue(course.student, by=course.manager, today=DAY)
    with pytest.raises(ValidationError, match="ja s'ha emès"):
        certificates.record_outcome(course.student, result=O.FAIL, reason="Y.", by=course.teacher)
    entries = AuditEntry.objects.filter(
        action=certificates.OUTCOME_RECORDED, target_id=str(first.pk)
    )
    assert [(e.old_value, e.new_value) for e in entries.order_by("pk")] == [
        (None, "fail"),
        ("fail", "pass"),
    ]


def test_only_ac13_issues_and_a_level_is_needed(course, make_admin):  # noqa: F811
    certificates.record_outcome(course.student, result=O.PASS, by=course.teacher)
    with pytest.raises(Http404):
        certificates.issue(course.student, by=course.teacher, today=DAY)
    course.activity.catalogue_entry.__class__.objects.filter(
        pk=course.activity.catalogue_entry_id
    ).update(level="Un nivell que no és a la llista")
    with pytest.raises(ValidationError, match="nivell"):
        certificates.issue(course.student, by=course.manager, today=DAY)
    outcome = certificates.issue(course.student, by=course.manager, level=course.level, today=DAY)
    assert outcome.certificate_number


def test_the_database_keeps_numbers_unique_and_only_for_pass(course):
    certificates.record_outcome(course.student, result=O.PASS, by=course.teacher)
    certificates.issue(course.student, by=course.manager, today=DAY)
    other = certificates.record_outcome(course.mate, result=O.PASS, by=course.teacher)
    with pytest.raises(IntegrityError), transaction.atomic():
        CourseOutcome.objects.filter(pk=other.pk).update(certificate_number="C-2027-0001")
    with pytest.raises(IntegrityError), transaction.atomic():
        CourseOutcome.objects.filter(pk=other.pk).update(
            result="fail", reason="", certificate_number=""
        )
