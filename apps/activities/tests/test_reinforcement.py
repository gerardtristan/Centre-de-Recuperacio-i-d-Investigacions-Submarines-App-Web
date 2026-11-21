"""Classes de reforç (T-M02-18; RN-M02-14, 15 i 17; CA-M02-18; AC10b i AC11). Portat de la branca
aparcada. Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import closing, duplicate, enrolment, privacy, reinforcement, sessions
from apps.activities.models import Enrolment, ReinforcementRequest, Session, TrainingCatalogueEntry
from apps.core.models import AuditEntry, Charge, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import BEFORE_DEADLINE, a_member, a_place, an_entry, an_open_course, moment

pytestmark = pytest.mark.django_db
RS = ReinforcementRequest.Status


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
    teacher, stranger = make_admin("instructor"), make_admin("instructor")
    place = a_place(manager)
    activity = an_open_course(manager, an_entry(manager, reinforcement_price_cents=3000))
    group = sessions.add_session(
        activity, by=manager, kind=Session.Kind.POOL, starts_at=moment(2027, 6, 14, 9),
        ends_at=moment(2027, 6, 14, 11), place=place, is_practice=True,
        instructors=[teacher.person],
    )  # fmt: skip
    return type("Course", (), dict(manager=manager, teacher=teacher, stranger=stranger,
                                   place=place, activity=activity, group=group,
                                   student=confirmed(activity)))  # fmt: skip


def classes(course, n):
    return [
        {"kind": Session.Kind.POOL, "starts_at": moment(2027, 6, 20 + i, 18),
         "ends_at": moment(2027, 6, 20 + i, 20), "place": course.place,
         "instructors": [course.teacher.person]}
        for i in range(n)
    ]  # fmt: skip


def propose(course, n=2):
    reason = "Li cal més pràctica de compensació (inventat)."
    return reinforcement.propose(course.student, by=course.teacher, classes=n, reason=reason)


def test_ca_m02_18_two_sessions_only_for_the_student_and_a_charge(course):
    proposal = propose(course)
    done = reinforcement.confirm(proposal, by=course.manager, sessions_data=classes(course, 2))
    assert (done.status, done.price_cents) == (RS.CONFIRMED, 3000)
    own = Session.objects.filter(reinforcement_for=course.student)
    assert own.count() == 2
    group = Session.objects.filter(activity=course.activity, reinforcement_for__isnull=True)
    assert list(group) == [course.group]  # l'horari del grup no canvia
    charge = done.charge
    assert (charge.person_id, charge.amount_cents, charge.kind, charge.status) == (
        course.student.person_id, 3000, Charge.Kind.ENROLMENT, Charge.Status.PENDING,
    )  # fmt: skip
    assert charge.department_id == course.activity.department_id
    assert AuditEntry.objects.filter(action=reinforcement.CONFIRMED).count() == 1


def test_only_who_teaches_proposes_and_never_for_themselves(course, make_admin):  # noqa: F811
    with pytest.raises(Http404):
        reinforcement.propose(course.student, by=course.stranger, classes=1, reason="Motiu.")
    teacher_row = confirmed(course.activity, "Instructora")
    Enrolment.objects.filter(pk=teacher_row.pk).update(person=course.teacher.person)
    teacher_row.refresh_from_db()
    with pytest.raises(ValidationError):
        reinforcement.propose(teacher_row, by=course.teacher, classes=1, reason="Motiu.")
    assert not ReinforcementRequest.objects.exists()


def test_proposal_rules(course):
    for wrong in (0, 11, True):
        with pytest.raises(ValidationError):
            reinforcement.propose(course.student, by=course.teacher, classes=wrong, reason="M.")
    with pytest.raises(ValidationError, match="motiu"):
        reinforcement.propose(course.student, by=course.teacher, classes=1, reason="  ")
    propose(course)
    with pytest.raises(ValidationError, match="per resoldre"):
        propose(course)


def test_confirm_needs_one_session_per_class_and_a_price(course):
    proposal = propose(course, 2)
    with pytest.raises(ValidationError, match="2 classes"):
        reinforcement.confirm(proposal, by=course.manager, sessions_data=classes(course, 1))
    TrainingCatalogueEntry.objects.filter(pk=course.activity.catalogue_entry_id).update(
        reinforcement_price_cents=None
    )
    with pytest.raises(ValidationError, match="preu de reforç"):
        reinforcement.confirm(proposal, by=course.manager, sessions_data=classes(course, 2))
    with pytest.raises(Http404):  # AC11
        reinforcement.confirm(proposal, by=course.teacher, sessions_data=classes(course, 2))
    assert not Session.objects.filter(reinforcement_for__isnull=False).exists()


def test_a_free_reinforcement_has_no_charge(course):
    TrainingCatalogueEntry.objects.filter(pk=course.activity.catalogue_entry_id).update(
        reinforcement_price_cents=0
    )
    done = reinforcement.confirm(propose(course, 1), by=course.manager,
                                 sessions_data=classes(course, 1))  # fmt: skip
    assert (done.price_cents, done.charge) == (0, None)


def test_reject_needs_a_reason(course):
    proposal = propose(course)
    with pytest.raises(ValidationError):
        reinforcement.reject(proposal, by=course.manager, reason="")
    done = reinforcement.reject(proposal, by=course.manager, reason="No cal (inventat).")
    assert done.status == RS.REJECTED
    with pytest.raises(ValidationError, match="resolta"):
        reinforcement.reject(proposal, by=course.manager, reason="Una altra vegada.")


def test_rn_m02_22_an_unpaid_reinforcement_blocks_closing(course):
    reinforcement.confirm(propose(course, 1), by=course.manager, sessions_data=classes(course, 1))
    assert "Hi ha 1 càrrec de reforç sense pagar." in closing.closing_blockers(course.activity)


def test_rn_m02_21_reinforcement_sessions_are_not_duplicated(course):
    reinforcement.confirm(propose(course, 1), by=course.manager, sessions_data=classes(course, 1))
    copy = duplicate.duplicate(course.activity, datetime.date(2027, 9, 13), by=course.manager)
    assert copy.sessions.count() == 1


def test_the_reason_is_in_the_rgpd_export_and_erased_on_anonymising(course):
    propose(course)
    person = course.student.person
    (row,) = privacy.export(person)["propostes_de_reforc"]
    assert row["motiu"].startswith("Li cal") and row["classes"] == 2
    privacy.anonymise(person, by=course.manager)
    assert ReinforcementRequest.objects.get().reason == ""
