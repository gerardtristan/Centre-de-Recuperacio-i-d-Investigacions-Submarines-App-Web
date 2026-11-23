"""T-DX-90 (revisió de DISSENY de les pantalles del 09): al marge d'una activitat, la categoria del
cost previst diu «Tria una categoria» i no «---------», i l'import previst va alineat a la dreta
(`cel-import`, regla D14). Només dades inventades."""

from apps.accounts.security import AREA_ADMIN
from apps.activities.tests.helpers import an_outing
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.expenses.models import ExpenseCategory
from apps.margins.models import PlannedCost

from .test_views import R, manager, page  # noqa: F401 (fixture)


def test_planned_costs_read_well(login_as, make_admin, manager):  # noqa: F811
    activity = an_outing(manager)
    PlannedCost.objects.create(
        activity=activity, category=ExpenseCategory.objects.get(name="Embarcació"),
        amount_cents=25000, created_by=manager,
    )  # fmt: skip
    client = login_as(make_admin(R.TREASURER), AREA_ADMIN)
    html = main_of(client.get(page(activity)).content.decode())
    assert "---------" not in html and "Tria una categoria" in html
    assert '<th scope="col" class="cel-import">Import previst</th>' in html
    assert 'class="cel-import"><span class="import">250,00 €</span>' in html
