"""T-M09-09: costos previstos per activitat i registre de canvis. Només dades inventades."""

import pytest
from django.http import Http404

from apps.activities.models import Activity, Place
from apps.activities.tests.helpers import outing_data
from apps.core.models import AuditEntry
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses.models import ExpenseCategory
from apps.expenses.services import ExpenseRejected
from apps.margins import planned
from apps.margins.models import PlannedCost

pytestmark = pytest.mark.django_db


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


@pytest.fixture
def activity(treasurer):
    place = Place.objects.create(name="Port inventat", created_by=treasurer)
    return Activity.objects.create(**outing_data(place))


def boat():
    return ExpenseCategory.objects.get(name="Embarcació")


def test_un_cost_previst_per_categoria_que_es_canvia_amb_registre(activity, treasurer):
    first = planned.set_planned_cost(activity, boat(), 25000, by=treasurer, note="Pressupost")
    again = planned.set_planned_cost(activity, boat(), 26000, by=treasurer)
    assert first.pk == again.pk
    assert PlannedCost.objects.get().amount_cents == 26000
    assert str(again) == "Embarcació: 26000 c"
    values = list(
        AuditEntry.objects.filter(action=planned.PLANNED_COST_SET)
        .order_by("pk")
        .values_list("old_value", "new_value")
    )
    assert values == [(None, 25000), (25000, 26000)]


def test_treure_un_cost_previst_queda_al_registre(activity, treasurer):
    cost = planned.set_planned_cost(activity, boat(), 25000, by=treasurer)
    planned.remove_planned_cost(cost, by=treasurer)
    assert not PlannedCost.objects.exists()
    entry = AuditEntry.objects.get(action=planned.PLANNED_COST_REMOVED)
    assert entry.old_value == 25000


@pytest.mark.parametrize(("amount", "note"), [(-1, ""), (1.5, ""), (True, ""), (100, "x" * 201)])
def test_dades_que_no_valen(activity, treasurer, amount, note):
    with pytest.raises(ExpenseRejected):
        planned.set_planned_cost(activity, boat(), amount, by=treasurer, note=note)


def test_una_activitat_tancada_no_canvia_els_costos_previstos(activity, treasurer):
    cost = planned.set_planned_cost(activity, boat(), 25000, by=treasurer)
    Activity.objects.filter(pk=activity.pk).update(status=Activity.Status.CLOSED)
    with pytest.raises(ExpenseRejected):
        planned.set_planned_cost(activity, boat(), 1, by=treasurer)
    with pytest.raises(ExpenseRejected):
        planned.remove_planned_cost(cost, by=treasurer)


@pytest.mark.parametrize("role", ["secretary", "board", "president", "courses_manager", None])
def test_sense_mg5_amb_abast_valid_no_es_toquen(activity, make_admin, role):  # noqa: F811
    # El responsable de cursos i sortides té «les seves activitats»: fins que el 02 en registri
    # la comprovació per objecte, no deixa passar cap activitat.
    with pytest.raises(Http404):
        planned.set_planned_cost(activity, boat(), 1, by=make_admin(*([role] if role else [])))


def test_l_administrador_te_mg5(activity, make_admin):  # noqa: F811
    assert planned.set_planned_cost(activity, boat(), 1, by=make_admin("administrator")).pk
