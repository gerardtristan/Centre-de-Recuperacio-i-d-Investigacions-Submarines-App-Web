"""`grants.granted_by_department` per al dashboard (T-M08-06; M09-ajuts-8). Dades inventades."""

from datetime import date

import pytest

from apps.core.models import Department
from apps.grants import totals
from apps.grants.models import GrantApplication

pytestmark = pytest.mark.django_db
S = GrantApplication.Status


def resolved(call, treasurer, department, status, cents, on):
    return GrantApplication.objects.create(
        call=call, responsible=treasurer.person, department=department, created_by=treasurer,
        status=status, submitted_on=date(2027, 1, 10), submission_ref="RE-1",
        amount_requested_cents=cents, amount_granted_cents=cents, resolved_on=on,
        justified_on=on if status == S.JUSTIFIED else None,
    )  # fmt: skip


def test_granted_by_department_in_the_period(call, treasurer, general):
    other = Department.objects.create(name="Departament inventat")
    resolved(call, treasurer, general, S.GRANTED, 100000, date(2027, 3, 1))
    resolved(call, treasurer, general, S.JUSTIFIED, 2345, date(2027, 3, 31))
    resolved(call, treasurer, other, S.CLOSED, 500, date(2027, 1, 1))
    resolved(call, treasurer, other, S.DENIED, 999, date(2027, 2, 1))  # denegada: no
    resolved(call, treasurer, other, S.GRANTED, 7000, date(2027, 4, 1))  # fora del període
    assert totals.granted_by_department(date(2027, 1, 1), date(2027, 3, 31)) == {
        "Departament inventat": 500,
        "General": 102345,
    }
