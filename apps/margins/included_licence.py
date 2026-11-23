"""Cost previst de la primera llicència inclosa al curs (RN-M02-59; CA-M02-60; T-M02-51b).

El 02 envia `activities.extensions.first_licence_included` quan es crea una llicència inclosa (el
02 no importa el 09); `on_first_licence_included` hi suma el preu de la federació (la versió
vigent el dia d'inici) al cost previst de l'activitat, a la categoria de despesa de l'ajust VC-60,
i així compta al marge previst (RN-M09-06). És una acció del sistema en emetre el certificat: no
demana el permís MG5 de la pantalla. Si l'activitat ja és tancada o VC-60 no té cap categoria, no
toca res i ho deixa al registre (`filings.COST_NOT_PLANNED`), perquè la llista avisi el tresorer
[A validar: tresorer].
"""

from django.db import transaction
from django.utils.translation import gettext as _

from apps.activities.models import Activity
from apps.core import audit, business_settings
from apps.expenses.models import ExpenseCategory

from .models import PlannedCost
from .planned import PLANNED_COST_SET, _check_low_margin

CATEGORY_KEY = "activities.included_licence_expense_category"  # VC-60


@transaction.atomic
def add_included_licence_cost(activity, amount_cents: int, *, actor, note="") -> bool:
    """Suma `amount_cents` (enter, zero o més) al cost previst de la categoria de VC-60."""
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents < 0:
        raise ValueError("amount_cents ha de ser un enter de cèntims, zero o més")
    name = business_settings.get(CATEGORY_KEY)
    category = ExpenseCategory.objects.filter(name=name, active=True).first() if name else None
    activity = Activity.objects.select_for_update().get(pk=activity.pk)
    if category is None or activity.status == Activity.Status.CLOSED:
        return False
    planned = PlannedCost.objects.select_for_update().filter(activity=activity, category=category)
    planned = planned.first()
    old = planned.amount_cents if planned else None
    if planned is None:
        planned = PlannedCost(
            activity=activity, category=category, created_by=actor, amount_cents=0
        )
    planned.amount_cents += amount_cents
    planned.note = planned.note or note[:200]
    planned.save()
    audit.record(
        PLANNED_COST_SET, actor=actor, target=planned, field="amount_cents", old=old,
        new=planned.amount_cents,
        details={"activity": activity.pk, "category": category.name, "reason": "included_licence"},
    )  # fmt: skip
    _check_low_margin(activity)
    return True


def on_first_licence_included(sender, *, activity, filing, licence_type, by, **kwargs) -> None:
    from apps.activities.filings import COST_NOT_PLANNED
    from apps.licences.prices import applicable

    price = applicable(licence_type, activity.starts_on)
    cost = price.federation_cost_cents if price else 0
    note = _("Primera llicència inclosa: %(name)s") % {"name": licence_type.name}
    if not add_included_licence_cost(activity, cost, actor=by, note=note):
        audit.record(COST_NOT_PLANNED, actor=by, target=filing, details={"cents": cost})
