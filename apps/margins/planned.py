"""Costos previstos d'una activitat (T-M09-09; M09-6; RN-M09-06). Un per categoria; es canvien
mentre l'activitat no és tancada i cada canvi va al registre amb el valor anterior. Desar-los
comprova el marge baix (T-M09-13)."""

from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from apps.activities.models import Activity
from apps.core import audit
from apps.core.permissions import has_perm
from apps.expenses.services import ExpenseRejected

from .models import PlannedCost

PLANNED_COSTS = "expenses.planned_costs"  # MG5
PLANNED_COST_SET = "margins.planned_cost_set"
PLANNED_COST_REMOVED = "margins.planned_cost_removed"


def _editable(activity, by) -> Activity:
    # MG5: el responsable de cursos i sortides, només les seves activitats (abast del 02).
    if not has_perm(by, PLANNED_COSTS, activity, write=True):
        raise Http404
    activity = Activity.objects.select_for_update().get(pk=activity.pk)
    if activity.status == Activity.Status.CLOSED:
        raise ExpenseRejected(_("L'activitat ja és tancada: els costos previstos no canvien."))
    return activity


@transaction.atomic
def set_planned_cost(activity, category, amount_cents, *, by, note="") -> PlannedCost:
    """Crea o canvia el cost previst d'una categoria."""
    activity = _editable(activity, by)
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents < 0:
        raise ExpenseRejected(_("L'import previst ha de ser un enter de cèntims, zero o més."))
    note = (note or "").strip()
    if len(note) > 200:
        raise ExpenseRejected(_("La nota té 200 caràcters com a màxim."))
    planned = PlannedCost.objects.select_for_update().filter(activity=activity, category=category)
    planned = planned.first()
    old = planned.amount_cents if planned else None
    if planned is None:
        planned = PlannedCost(activity=activity, category=category, created_by=by)
    planned.amount_cents, planned.note = amount_cents, note
    planned.save()
    audit.record(
        PLANNED_COST_SET,
        actor=by,
        target=planned,
        field="amount_cents",
        old=old,
        new=amount_cents,
        details={"activity": activity.pk, "category": category.name, "note": note},
    )
    _check_low_margin(activity)
    return planned


@transaction.atomic
def remove_planned_cost(planned, *, by) -> None:
    activity = _editable(planned.activity, by)
    planned = PlannedCost.objects.select_for_update().get(pk=planned.pk)
    audit.record(
        PLANNED_COST_REMOVED,
        actor=by,
        target=planned,
        field="amount_cents",
        old=planned.amount_cents,
        details={"activity": activity.pk, "category": planned.category.name},
    )
    planned.delete()
    _check_low_margin(activity)


def _check_low_margin(activity) -> None:
    from .alerts import check_forecast  # `alerts` fa servir `services`, que importa aquest mòdul

    check_forecast(activity)


def planned_costs(activity) -> dict[str, int]:
    """Categoria → import previst, per al marge previst (RN-M09-06)."""
    return dict(
        PlannedCost.objects.filter(activity=activity).values_list("category__name", "amount_cents")
    )
