"""La llista d'espera a mà (T-M02-12b; RN-M02-09; AC16). Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import enrolment, states, waitlist
from apps.activities.models import Activity, Enrolment
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import BEFORE_DEADLINE, a_member, an_open_outing

pytestmark = pytest.mark.django_db

S = Enrolment.Status
NOW = BEFORE_DEADLINE
REASON = "Motiu inventat de proves"


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def full_with_queue(manager, waiting=3):
    outing = an_open_outing(manager, max_places=1)
    accounts = [a_member() for _ in range(waiting + 1)]
    rows = [
        enrolment.enrol(outing, a.person, channel="account", actor=a, now=NOW) for a in accounts
    ]
    return outing, rows[0], rows[1:]


def positions(outing):
    return list(enrolment.waitlist(outing).values_list("pk", "waitlist_position"))


def test_rn_m02_09_moving_someone_keeps_positions_without_gaps_and_is_recorded(manager):
    outing, _, (first, second, third) = full_with_queue(manager)

    moved = waitlist.move(third, 1, by=manager, reason=REASON)

    assert moved.waitlist_position == 1
    assert positions(outing) == [(third.pk, 1), (first.pk, 2), (second.pk, 3)]
    entry = AuditEntry.objects.get(action=waitlist.MOVED)
    assert (entry.old_value, entry.new_value, entry.reason) == (3, 1, REASON)


@pytest.mark.parametrize(("position", "reason"), [(1, ""), (0, REASON), (4, REASON), ("1", REASON)])
def test_moving_needs_a_reason_and_a_valid_position(manager, position, reason):
    outing, _, (first, second, third) = full_with_queue(manager)
    with pytest.raises(ValidationError):
        waitlist.move(third, position, by=manager, reason=reason)
    assert positions(outing) == [(first.pk, 1), (second.pk, 2), (third.pk, 3)]


def test_offering_a_free_place_by_hand_skips_the_order_only_with_a_reason(manager):
    outing, taken, (first, second, third) = full_with_queue(manager)
    Enrolment.objects.filter(pk=taken.pk).update(status=S.EXPIRED, payment_due_at=None)

    with pytest.raises(ValidationError, match="motiu"):
        waitlist.offer_to(second, by=manager, now=NOW)
    offered = waitlist.offer_to(second, by=manager, reason=REASON, now=NOW)

    assert (offered.status, offered.waitlist_position) == (S.OFFERED, None)
    assert offered.offer_expires_at == NOW + datetime.timedelta(hours=48)
    assert positions(outing) == [(first.pk, 1), (third.pk, 2)]
    with pytest.raises(ValidationError, match="cap plaça lliure"):
        waitlist.offer_to(first, by=manager, now=NOW)


def test_no_offer_with_registration_closed(manager):
    outing, taken, (first, *_) = full_with_queue(manager)
    Enrolment.objects.filter(pk=taken.pk).update(status=S.EXPIRED, payment_due_at=None)
    states.close_registration(outing, by=manager, now=NOW)
    with pytest.raises(enrolment.ActivityNotOpen):
        waitlist.offer_to(first, by=manager, now=NOW)


@pytest.mark.parametrize("role", ["secretary", "instructor", "board"])
def test_ac16_only_some_roles_manage_the_list(make_admin, manager, role):  # noqa: F811
    outing, _, (first, second, _third) = full_with_queue(manager)
    by = make_admin(role)
    with pytest.raises(Http404):
        waitlist.move(second, 1, by=by, reason=REASON)
    with pytest.raises(Http404):
        waitlist.offer_to(first, by=by, now=NOW)


def test_a_member_cannot_manage_the_list(manager):
    outing, _, (first, second, _third) = full_with_queue(manager)
    with pytest.raises(Http404):
        waitlist.move(second, 1, by=a_member(), reason=REASON)
    assert Activity.objects.get(pk=outing.pk).status == Activity.Status.OPEN
