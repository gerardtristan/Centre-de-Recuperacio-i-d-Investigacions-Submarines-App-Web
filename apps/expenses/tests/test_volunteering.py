"""T-M09-17: hores de voluntariat per funció, mai per persona (RN-M09-21). Dades inventades."""

from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.core.models import AuditEntry, Department
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import volunteering
from apps.expenses.models import VolunteerHours
from apps.expenses.services import ExpenseRejected

pytestmark = pytest.mark.django_db


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


def record(by, **extra):
    fields = {
        "date": date(2026, 10, 15),
        "hours": "3.5",
        "role_label": "Patró de l'embarcació",
        "department": Department.objects.get(name="General"),
        "by": by,
    }
    return volunteering.record_volunteer_hours(**{**fields, **extra})


def test_hores_per_funcio_sense_cap_camp_de_persona(treasurer):
    entry = record(treasurer, description="Sortida a les Medes")
    assert (entry.hours, entry.role_label, str(entry)) == (
        Decimal("3.50"),
        "Patró de l'embarcació",
        "Patró de l'embarcació: 3.50 h",
    )
    # RN-M09-21: cap camp no apunta a una persona (només qui ho registra).
    person_fields = {
        f.name for f in VolunteerHours._meta.fields if f.related_model and f.name != "recorded_by"
    }
    assert person_fields == {"department"}
    assert AuditEntry.objects.get(action=volunteering.VOLUNTEER_HOURS_RECORDED).details == {
        "hours": "3.50",
        "department": "General",
    }


@pytest.mark.parametrize(
    "extra",
    [
        {"hours": 0},
        {"hours": "-1"},
        {"hours": "1000"},
        {"hours": "0.001"},
        {"hours": "tres"},
        {"hours": "Infinity"},
        {"hours": "NaN"},
        {"hours": "1e40"},
        {"role_label": "  "},
        {"role_label": "x" * 81},
        {"description": "x" * 201},
    ],
)
def test_dades_que_no_valen(treasurer, extra):
    with pytest.raises(ExpenseRejected):
        record(treasurer, **extra)
    assert not VolunteerHours.objects.exists()


def test_departament_inactiu(treasurer):
    closed = Department.objects.create(name="Departament tancat", active=False)
    with pytest.raises(ExpenseRejected):
        record(treasurer, department=closed)


@pytest.mark.parametrize("role", ["president", "secretary", "board", None])
def test_sense_mg13_no_es_registren(make_admin, role):  # noqa: F811
    with pytest.raises(Http404):
        record(make_admin(*([role] if role else [])))


def test_la_base_de_dades_rebutja_hores_a_zero(treasurer):
    entry = record(treasurer)
    with pytest.raises(IntegrityError), transaction.atomic():
        VolunteerHours.objects.filter(pk=entry.pk).update(hours=0)
