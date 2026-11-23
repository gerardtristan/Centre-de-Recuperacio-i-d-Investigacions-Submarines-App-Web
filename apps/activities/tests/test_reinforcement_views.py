"""Pantalles de les classes de reforç (T-M02-18b; P-M02-F passos 2 a 4; CA-M02-18; AC10b i AC11).
Només dades inventades."""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_ADMIN
from apps.activities import permissions
from apps.activities.models import ReinforcementRequest, Session, TrainingCatalogueEntry
from apps.core.models import AuditEntry, Charge, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import a_place
from .test_attendance import manager  # noqa: F401 (fixtures)
from .test_attendance_views import today_course  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
R = Role.Code


def propose_url(course):
    args = [course.activity.pk, course.student.pk]
    return reverse("administration:reinforcement_propose", args=args)


def list_url(course):
    return reverse("administration:reinforcement_list", args=[course.activity.pk])


def sheet_url(course):
    return reverse("administration:assessment_sheet", args=[course.activity.pk, course.first.pk])


def test_the_instructor_proposes_from_the_assessment_sheet(login_as, today_course):  # noqa: F811
    Session.objects.filter(pk=today_course.first.pk).update(is_practice=True)
    client = login_as(today_course.own, AREA_ADMIN)
    assert propose_url(today_course) in main_of(
        client.get(sheet_url(today_course)).content.decode()
    )
    html = main_of(client.get(propose_url(today_course)).content.decode())
    assert "Sense dades de salut" in html
    response = client.post(propose_url(today_course), {"classes": "2", "motiu": ""})
    assert "Cal explicar el motiu" in response.content.decode()
    response = client.post(
        propose_url(today_course), {"classes": "2", "motiu": "Ha de repetir la flotabilitat."}
    )
    assert response.status_code == 303
    proposal = ReinforcementRequest.objects.get()
    assert (proposal.classes, proposal.status) == (2, "proposed")
    page = main_of(client.get(list_url(today_course)).content.decode())
    assert "Ha de repetir la flotabilitat." in page and "Confirma el reforç" not in page


def test_ca_m02_18_the_manager_confirms_with_sessions_and_charge(
    login_as,
    today_course,  # noqa: F811
    manager,  # noqa: F811
):
    TrainingCatalogueEntry.objects.filter(pk=today_course.activity.catalogue_entry_id).update(
        reinforcement_price_cents=3000
    )
    ReinforcementRequest.objects.create(
        enrolment=today_course.student, proposed_by=today_course.own, classes=1,
        reason="Repetir la flotabilitat (inventat).", status="proposed",
    )  # fmt: skip
    proposal = ReinforcementRequest.objects.get()
    client = login_as(manager, AREA_ADMIN)
    assert "Confirma el reforç" in main_of(client.get(list_url(today_course)).content.decode())
    day = timezone.localdate() + datetime.timedelta(days=7)
    data = {
        "proposta": proposal.pk, "confirma": "1", "dia-1": day.isoformat(), "inici-1": "10:00",
        "final-1": "11:00", "classe-1": "pool", "lloc-1": a_place(manager, prices=None).pk,
        "instructor-1": today_course.own.person.pk,
    }  # fmt: skip
    response = client.post(list_url(today_course), data, follow=True)
    assert "Reforç confirmat" in response.content.decode()
    proposal.refresh_from_db()
    assert proposal.status == "confirmed"
    session = Session.objects.get(reinforcement_for=today_course.student)
    assert list(session.instructors.all()) == [today_course.own.person]
    assert Charge.objects.get(pk=proposal.charge_id).amount_cents == 3000


def test_reject_needs_a_reason_and_missing_fields_are_reported(
    login_as,
    today_course,  # noqa: F811
    manager,  # noqa: F811
):
    proposal = ReinforcementRequest.objects.create(
        enrolment=today_course.student, proposed_by=today_course.own, classes=1,
        reason="Motiu (inventat).", status="proposed",
    )  # fmt: skip
    client = login_as(manager, AREA_ADMIN)
    response = client.post(
        list_url(today_course), {"proposta": proposal.pk, "confirma": "1"}, follow=True
    )
    assert "Omple la data" in response.content.decode()
    data = {"proposta": proposal.pk, "rebutja": "1", "motiu": ""}
    response = client.post(list_url(today_course), data, follow=True)
    assert "cal un motiu" in response.content.decode()
    client.post(list_url(today_course), {**data, "motiu": "Ja està preparat (inventat)."})
    proposal.refresh_from_db()
    assert proposal.status == "rejected"


def test_without_permission_not_found(login_as, today_course, make_admin):  # noqa: F811
    stranger = make_admin(R.INSTRUCTOR)  # no fa classe en aquest curs
    client = login_as(stranger, AREA_ADMIN)
    assert client.get(propose_url(today_course)).status_code == 404
    assert client.get(list_url(today_course)).status_code == 404
    assert AuditEntry.objects.filter(action=permissions.OUT_OF_SCOPE).count() == 2
    proposal = ReinforcementRequest.objects.create(
        enrolment=today_course.student, proposed_by=today_course.own, classes=1,
        reason="Motiu (inventat).", status="proposed",
    )  # fmt: skip
    # L'instructor del curs veu la llista, però no pot decidir.
    own = login_as(today_course.own, AREA_ADMIN)
    response = own.post(
        list_url(today_course), {"proposta": proposal.pk, "rebutja": "1", "motiu": "x"}
    )
    assert response.status_code == 404
    proposal.refresh_from_db()
    assert proposal.status == "proposed"
    assert (
        login_as(make_admin(R.SECRETARY), AREA_ADMIN).get(list_url(today_course)).status_code == 404
    )
