"""T-DX-106 (Gastos al 09): el marge d'una activitat porta l'anell de Gastos amb on van els costos
(cada categoria i el cost de material), calculat al servidor. Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities.tests.helpers import an_outing
from apps.core.models import Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.expenses.models import ExpenseCategory
from apps.margins.templatetags.gastos import anell_gastos

from .test_views import manager, page  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db


def test_the_ring_shares_add_up_and_groups_the_rest():
    ring = anell_gastos([("A", 5000), ("B", 3000), ("C", 1000), ("D", 500), ("E", 300),
                         ("F", 200), ("Buit", 0)], "Costos")  # fmt: skip
    names = [row["name"] for row in ring["rows"]]
    assert names == ["A", "B", "C", "D", "Altres"]  # 5 colors; la resta, junta
    assert [row["share"] for row in ring["rows"]] == [50, 30, 10, 5, 5]
    assert ring["total"] == "100,00 €" and ring["rows"][0]["offset"] == "-0.00"
    assert anell_gastos([("A", 0)], "Costos")["rows"] == []  # sense costos, cap anell


def test_the_margin_page_shows_where_the_costs_go(login_as, make_admin, manager):  # noqa: F811
    activity = an_outing(manager)
    client = login_as(make_admin(Role.Code.TREASURER), AREA_ADMIN)
    boat = ExpenseCategory.objects.get(name="Embarcació")
    client.post(
        reverse("administration:activity_margin_planned", args=[activity.pk]),
        {"category": boat.pk, "amount": "250,00"},
    )
    html = main_of(client.get(page(activity)).content.decode())
    assert 'class="gastos-anell"' in html and "Embarcació · " in html
