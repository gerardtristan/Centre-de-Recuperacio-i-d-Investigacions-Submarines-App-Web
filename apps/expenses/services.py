"""Despeses (T-M09-04; M09-6, M09-8; RN-M09-09 i 11). Cap altra app escriu aquests models.

Cada servei que escriu comprova el permís del rol (T-M09-30) i, sense, respon «no trobat».
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import Exists, OuterRef, Q
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from apps.core import audit, mail
from apps.core.permission_catalog import SCOPE_ALL
from apps.core.permissions import accounts_with_perm, scope_for
from apps.treasury import services as treasury
from apps.treasury.models import CostCentre
from apps.treasury.services import InvalidDepartment

from .models import DocumentIllegibleMark, Expense, ExpenseAnnulment

RECORD = "expenses.record"  # MG1
PAY = "expenses.pay"  # MG2
NO_INVOICE_TEMPLATE = "avis-despesa-sense-factura"
EXPENSE_RECORDED = "expenses.expense_recorded"
EXPENSE_CHANGED = "expenses.expense_changed"
EXPENSE_PAID = "expenses.expense_paid"
EXPENSE_ANNULLED = "expenses.expense_annulled"

# Els camps que es poden corregir mentre la despesa és per pagar (RN-M09-11).
EDITABLE = (
    "supplier",
    "invoice_number",
    "invoice_date",
    "category",
    "description",
    "amount_cents",
    "tax_cents",
    "department",
    "cost_centre",
)


class ExpenseRejected(ValidationError):
    """A la despesa li falta alguna dada o en té alguna que no val."""


class ExpenseLocked(ValidationError):
    """Una despesa pagada o anul·lada no es modifica (RN-M09-11, CA-M09-03)."""


class AlreadyPaid(ExpenseLocked):
    """La despesa ja està pagada o anul·lada: no es torna a pagar (CA-M09-02)."""


def _require(by, code) -> None:
    """Sense el permís amb abast «tot», «no trobat». L'abast «les seves activitats» (MG1 del
    responsable de cursos i sortides) necessita la despesa lligada a una activitat, que arriba
    amb el repartiment (T-M09-07): fins llavors, no hi val."""
    if scope_for(by, code) != SCOPE_ALL:
        raise Http404


def _cents(value, *, optional=False) -> bool:
    if optional and value is None:
        return True
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def _validate(expense: Expense) -> None:
    if not _cents(expense.amount_cents) or expense.amount_cents == 0:
        raise ExpenseRejected(_("L'import ha de ser un enter de cèntims més gran que zero."))
    if not _cents(expense.tax_cents, optional=True):
        raise ExpenseRejected(_("L'IVA ha de ser un enter de cèntims, zero o més."))
    expense.description = (expense.description or "").strip()
    expense.invoice_number = (expense.invoice_number or "").strip()
    if not expense.description or len(expense.description) > 200:
        raise ExpenseRejected(_("Cal una descripció de 200 caràcters com a màxim."))
    if len(expense.invoice_number) > 40:
        raise ExpenseRejected(_("El número de factura té 40 caràcters com a màxim."))
    if not expense.supplier.active or not expense.category.active:
        raise ExpenseRejected(_("Tria un proveïdor i una categoria actius."))
    department, centre = expense.department, expense.cost_centre
    if (
        department is None
        or not department.active
        or (
            centre is not None
            and not CostCentre.selectable().filter(pk=centre.pk, department=department).exists()
        )
    ):
        raise InvalidDepartment(_("Tria un departament actiu i un centre de cost seu."))


def _save(expense: Expense) -> None:
    try:
        with transaction.atomic():
            expense.save()
    except IntegrityError as error:
        raise ExpenseRejected(_("Aquest proveïdor ja té una factura amb aquest número.")) from error


def _audit_value(value):
    return value.pk if isinstance(value, models.Model) else value


@transaction.atomic
def record_expense(*, by, **fields) -> Expense:
    """`expenses.record_expense(data, actor)` (M09-8): una despesa per pagar. Sense factura
    adjunta, surt a `without_invoice` (RN-M09-09). Cap moviment de la 04 fins que es paga
    (T-M09-05); la data de la factura pot ser d'un període tancat (L-M09-02, P-472)."""
    _require(by, RECORD)
    unknown = set(fields) - set(EDITABLE)
    if unknown:
        raise TypeError(f"Camps desconeguts: {sorted(unknown)}")
    expense = Expense(recorded_by=by, status=Expense.Status.TO_PAY, **fields)
    _validate(expense)
    _save(expense)
    audit.record(
        EXPENSE_RECORDED,
        actor=by,
        target=expense,
        details={name: _audit_value(getattr(expense, name)) for name in EDITABLE},
    )
    # Una despesa neix sense factura: el fitxer s'adjunta després (T-M09-25).
    _notify_without_invoice(expense)
    return expense


