"""Cancel·lacions i propostes de devolució (T-M02-15; P-M02-D passos 3 i 4; RN-M02-12 i RN-M02-13;
CA-M02-14 i CA-M02-15; S-M02-23).

- **El participant cancel·la** (`cancel_enrolment`): el seu compte personal, o qui inscriu
  presencialment (AC5) en nom seu, només abans de la data límit d'inscripció (RN-M02-12). Si
  estava pendent de pagament, el càrrec s'anul·la; si estava pagada, es crea una proposta de
  devolució de l'import pagat (mentre la junta no fixi la política, S-M02-05) per al tresorer. La
  plaça que s'allibera s'ofereix al primer de la llista (T-M02-13).
- **El club cancel·la l'activitat** (`cancel_activity`, AC7; també per meteorologia): l'activitat
  passa a `cancelled` (`states.cancel`), totes les inscripcions vives a `cancelled`, els càrrecs
  pendents s'anul·len i els pagats tenen una proposta del 100 % (RN-M02-13). La comissió del
  proveïdor no es recupera (RN-T11): ho porta la 04.
- **El tresorer decideix** (`decide_refund`, AC18): fa la devolució amb el 05b (`payments.refund`,
  que també demana B5 i és idempotent per la clau de la proposta) o la rebutja amb motiu. Cap
  devolució no es fa sense el tresorer (CA-M02-14).

**Amb un pagament en curs** (T-M02-36; RN-M02-37; CA-M02-39): el càrrec no es pot anul·lar
mentre l'intent del 05b no acaba (RN-M05b-22). La inscripció es cancel·la igualment i s'omple
`void_pending_since`. `retry_pending_voids` (tasca de la cua) anul·la el càrrec quan l'intent
acaba sense pagar; si acaba pagat, `charges.on_charge_paid` no confirma res i crea la proposta de
devolució de l'import pagat.

**Fora d'aquesta peça:** els avisos als inscrits i a la llista d'espera (T-M02-21), els
esdeveniments `enrolment.cancelled` i `activity.cancelled` (T-M02-35) i les pantalles.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import Account
from apps.core import audit, charges
from apps.core.models import Charge
from apps.payments import refunds

from . import deadlines, permissions, states
from . import enrolment as enrolments
from .models import Enrolment, RefundProposal

S = Enrolment.Status
REFUND_DECIDED = "activities.refund_decided"


def _reason(reason) -> str:
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal escriure el motiu de la cancel·lació."))
    return reason


def _cancel_row(row, *, by, reason, now, request=None) -> RefundProposal | None:
    """Cancel·la una inscripció viva ja bloquejada: anul·la el càrrec pendent (o el deixa per
    anul·lar quan acabi el pagament en curs) o proposa la devolució del pagat. Torna la proposta,
    si n'hi ha."""
    charge = row.charge
    if row.status == S.OFFERED:  # RN-M02-03: una plaça oferta no acceptada caduca
        enrolments.change_status(row, S.EXPIRED, actor=by, reason=reason, request=request)
    else:
        enrolments.change_status(row, S.CANCELLED, actor=by, reason=reason, request=request)
        row.cancelled_reason = reason
        row.cancelled_by = by if isinstance(by, Account) else None
    row.waitlist_position = row.payment_due_at = row.offer_expires_at = None
    row.save()
    if charge is None:
        return None
    if charge.status == Charge.Status.PENDING and deadlines.paying(charge):
        row.void_pending_since = now
        row.save(update_fields=["void_pending_since", "updated_at"])
        return None
    if charge.status == Charge.Status.PENDING:
        charges.cancel(charge, reason, by=by)
        return None
    if charge.status == Charge.Status.PAID:
        return propose_refund(row)
    return None


def propose_refund(row) -> RefundProposal:
    """La proposta de l'import pagat (RN-M02-12 i RN-M02-13: ara totes dues són el pagat, S-M02-05).
    Una sola per inscripció."""
    proposal, _created = RefundProposal.objects.get_or_create(
        enrolment=row,
        defaults={
            "charge": row.charge,
            "amount_cents": row.charge.amount_cents,
            "reason": row.cancelled_reason,
        },
    )
    return proposal


SYSTEM = audit.system("activities.pending_voids")


