"""Repartiment d'una despesa entre activitats (T-M09-07; P-M09-B; RN-M09-10; CA-M09-04, 05 i 06;
MG3). Cap altra app escriu aquests models.

- **Per participants:** proporcional als assistents de cada activitat; sense llista, a les
  inscripcions confirmades (`activities.attendance.participants`; [A validar: tresorer, S-M09-02]).
- **A parts iguals** o **a mà** (el tresorer corregeix la proposta).
- **Arrodoniment (VT-05):** cada part a la baixa i els cèntims que sobren, un a un, a les
  activitats amb més participants; en empat, la més antiga (data d'inici i, després, la creada
  abans).
- La suma no passa mai de l'import (`AllocationExceedsAmount`); el que no es reparteix queda al
  departament de la despesa, sense activitat.
- Tornar a repartir substitueix el repartiment anterior; el registre guarda l'anterior i el nou.
"""

from django.db import transaction
from django.db.models import Sum
from django.utils.translation import gettext as _

from apps.activities import attendance
from apps.core import audit

from .models import Expense, ExpenseAllocation
from .services import ExpenseRejected, _require

ALLOCATE = "expenses.allocate"  # MG3
ALLOCATED = "expenses.expense_allocated"
M = ExpenseAllocation.Method


class AllocationExceedsAmount(ExpenseRejected):
    """La suma dels repartiments passa de l'import de la despesa (CA-M09-06)."""


def split(amount_cents: int, weights, order) -> list[int]:
    """Reparteix `amount_cents` en parts proporcionals a `weights` (enters ≥ 0, suma > 0). Cada
    part a la baixa; els cèntims que sobren, un a un, segons `order` (índexs per prioritat)."""
    total = sum(weights)
    parts = [amount_cents * w // total for w in weights]
    for i in order[: amount_cents - sum(parts)]:
        parts[i] += 1
    return parts


def propose(expense, activities, method) -> dict:
    """Els imports que proposa el sistema per participants o a parts iguals (P-M09-B pas 2)."""
    activities = list(dict.fromkeys(activities))
    if not activities:
        raise ExpenseRejected(_("Cal triar almenys una activitat."))
    people = [attendance.participants(a) for a in activities]
    if method == M.PARTICIPANTS:
        weights = people
        if not sum(weights):
            raise ExpenseRejected(_("Cap d'aquestes activitats no té participants."))
    elif method == M.EQUAL:
        weights = [1] * len(activities)
    else:
        raise ExpenseRejected(_("Criteri de repartiment desconegut."))
    order = sorted(
        range(len(activities)),
        key=lambda i: (-people[i], activities[i].starts_on, activities[i].pk),
    )
    return dict(zip(activities, split(expense.amount_cents, weights, order), strict=True))


@transaction.atomic
def allocate(expense, activities, method, *, by, amounts=None) -> list[ExpenseAllocation]:
    """`expenses.allocate` (M09-8). Per participants o a parts iguals, els imports de `propose`;
    a mà, `amounts` ({activitat: cèntims}). Substitueix el repartiment anterior."""
    _require(by, ALLOCATE)
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.status == Expense.Status.ANNULLED:
        raise ExpenseRejected(_("Una despesa anul·lada no es reparteix."))
    if method == M.MANUAL:
        parts = dict(amounts or {})
        if not parts:
            raise ExpenseRejected(_("Cal triar almenys una activitat."))
        if any(isinstance(v, bool) or not isinstance(v, int) for v in parts.values()):
            raise ExpenseRejected(_("Cada import ha de ser un enter de cèntims."))
    else:
        parts = propose(expense, activities, method)
    if any(v <= 0 for v in parts.values()):
        raise ExpenseRejected(_("Cada activitat ha de rebre més de zero cèntims."))
    if sum(parts.values()) > expense.amount_cents:
        raise AllocationExceedsAmount(_("La suma dels repartiments passa de l'import."))
    current = ExpenseAllocation.objects.filter(expense=expense)
    old = {str(a.activity_id): a.amount_cents for a in current}
    current.delete()
    rows = ExpenseAllocation.objects.bulk_create(
        ExpenseAllocation(
            expense=expense, activity=activity, amount_cents=cents, method=method, created_by=by
        )
        for activity, cents in parts.items()
    )
    audit.record(
        ALLOCATED,
        actor=by,
        target=expense,
        field="allocations",
        old=old or None,
        new={str(a.pk): cents for a, cents in parts.items()},
        details={"method": method},
    )
    return rows


def allocated_costs(activity) -> dict[str, int]:
    """Categoria → cèntims repartits a l'activitat (costos reals per al marge, RN-M09-04). Les
    despeses anul·lades no compten."""
    rows = (
        ExpenseAllocation.objects.filter(activity=activity)
        .exclude(expense__status=Expense.Status.ANNULLED)
        .values_list("expense__category__name")
        .annotate(total=Sum("amount_cents"))
    )
    return dict(rows)