def _notify_without_invoice(expense: Expense) -> None:
    """CA-M09-01: un correu a cada adreça de qui pot pagar despeses (MG2, d'inici el tresorer i
    l'administrador; P-473), a la mateixa transacció. Només la referència interna."""
    sent = set()
    for account in accounts_with_perm(PAY, write=True):
        address = account.notification_email
        if address and address not in sent:
            context = {"expense_id": expense.pk}
            mail.queue_email(
                NO_INVOICE_TEMPLATE, to=address, person=account.person, context=context
            )
            sent.add(address)


@transaction.atomic
def update_expense(expense: Expense, *, by, **changes) -> Expense:
    """Corregeix una despesa per pagar; cada camp que canvia va al registre amb el valor anterior
    (M09-6). Pagada o anul·lada, `ExpenseLocked` (RN-M09-11)."""
    _require(by, RECORD)
    unknown = set(changes) - set(EDITABLE)
    if unknown:
        raise TypeError(f"Camps desconeguts: {sorted(unknown)}")
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.status != Expense.Status.TO_PAY:
        raise ExpenseLocked(_("Una despesa pagada o anul·lada no es modifica: s'anul·la."))
    before = {name: _audit_value(getattr(expense, name)) for name in changes}
    for name, value in changes.items():
        setattr(expense, name, value)
    _validate(expense)
    _save(expense)
    audit.record_changes(
        EXPENSE_CHANGED,
        actor=by,
        target=expense,
        changes={name: (before[name], _audit_value(getattr(expense, name))) for name in changes},
    )
    return expense


@transaction.atomic
def pay(expense: Expense, *, account, value_date, by) -> Expense:
    """`expenses.pay` (M09-8, CA-M09-02): un sol moviment `expense` de la 04 amb el mateix import,
    departament i centre de cost, i la despesa passa a «pagada». Amb la data de valor dins un
    període tancat, la 04 respon `PeriodClosed` i no es desa res (RN-T30). El comprovant del
    banc s'adjunta amb la T-M09-25."""
    _require(by, PAY)
    expense = Expense.objects.select_for_update().select_related("supplier").get(pk=expense.pk)
    if expense.status != Expense.Status.TO_PAY:
        raise AlreadyPaid(_("Aquesta despesa ja està pagada o anul·lada."))
    movement = treasury.record_expense(
        account,
        expense.amount_cents,
        value_date=value_date,
        department=expense.department,
        cost_centre=expense.cost_centre,
        # El concepte, sense el nom del proveïdor, que pot ser una persona (M09-12).
        concept=f"{_('Despesa')} {expense.pk}: {expense.description}"[:140],
        by=by,
    )
    expense.status, expense.paid_movement = Expense.Status.PAID, movement
    expense.save(update_fields=["status", "paid_movement", "updated_at"])
    audit.record(
        EXPENSE_PAID,
        actor=by,
        target=expense,
        details={"movement": movement.pk, "value_date": value_date.isoformat()},
    )
    return expense


@transaction.atomic
def annul(expense: Expense, *, reason: str, by, value_date=None) -> ExpenseAnnulment:
    """`expenses.annul` (M09-8; RN-M09-11; CA-M09-03 i 22): anul·lació amb motiu i, si estava
    pagada, el contramoviment de la 04 (anul·lació manual: `value_date`, per defecte avui, no pot
    ser d'un període tancat). El moviment original no canvia. La correcció és una despesa nova."""
    _require(by, PAY)
    reason = (reason or "").strip()
    if not reason:
        raise ExpenseRejected(_("Per anul·lar una despesa cal escriure'n el motiu."))
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.status == Expense.Status.ANNULLED:
        raise ExpenseLocked(_("Aquesta despesa ja està anul·lada."))
    reversal = None
    if expense.status == Expense.Status.PAID:
        reversal = treasury.reverse(
            expense.paid_movement, reason=reason, by=by, value_date=value_date
        )
    annulment = ExpenseAnnulment.objects.create(
        expense=expense, reason=reason, reversal_movement=reversal, annulled_by=by
    )
    expense.status = Expense.Status.ANNULLED
    expense.save(update_fields=["status", "updated_at"])
    audit.record(
        EXPENSE_ANNULLED,
        actor=by,
        target=expense,
        reason=reason,
        details={"reversal": reversal.pk if reversal else None},
    )
    return annulment


def open_marks(document):
    """Marques d'il·legible obertes d'un document de la despesa de la consulta exterior."""
    return DocumentIllegibleMark.objects.filter(
        expense=OuterRef("pk"), document=document, replaced_at__isnull=True
    )


def without_invoice():
    """«Sense factura» (RN-M09-09 i 25): les despeses vives sense factura adjunta o amb la
    factura il·legible (una `DocumentIllegibleMark` oberta; T-M09-25b)."""
    return Expense.objects.exclude(status=Expense.Status.ANNULLED).filter(
        Q(invoice_file__isnull=True) | Exists(open_marks(DocumentIllegibleMark.Document.INVOICE))
    )
