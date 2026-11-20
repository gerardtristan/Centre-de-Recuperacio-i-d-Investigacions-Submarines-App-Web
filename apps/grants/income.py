"""Ingrés d'un ajut des de la sol·licitud (T-M09A-08; P-M09A-E; RN-M09A-09). El registra la part
principal del 09 com a `OtherIncome` de tipus ajut, lligat a la sol·licitud i al seu departament,
mai a una activitat; `grants` no escriu als models de `expenses`."""

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.expenses import income as expenses_income
from apps.expenses.models import OtherIncome

from .models import GrantApplication
from .services import GrantError, require

INCOME = "grants.income"  # AJ6 (demana també MG4, que comprova el 09)
S = GrantApplication.Status


@transaction.atomic
def record_income(application, *, amount_cents, account, value_date, by) -> OtherIncome:
    """Un ingrés d'una sol·licitud concedida (o ja justificada): pot n'hi haver més d'un
    (bestreta i saldo). La resolució de la concessió és el document de l'ingrés."""
    require(by, INCOME)
    application = (
        GrantApplication.objects.select_for_update().select_related("call").get(pk=application.pk)
    )
    if application.status not in (S.GRANTED, S.JUSTIFIED):
        raise GrantError(_("Només es registra l'ingrés d'un ajut concedit."))
    return expenses_income.record_other_income(
        kind=OtherIncome.Kind.GRANT,
        payer=application.call.body,
        amount_cents=amount_cents,
        account=account,
        value_date=value_date,
        department=application.department,
        cost_centre=application.cost_centre,
        document_file=application.resolution_file,
        grant_application=application,
        by=by,
    )
