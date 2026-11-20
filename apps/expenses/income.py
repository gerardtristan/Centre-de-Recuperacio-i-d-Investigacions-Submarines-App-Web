"""Altres ingressos: ajut, patrocini, donatiu (T-M09-08; M09-6, M09-8; RN-M09-08). El moviment
`other_income` el crea la 04 (`treasury.record_other_income`); el 09 no escriu als seus models."""

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.core import audit
from apps.treasury import services as treasury

from .models import OtherIncome
from .services import ExpenseRejected, _require

OTHER_INCOME = "expenses.other_income"  # MG4
OTHER_INCOME_RECORDED = "expenses.other_income_recorded"


@transaction.atomic
def record_other_income(
    *,
    kind,
    payer,
    amount_cents,
    account,
    value_date,
    department,
    by,
    cost_centre=None,
    document_file=None,
) -> OtherIncome:
    """`expenses.record_other_income` (M09-8). Un ajut porta la resolució (`document_file`). Dins
    un període tancat, la 04 respon `PeriodClosed` i no es desa res (RN-T30)."""
    _require(by, OTHER_INCOME)
    payer = (payer or "").strip()
    if kind not in OtherIncome.Kind.values:
        raise ExpenseRejected(_("Tria el tipus d'ingrés."))
    if not payer or len(payer) > 140:
        raise ExpenseRejected(_("Cal el pagador, de 140 caràcters com a màxim."))
    if kind == OtherIncome.Kind.GRANT and document_file is None:
        raise ExpenseRejected(_("Un ajut porta la resolució o el contracte."))
    label = OtherIncome.Kind(kind).label
    movement = treasury.record_other_income(
        account,
        amount_cents,
        value_date=value_date,
        department=department,
        cost_centre=cost_centre,
        # Sense el pagador, que podria ser una persona (S-M09-03).
        concept=f"{label} ({department.name})"[:140],
        by=by,
    )
    income = OtherIncome.objects.create(
        kind=kind,
        payer=payer,
        amount_cents=amount_cents,
        department=department,
        cost_centre=cost_centre,
        document_file=document_file,
        movement=movement,
        recorded_by=by,
    )
    audit.record(
        OTHER_INCOME_RECORDED,
        actor=by,
        target=income,
        details={"kind": kind, "amount_cents": amount_cents, "movement": movement.pk},
    )
    return income