def retry_pending_voids() -> int:
    """RN-M02-37: anul·la el càrrec de les inscripcions cancel·lades amb un pagament en curs quan
    l'intent ja ha acabat sense pagar. Si s'ha pagat, en deixa la proposta. Torna quantes resol."""
    done = 0
    for pk in Enrolment.objects.filter(void_pending_since__isnull=False).values_list(
        "pk", flat=True
    ):
        with transaction.atomic():
            row = Enrolment.objects.select_for_update(of=("self",)).select_related("charge")
            row = row.get(pk=pk)
            charge = row.charge
            if row.void_pending_since is None or (
                charge.status == Charge.Status.PENDING and deadlines.paying(charge)
            ):
                continue
            if charge.status == Charge.Status.PENDING:
                charges.cancel(charge, row.cancelled_reason, by=SYSTEM)
            elif charge.status == Charge.Status.PAID:
                propose_refund(row)
            row.void_pending_since = None
            row.save(update_fields=["void_pending_since", "updated_at"])
            done += 1
    return done


def _check_canceller(enrolment, by) -> None:
    if isinstance(by, Account) and by.kind == Account.Kind.PERSONAL:
        if by.person_id != enrolment.person_id:
            raise Http404
        return
    permissions.require(by, permissions.ENROL_IN_PERSON)


def cancel_enrolment(enrolment, *, by, reason, now=None, request=None) -> RefundProposal | None:
    """El participant (o AC5 en nom seu) cancel·la abans de la data límit (RN-M02-12)."""
    _check_canceller(enrolment, by)
    reason, now = _reason(reason), now or timezone.now()
    with transaction.atomic():
        activity = enrolments.lock(enrolment.activity)
        row = Enrolment.objects.select_for_update(of=("self",)).select_related("charge")
        row = row.get(pk=enrolment.pk)
        if row.status not in Enrolment.LIVE:
            raise ValidationError(_("Aquesta inscripció ja no està activa."))
        if activity.registration_closes_at <= now:
            raise ValidationError(
                _("La data límit d'inscripció ja ha passat: parla amb el responsable.")
            )
        proposal = _cancel_row(row, by=by, reason=reason, now=now, request=request)
        deadlines.renumber(activity)
        deadlines.offer_free_places(activity, now=now)
    return proposal


def cancel_activity(activity, *, by, reason, now=None, request=None) -> list[RefundProposal]:
    """El club cancel·la l'activitat: propostes del 100 % per als pagats (RN-M02-13)."""
    permissions.require(by, permissions.MANAGE)
    reason, now = _reason(reason), now or timezone.now()
    with transaction.atomic():
        live = Enrolment.objects.select_for_update(of=("self",)).select_related("charge")
        rows = list(live.filter(activity=activity, status__in=Enrolment.LIVE))
        states.cancel(activity, by=by, reason=reason, now=now, request=request)
        proposals = [
            _cancel_row(row, by=by, reason=reason, now=now, request=request) for row in rows
        ]
    return [proposal for proposal in proposals if proposal is not None]


def decide_refund(proposal, *, approve: bool, note: str, by) -> RefundProposal:
    """AC18: el tresorer fa la devolució amb el 05b o la rebutja amb motiu. Si el 05b falla, la
    proposta continua «proposada» i es pot tornar a provar."""
    permissions.require(by, permissions.REFUND_EXECUTE)
    note = (note or "").strip()
    if not note:
        raise ValidationError(_("Cal una nota que expliqui la decisió."))
    if proposal.status != RefundProposal.Status.PROPOSED:
        raise ValidationError(_("Aquesta proposta de devolució ja està decidida."))
    request = None
    if approve:
        (payment,) = charges.active_payments(proposal.charge)
        request = refunds.refund(
            payment, proposal.amount_cents, reason=note, key=proposal.refund_key, by=by
        )
    with transaction.atomic():
        locked = RefundProposal.objects.select_for_update().get(pk=proposal.pk)
        if locked.status != RefundProposal.Status.PROPOSED:
            return locked
        locked.status = RefundProposal.Status.DONE if approve else RefundProposal.Status.REJECTED
        locked.refund, locked.decision_reason = request, note
        locked.decided_by, locked.decided_at = by, timezone.now()
        locked.save()
        audit.record(
            REFUND_DECIDED, actor=by, target=locked, field="status",
            old=RefundProposal.Status.PROPOSED, new=locked.status, reason=note,
            details={"amount_cents": locked.amount_cents, "charge": locked.charge_id},
        )  # fmt: skip
    return locked
