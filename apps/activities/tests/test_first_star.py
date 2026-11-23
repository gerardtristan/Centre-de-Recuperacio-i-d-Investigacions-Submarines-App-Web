"""Primera estrella (T-M02-45; addenda de la 104; RN-M02-52; CA-M02-55): en emetre el certificat
d'un alumne apte d'una fitxa amb `official_level`, es crea la tramitació `course` `requested`, una
per resultat; «Titulacions i llicències per tramitar» diu «Cal llicència» si no en té. Només dades
inventades."""

import datetime

import pytest
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.activities import catalogue, certificates, filings
from apps.activities.models import CertificationFiling, CourseOutcome, TrainingCatalogueEntry
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences.models import Licence, LicenceType, ValidityRule

from .test_certificates import DAY, course  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db

F = CertificationFiling
O = CourseOutcome.Result  # noqa: E741


def with_official_level(course):  # noqa: F811
    star = catalogue.create_level(by=course.manager, name="Una estrella (inventat)", rank=20)
    TrainingCatalogueEntry.objects.filter(pk=course.activity.catalogue_entry_id).update(
        official_level=star
    )
    return star


def pass_and_issue(course, enrolment):  # noqa: F811
    certificates.record_outcome(enrolment, result=O.PASS, by=course.teacher)
    return certificates.issue(enrolment, by=course.manager, today=DAY)


def test_ca_m02_55_a_course_filing_once_per_outcome(course):  # noqa: F811
    star = with_official_level(course)
    outcome = pass_and_issue(course, course.student)
    certificates.issue(course.student, by=course.manager, today=DAY)  # una segona vegada

    filing = F.objects.get()
    assert (filing.kind, filing.status, filing.target_level, filing.course_outcome) == (
        F.Kind.COURSE, F.Status.REQUESTED, star, outcome,
    )  # fmt: skip
    assert filing.person == course.student.person and filing.charge is None
    assert filing.source_certification.course_outcome == outcome
    with pytest.raises(IntegrityError), transaction.atomic():
        F.objects.create(
            kind=F.Kind.COURSE, person=filing.person, status=F.Status.DONE,
            requested_by=course.manager, requested_at=filing.requested_at, course_outcome=outcome,
        )  # fmt: skip


def test_ca_m02_55_without_official_level_no_filing(course):  # noqa: F811
    pass_and_issue(course, course.student)
    assert not F.objects.exists()


def test_the_list_says_who_needs_a_licence(course, make_admin):  # noqa: F811
    with_official_level(course)
    pass_and_issue(course, course.student)
    pass_and_issue(course, course.mate)
    kind = LicenceType.objects.create(
        name="Aficionat (inventat)", category=LicenceType.Category.AMATEUR,
        validity_rule=ValidityRule.CALENDAR_YEAR,
    )  # fmt: skip
    Licence.objects.create(
        person=course.mate.person, licence_type=kind, validity_rule=kind.validity_rule,
        status=Licence.Status.ACTIVE, origin=Licence.Origin.CLUB,
        starts_on=datetime.date(2027, 1, 1), expires_on=datetime.date(2027, 12, 31),
        price_kind="member", price_cents=9000,
    )  # fmt: skip
    secretary = make_admin(Role.Code.SECRETARY)
    rows = filings.course_pending(by=secretary, today=DAY)
    needs = {row["filing"].person_id: row["needs_licence"] for row in rows}
    assert needs == {course.student.person_id: True, course.mate.person_id: False}
    with pytest.raises(Http404):
        filings.course_pending(by=make_admin(Role.Code.INSTRUCTOR), today=DAY)
