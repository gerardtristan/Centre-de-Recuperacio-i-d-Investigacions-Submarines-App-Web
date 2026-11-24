"""Ordre i blocs amagats per compte (T-M08-12; P-M08-D; CA-M08-13; RN-M08-06; P-490)."""

import pytest
from django.http import Http404

from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.dashboard import layout
from apps.dashboard.models import DashboardLayout

pytestmark = pytest.mark.django_db
R = Role.Code
BLOCKS = {"active_members": 1, "new_members": 2, "unpaid_members": 3, "free_places": 4}


def test_ca_m08_13_one_account_reorders_and_hides_and_the_other_does_not_change(make_admin):  # noqa: F811
    treasurer, president = make_admin(R.TREASURER), make_admin(R.PRESIDENT)
    layout.save(treasurer, ["unpaid_members", "free_places"], ["new_members"])
    assert list(layout.arrange(treasurer, BLOCKS)) == [
        "unpaid_members", "free_places", "active_members",
    ]  # fmt: skip
    assert list(layout.arrange(president, BLOCKS)) == list(BLOCKS)
    assert layout.arrange(treasurer, BLOCKS)["unpaid_members"] == 3


def test_saving_again_replaces_the_preference_of_the_same_account(make_admin):  # noqa: F811
    treasurer = make_admin(R.TREASURER)
    layout.save(treasurer, ["free_places"], ["new_members"])
    layout.save(treasurer, ["free_places", "free_places", "active_members"], [])
    saved = DashboardLayout.objects.get(account=treasurer)
    assert (saved.order, saved.hidden) == (["free_places", "active_members"], [])
    assert DashboardLayout.objects.count() == 1


@pytest.mark.parametrize(
    "order, hidden",
    [(["no_such_block"], []), ([], ["no_such_block"]), ("active_members", []), ([1], [])],
)
def test_unknown_or_malformed_codes_are_rejected(make_admin, order, hidden):  # noqa: F811
    with pytest.raises(Http404):
        layout.save(make_admin(R.TREASURER), order, hidden)
    assert not DashboardLayout.objects.exists()


def test_ca_m08_13_a_block_the_role_cannot_see_is_rejected(make_admin):  # noqa: F811
    """Sense DB1 (l'instructor), cap bloc: una petició forçada no desa res."""
    with pytest.raises(Http404):
        layout.save(make_admin(R.INSTRUCTOR), ["active_members"], [])
    assert not DashboardLayout.objects.exists()


def test_blocks_missing_from_the_panel_are_skipped(make_admin):  # noqa: F811
    treasurer = make_admin(R.TREASURER)
    layout.save(treasurer, ["treasury_balances", "free_places"], ["conference_attendees"])
    assert list(layout.arrange(treasurer, BLOCKS))[0] == "free_places"


def test_without_db1_even_an_empty_layout_is_rejected(make_admin):  # noqa: F811
    with pytest.raises(Http404):
        layout.save(make_admin(R.INSTRUCTOR), [], [])
    assert not DashboardLayout.objects.exists()
