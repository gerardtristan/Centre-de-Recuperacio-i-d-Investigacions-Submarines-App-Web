"""Justificació d'un ajut: despeses lligades (T-M09A-09; P-M09A-F, passos 1 i 2; RN-M09A-10). El
paquet (T-M09A-10) i els canvis amb un requeriment obert (T-M09A-15) arriben amb les seves
tasques. `grants` llegeix les despeses però no hi escriu mai."""

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit
from apps.expenses.models import Expense

from .models import GrantApplication, GrantExpenseLink
from .services import GrantError, require

JUSTIFY = "grants.justification"  # AJ7
EXPENSE_LINKED = "grants.expense_linked"
EXPENSE_UNLINKED = "grants.expense_unlinked"
S = GrantApplication.Status


class ExpenseOutOfScope(GrantError):
    """La despesa no és del departament, és fora del període subvencionable o és anul·lada."""


class OverImputed(GrantError):
    """La suma imputada d'una despesa entre tots els ajuts passaria del seu import."""


class AlreadyJustified(GrantError):
    """Sol·licitud justificada: les despeses lligades no canvien sense un requeriment obert."""


def _check_status(application) -> None:
    if application.status == S.JUSTIFIED:
        raise AlreadyJustified(_("La justificació ja s'ha enviat: cal un requeriment obert."))
    if application.status != S.GRANTED:
        raise GrantError(_("Només es lliguen despeses a un ajut concedit."))


@transaction.atomic
def link_expense(application, expense, amount_cents, *, by) -> GrantExpenseLink:
    """`grants.link_expense` (CA-M09A-09 i 10)."""
    require(by, JUSTIFY)
    application = (
        GrantApplication.objects.select_for_update().select_related("call").get(pk=application.pk)
    )
    _check_status(application)
    # El pany de la despesa: dos ajuts alhora no poden passar-se del seu import.
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    call = application.call
    if (
        expense.status == Expense.Status.ANNULLED
        or expense.department_id != application.department_id
        or (call.eligible_expenses_from and expense.invoice_date < call.eligible_expenses_from)
        or (call.eligible_expenses_to and expense.invoice_date > call.eligible_expenses_to)
    ):
        raise ExpenseOutOfScope(
            _("Només despeses del departament de l'ajut, dins el període i no anul·lades.")
        )
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents <= 0:
        raise GrantError(_("L'import imputat ha de ser un enter de cèntims més gran que zero."))
    imputed = (
        GrantExpenseLink.objects.filter(expense=expense, removed_at__isnull=True).aggregate(
            total=Sum("amount_cents")
        )["total"]
        or 0
    )
    if imputed + amount_cents > expense.amount_cents:
        raise OverImputed(
            _("Aquesta despesa ja té %(imputed)s cèntims imputats de %(total)s.")
            % {"imputed": imputed, "total": expense.amount_cents}
        )
    try:
        with transaction.atomic():
            link = GrantExpenseLink.objects.create(
                application=application, expense=expense, amount_cents=amount_cents, created_by=by
            )
    except IntegrityError as error:
        raise GrantError(_("Aquesta despesa ja és lligada a aquest ajut.")) from error
    audit.record(
        EXPENSE_LINKED,
        actor=by,
        target=link,
        details={
            "application": application.pk,
            "expense": expense.pk,
            "amount_cents": amount_cents,
        },
    )
    return link


@transaction.atomic
def unlink_expense(link, *, by) -> GrantExpenseLink:
    """`grants.unlink_expense`: la baixa d'un enllaç, que es conserva (CA-M09A-21)."""
    require(by, JUSTIFY)
    link = (
        GrantExpenseLink.objects.select_for_update().select_related("application").get(pk=link.pk)
    )
    if link.removed_at is not None:
        raise GrantError(_("Aquesta despesa ja s'ha donat de baixa de l'ajut."))
    _check_status(link.application)
    link.removed_at, link.removed_by = timezone.now(), by
    link.save()
    audit.record(EXPENSE_UNLINKED, actor=by, target=link, details={"expense": link.expense_id})
    return link
