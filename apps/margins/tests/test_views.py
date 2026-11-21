"""Pantalla del marge d'una activitat (P-M09-D; MG5, MG6 i MG7). Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities.models import Activity, Enrolment
from apps.activities.tests.helpers import a_person, an_outing
from apps.activities.tests.test_attendance import enrolled, opened
from apps.core.models import Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.expenses.models import ExpenseCategory
from apps.margins.models import MarginSnapshot, PlannedCost

pytestmark = pytest.mark.django_db
R = Role.Code


def page(activity):
    return reverse("administration:activity_margin", args=[activity.pk])


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(R.COURSES_MANAGER)


def test_the_treasurer_sees_the_forecast_and_sets_a_planned_cost(login_as, make_admin, manager):  # noqa: F811
    activity = an_outing(manager)
    client = login_as(make_admin(R.TREASURER), AREA_ADMIN)
    html = main_of(client.get(page(activity)).content.decode())
    assert "Marge previst" in html and "Desa el cost previst" in html and "Tanca l" not in html
    boat = ExpenseCategory.objects.get(name="Embarcació")
    response = client.post(
        reverse("administration:activity_margin_planned", args=[activity.pk]),
        {"category": boat.pk, "amount": "250,00"}, follow=True,
    )  # fmt: skip
    assert PlannedCost.objects.get(activity=activity).amount_cents == 25000
    assert "Cost previst desat." in response.content.decode()


def test_closing_shows_the_reasons_then_freezes_the_margin(login_as, make_admin, manager):  # noqa: F811
    activity = opened(an_outing(manager), Activity.Status.DONE)
    pending = enrolled(activity, "Pendent", Enrolment.Status.PENDING_PAYMENT)
    client = login_as(make_admin(R.TREASURER), AREA_ADMIN)
    html = main_of(client.get(page(activity)).content.decode())
    assert "Encara no es pot tancar" in html and "1 inscripció pendent de pagament" in html
    assert "Marge real (en tancar-la)" in html
    close = reverse("administration:activity_margin_close", args=[activity.pk])
    assert "pendent de pagament" in client.post(close, follow=True).content.decode()
    assert not MarginSnapshot.objects.exists()
    Enrolment.objects.filter(pk=pending.pk).update(status="expired")
    response = client.post(close, follow=True)
    html = main_of(response.content.decode())
    assert "Marge congelat" in html and "queda congelat" in html
    assert MarginSnapshot.objects.filter(activity=activity).exists()


def test_by_object_and_by_role(login_as, make_admin, manager):  # noqa: F811
    person = a_person("Responsable inventada")
    responsible = make_admin(R.COURSES_MANAGER, person=person)
    own, other = an_outing(manager, responsible=person), an_outing(manager)
    client = login_as(responsible, AREA_ADMIN)
    assert "Desa el cost previst" in main_of(client.get(page(own)).content.decode())
    assert client.get(page(other)).status_code == 404
    board = login_as(make_admin(R.BOARD), AREA_ADMIN)
    html = main_of(board.get(page(other)).content.decode())
    assert "Marge previst" in html and "Desa el cost previst" not in html  # consulta
    assert login_as(make_admin(R.SECRETARY), AREA_ADMIN).get(page(own)).status_code == 404
