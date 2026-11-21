"""T-M09-11, part prevista: marge previst d'una activitat amb els costos previstos i el cost de
material previst del 02 (RN-M09-06; RN-M02-43). Només dades inventades."""

import pytest

from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses.models import ExpenseCategory
from apps.margins import calc, planned, services
from apps.margins.tests.test_planned import activity, boat, treasurer  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db


def test_marge_previst_amb_els_costos_previstos_i_el_material_previst(
    activity,  # noqa: F811
    treasurer,  # noqa: F811
    monkeypatch,
):
    planned.set_planned_cost(activity, boat(), 25000, by=treasurer)
    planned.set_planned_cost(
        activity, ExpenseCategory.objects.get(name="Aire"), 12000, by=treasurer
    )
    activity.material_cost_cents = 350
    monkeypatch.setattr(services, "_live_enrolments", lambda a: (8 * 4500, 8))

    margin = services.activity_margin(activity)

    assert margin.kind == calc.FORECAST
    assert margin.breakdown["costs_by_category"] == {"Embarcació": 25000, "Aire": 12000}
    assert (margin.material_cost_cents, margin.breakdown["material_source"]) == (2800, "planned")
    assert margin.margin_cents == 36000 - 25000 - 12000 - 2800


def test_sense_inscripcions_ni_cost_de_material_el_previst_son_els_costos(activity, treasurer):  # noqa: F811
    planned.set_planned_cost(activity, boat(), 25000, by=treasurer)
    margin = services.activity_margin(activity)
    assert (margin.margin_cents, margin.material_cost_cents, margin.margin_pct_tenths) == (
        -25000,
        0,
        None,
    )


def test_el_marge_real_encara_no_hi_es(activity):  # noqa: F811
    with pytest.raises(NotImplementedError):
        services.activity_margin(activity, calc.REAL)
