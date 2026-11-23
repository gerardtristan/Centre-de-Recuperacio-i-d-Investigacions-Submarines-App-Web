"""T-M03-22b: cost d'ús del material del club per tipus (VC-28; RN-M03-08 i RN-AJ-04). Només dades
inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities.tests.test_attendance import enrolled
from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, usage_rates
from apps.equipment.costs import usage_cost_on

from .test_assignments import JUNE, jacket, keeper, kind, manager, outing  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
R = Role.Code
TODAY = JUNE - datetime.timedelta(days=30)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    account = make_admin(R.TREASURER)
    account.notification_email = "tresor@example.org"
    account.save()
    return account


def change(by, cents, valid_from=TODAY, note="Cost revisat (inventat)."):
    return usage_rates.set_rate(
        kind("Jaquet"), cost_per_day_cents=cents, valid_from=valid_from, note=note, by=by,
        today=TODAY,
    )  # fmt: skip


def test_vc_28_the_treasurer_changes_it_with_date_note_log_and_notice(treasurer):
    change(treasurer, 150)
    later = change(treasurer, 200, valid_from=JUNE)
    assert usage_cost_on(kind("Jaquet"), TODAY) == 150
    assert usage_cost_on(kind("Jaquet"), JUNE) == 200
    entry = AuditEntry.objects.filter(action=usage_rates.CHANGED).latest("pk")
    assert (entry.old_value, entry.new_value) == (150, 200)
    assert entry.reason == "Cost revisat (inventat)."
    assert entry.target_id == str(later.pk)
    emails = OutgoingEmail.objects.filter(to_address="tresor@example.org")
    assert emails.count() == 2


def test_out_of_range_past_dates_and_no_note_are_rejected(treasurer):
    for kwargs in (
        {"cents": -1},
        {"cents": 100, "valid_from": TODAY - datetime.timedelta(days=1)},
        {"cents": 100, "note": " "},
    ):
        with pytest.raises(ValidationError):
            change(treasurer, **kwargs)
    change(treasurer, 100)
    with pytest.raises(ValidationError):  # el mateix dia, ja n'hi ha un
        change(treasurer, 120)


def test_without_the_permission_not_found(keeper):  # noqa: F811
    with pytest.raises(Http404):
        change(keeper, 100)


def test_a_change_does_not_touch_assignments_already_made(treasurer, manager, keeper):  # noqa: F811
    change(treasurer, 100)
    before = assignments.assign_club(enrolled(outing(manager)), jacket(keeper), by=keeper)
    change(treasurer, 300, valid_from=JUNE)
    after = assignments.assign_club(enrolled(outing(manager), "B"), jacket(keeper), by=keeper)
    before.refresh_from_db()
    assert (before.cost_cents, after.cost_cents) == (200, 600)  # dos dies


def test_who_sees_the_rates(treasurer, keeper, make_admin):  # noqa: F811
    change(treasurer, 100, valid_from=JUNE)
    rows = {r["type"].name: r for r in usage_rates.rates(viewer=treasurer, today=TODAY)}
    assert rows["Jaquet"]["cents"] == 0 and rows["Jaquet"]["upcoming"].cost_per_day_cents == 100
    assert usage_rates.rates(viewer=keeper, today=TODAY)
    with pytest.raises(Http404):
        usage_rates.rates(viewer=make_admin(R.INSTRUCTOR), today=TODAY)
