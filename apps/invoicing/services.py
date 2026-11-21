"""Facturació d'un cobrament i factura manual (T-M09-19; RN-M09-17, 19 i 29; CA-M09-16, 17 i 19).

Tot va darrere de l'ajust `billing.enabled_charge_kinds` (VC-34), que neix buit: la facturació
està desactivada i el justificant és el rebut del 05b fins que es responguin la P-02 i la P-47 i
la junta l'activi. El número el dona el servei (`providers`); el 09 no numera mai."""

import re

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.core import audit, business_settings
from apps.core.models import Charge
from apps.core.permissions import has_perm
from apps.treasury.models import Movement

from .models import Invoice, InvoiceLine
from .providers import InvoiceData, InvoiceLineData, ProviderError, get_provider

ENABLED_KINDS = "billing.enabled_charge_kinds"  # VC-34
ISSUE = "expenses.invoices.issue"  # MG9
ACTOR = audit.system("invoicing")
INVOICE_ISSUED = "invoicing.invoice_issued"
INVOICE_FAILED = "invoicing.invoice_failed"
SERIES_GAP = "invoicing.series_gap"
MANUAL_REQUESTED = "invoicing.manual_requested"
RECTIFICATION_REQUESTED = "invoicing.rectification_requested"
_TRAILING_NUMBER = re.compile(r"(\d+)$")


class InvoicingDisabled(ValidationError):
    """RN-M09-19: la facturació no està activada."""


class AlreadyRectified(ValidationError):
    """La devolució ja té la seva rectificativa, o la factura ja està rectificada del tot."""


def check_enabled_kinds(value) -> None:
    """La comprovació de l'ajust (la registra `apps.InvoicingConfig.ready`): només tipus de
    càrrec que existeixen. Buit vol dir facturació desactivada."""
    allowed = {kind.upper() for kind in Charge.Kind.values}
    unknown = set(business_settings.split_list(value)) - allowed
    if unknown:
        raise ValidationError(
            gettext("Tipus de càrrec desconeguts: %(codes)s.")
            % {"codes": ", ".join(sorted(unknown))}
        )


def enabled_kinds(on=None) -> set[str]:
    return {
        code.lower()
        for code in business_settings.split_list(business_settings.get(ENABLED_KINDS, on))
    }


def _customer(invoice) -> tuple[str, str]:
    person = invoice.customer_person
    if person is None:
        return invoice.customer_name, invoice.customer_tax_id
    return f"{person.first_name} {person.last_name}".strip(), person.id_document_number


def _number_value(number: str) -> int | None:
    match = _TRAILING_NUMBER.search(number)
    return int(match.group(1)) if match else None


def _check_series(invoice) -> None:
    """RN-M09-17 (CA-M09-17): la sèrie no pot tenir salts. Un salt queda al registre.
    shortcut: l'avís per correu al tresorer necessita una plantilla del nucli (PR del nucli del
    09); fins llavors, només el registre."""
    numbers = [
        _number_value(n)
        for n in Invoice.objects.filter(series=invoice.series, status=Invoice.Status.ISSUED)
        .exclude(pk=invoice.pk)
        .values_list("number", flat=True)
    ]
    previous = max(filter(None, numbers), default=None)
    current = _number_value(invoice.number)
    if previous is not None and current != previous + 1:
        audit.record(
            SERIES_GAP,
            actor=ACTOR,
            target=invoice,
            details={"series": invoice.series, "expected": previous + 1, "got": current},
        )


def _send(invoice: Invoice) -> Invoice:
    """Demana la factura al servei. Si no respon o torna un número repetit, queda «fallida» i al
    registre, i `retry_failed` la torna a demanar (L-M09-06)."""
    name, tax_id = _customer(invoice)
    data = InvoiceData(
        series=invoice.series,
        customer_name=name,
        customer_tax_id=tax_id,
        base_cents=invoice.base_cents,
        tax_cents=invoice.tax_cents,
        total_cents=invoice.total_cents,
        lines=tuple(
            InvoiceLineData(line.description, line.quantity, line.unit_cents, line.total_cents)
            for line in invoice.lines.all()
        ),
        rectifies_number=invoice.rectifies.number if invoice.rectifies_id else "",
    )
    provider = get_provider()
    invoice.attempts += 1
    try:
        issued = (provider.rectify if invoice.rectifies_id else provider.issue)(data)
        if Invoice.objects.filter(series=invoice.series, number=issued.number).exists():
            raise ProviderError(f"Número repetit: {issued.number}")
    except ProviderError as error:
        invoice.status = Invoice.Status.FAILED
        invoice.save()
        audit.record(INVOICE_FAILED, actor=ACTOR, target=invoice, details={"error": str(error)})
        return invoice
    invoice.number, invoice.provider_ref, invoice.qr_payload = (
        issued.number,
        issued.provider_ref,
        issued.qr,
    )
    invoice.issued_on, invoice.status = timezone.localdate(), Invoice.Status.ISSUED
    invoice.save()
    audit.record(INVOICE_ISSUED, actor=ACTOR, target=invoice, details={"number": invoice.number})
    _check_series(invoice)
    return invoice


def on_charge_paid(event) -> None:
    """Subscriptor de `charge.paid` (049): la factura ordinària d'un càrrec pagat, si la
    facturació està activada per al seu tipus (CA-M09-19). Idempotent per càrrec (CA-M09-16)."""
    charge = Charge.objects.select_related("person").get(pk=event.payload["charge"])
    if charge.kind not in enabled_kinds():
        return
    invoice, created = Invoice.objects.get_or_create(
        series=Invoice.Series.ORDINARY,
        charge=charge,
        defaults={
            "customer_person": charge.person,
            # L'IVA per tipus de càrrec és de la T-M09-27 [A verificar: gestoria].
            "base_cents": charge.amount_cents,
            "tax_cents": 0,
            "total_cents": charge.amount_cents,
        },
    )
    if not created:
        return
    InvoiceLine.objects.create(
        invoice=invoice,
        description=charge.concept,
        quantity=1,
        unit_cents=charge.amount_cents,
        total_cents=charge.amount_cents,
    )
    _send(invoice)


def retry_failed() -> int:
    """Torna a demanar les factures fallides (per a la tasca de la cua). Torna quantes s'emeten."""
    issued = 0
    for invoice in Invoice.objects.filter(status=Invoice.Status.FAILED).order_by("pk"):
        with transaction.atomic():
            locked = Invoice.objects.select_for_update().get(pk=invoice.pk)
            issued += _send(locked).status == Invoice.Status.ISSUED
    return issued


def require(by) -> None:
    if not has_perm(by, ISSUE, write=True):
        raise Http404


@transaction.atomic
def issue_manual(*, customer_name, customer_tax_id, lines, by) -> Invoice:
    """`invoicing.issue_manual` (M09-8): una factura a una empresa, amb línies (descripció,
    quantitat, preu unitari en cèntims). Demana MG9 i la facturació activada."""
    require(by)
    if not enabled_kinds():
        raise InvoicingDisabled(_("La facturació no està activada."))
    customer_name, customer_tax_id = customer_name.strip(), customer_tax_id.strip()
    if not customer_name or not customer_tax_id or len(customer_tax_id) > 20:
        raise ValidationError(_("Cal el nom i el NIF o CIF del client."))
    rows = []
    for description, quantity, unit_cents in lines:
        description = (description or "").strip()
        valid = all(isinstance(v, int) and not isinstance(v, bool) for v in (quantity, unit_cents))
        if (
            not description
            or len(description) > 200
            or not valid
            or quantity <= 0
            or unit_cents < 0
        ):
            raise ValidationError(_("Cada línia porta descripció, quantitat i preu en cèntims."))
        rows.append((description, quantity, unit_cents))
    if not rows:
        raise ValidationError(_("Una factura porta almenys una línia."))
    total = sum(quantity * unit for _description, quantity, unit in rows)
    invoice = Invoice.objects.create(
        series=Invoice.Series.ORDINARY,
        customer_name=customer_name[:140],
        customer_tax_id=customer_tax_id,
        base_cents=total,
        tax_cents=0,
        total_cents=total,
    )
    InvoiceLine.objects.bulk_create(
        InvoiceLine(invoice=invoice, description=d, quantity=q, unit_cents=u, total_cents=q * u)
        for d, q, u in rows
    )
    audit.record(MANUAL_REQUESTED, actor=by, target=invoice, details={"total_cents": total})
    return _send(invoice)


@transaction.atomic
def issue_rectification(invoice, refund_movement, *, reason, by) -> Invoice:
    """`invoicing.issue_rectification` (T-M09-20; RN-M09-18; CA-M09-18): la rectificativa (sèrie
    R) d'una devolució, total o parcial, lligada a la factura original i per l'import de la
    devolució. Una devolució sense factura (L-M09-08) no en té: es rebutja amb el motiu."""
    require(by)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Una rectificativa porta el motiu."))
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    refund = Movement.objects.select_related("payment").get(pk=refund_movement.pk)
    if invoice.series != Invoice.Series.ORDINARY or invoice.status != Invoice.Status.ISSUED:
        raise ValidationError(_("Només es rectifica una factura ordinària emesa."))
    if (
        refund.kind != Movement.Kind.REFUND
        or invoice.charge_id is None
        or refund.payment is None
        or refund.payment.charge_id != invoice.charge_id
    ):
        raise ValidationError(_("Aquesta devolució no és del cobrament d'aquesta factura."))
    if Invoice.objects.filter(refund_movement=refund).exists():
        raise AlreadyRectified(_("Aquesta devolució ja té la seva rectificativa."))
    rectified = sum(
        invoice.rectifications.exclude(status=Invoice.Status.FAILED).values_list(
            "total_cents", flat=True
        )
    )
    if rectified + refund.amount_cents > invoice.total_cents:
        raise AlreadyRectified(_("La rectificativa passaria de l'import de la factura."))
    rectification = Invoice.objects.create(
        series=Invoice.Series.RECTIFYING,
        rectifies=invoice,
        refund_movement=refund,
        customer_person=invoice.customer_person,
        customer_name=invoice.customer_name,
        customer_tax_id=invoice.customer_tax_id,
        base_cents=refund.amount_cents,
        tax_cents=0,
        total_cents=refund.amount_cents,
    )
    InvoiceLine.objects.create(
        invoice=rectification,
        description=(gettext("Rectificació de la factura %(number)s") % {"number": invoice.number})[
            :200
        ],
        quantity=1,
        unit_cents=refund.amount_cents,
        total_cents=refund.amount_cents,
    )
    audit.record(
        RECTIFICATION_REQUESTED,
        actor=by,
        target=rectification,
        reason=reason,
        details={"rectifies": invoice.number, "refund": refund.pk},
    )
    return _send(rectification)
