"""Conciliació de l'extracte, primera part: estats de les línies i propostes (T-M04-11; P-M04-E
pas 2; RN-T15, RN-T17b, RN-T18; CA-T09.1 a CA-T09.3). Aquí no es paga res: un càrrec només passa
a «pagat» quan el tresorer confirma la conciliació (RN-T16, RN-M05b-05; T-M04-12).

`refresh()` dona estat a cada línia que la conciliació pot casar (`imports.statement_lines`) i
torna a calcular les que encara són obertes (pendents o proposades), perquè els càrrecs canvien:
- **Proposada** (CA-T09.2): línia d'entrada amb referències vàlides de càrrecs pendents i la
  suma dels càrrecs igual a l'import (una referència, o diverses: LT5).
- **Pendent i a revisar** (CA-T09.3, LT3, LT4, LT6), sense proposta: referència vàlida amb un
  import diferent, d'un càrrec que ja no està pendent, que no és de cap càrrec o que ja és en la
  proposta d'una línia anterior; o sense referència i un sol càrrec pendent del mateix import.
- **Pendent**: la resta (sortides, línies sense cap coincidència). Que tota línia sense
  referència vagi a revisar (LT2) és la P-101.
Cada canvi d'estat queda al registre d'activitat (RN-T13), sense el concepte de la línia.
"""

from django.db import connection, transaction
from django.db.models import Count

from apps.core import audit
from apps.core.imports import statement_lines
from apps.core.models import Charge

from .models import StatementLineState, TransferReference
from .references import references_in

STATE_CHANGED = "treasury.statement_line_state_changed"
OPEN = (StatementLineState.Status.PENDING, StatementLineState.Status.PROPOSED)
Reason = StatementLineState.ReviewReason


def _evaluate(line, charges_by_reference, single_amounts, taken):
    """(estat, motiu de la revisió, càrrecs proposats) d'una línia."""
    if line.amount_cents <= 0:
        return StatementLineState.Status.PENDING, "", []
    found = references_in(line.concept)
    if not found:
        reason = Reason.AMOUNT_ONLY if line.amount_cents in single_amounts else ""
        return StatementLineState.Status.PENDING, reason, []
    charges = [charges_by_reference.get(reference) for reference in found]
    if None in charges:
        reason = Reason.UNKNOWN_REFERENCE
    elif any(charge.status != Charge.Status.PENDING for charge in charges):
        reason = Reason.CHARGE_NOT_PENDING
    elif any(charge.pk in taken for charge in charges):
        reason = Reason.REPEATED_REFERENCE
    elif sum(charge.amount_cents for charge in charges) != line.amount_cents:
        reason = Reason.AMOUNT_MISMATCH
    else:
        taken.update(charge.pk for charge in charges)
        return StatementLineState.Status.PROPOSED, "", charges
    return StatementLineState.Status.PENDING, reason, []


def _snapshot(status, reason, charge_ids):
    return {
        "status": status,
        "to_review": bool(reason),
        "review_reason": reason,
        "charges": charge_ids,
    }


@transaction.atomic
def refresh() -> None:
    """Estat de totes les línies obertes. Idempotent: si res no ha canviat, no escriu res."""
    with connection.cursor() as cursor:  # dues actualitzacions alhora no es trepitgen
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [STATE_CHANGED])
    # shortcut: recalcula totes les línies obertes a cada crida (centenars l'any); si en
    # fossin desenes de milers, que només recalculi les dels càrrecs que han canviat.
    lines = list(statement_lines().order_by("value_date", "pk"))
    states = {
        state.statement_line_id: state
        for state in StatementLineState.objects.filter(
            statement_line__in=[line.pk for line in lines]
        ).prefetch_related("proposed_charges")
    }
    found = {reference for line in lines for reference in references_in(line.concept)}
    charges_by_reference = {
        row.reference: row.charge
        for row in TransferReference.objects.filter(reference__in=found).select_related("charge")
    }
    amounts = {line.amount_cents for line in lines if line.amount_cents > 0}
    single_amounts = {
        row["amount_cents"]
        for row in Charge.objects.filter(status=Charge.Status.PENDING, amount_cents__in=amounts)
        .values("amount_cents")
        .annotate(n=Count("pk"))
        if row["n"] == 1
    }
    taken, new_plain = set(), []
    for line in lines:
        state = states.get(line.pk)
        if state is not None and state.status not in OPEN:
            continue
        status, reason, charges = _evaluate(line, charges_by_reference, single_amounts, taken)
        new = _snapshot(status, reason, sorted(charge.pk for charge in charges))
        if state is None:
            if new == _snapshot(StatementLineState.Status.PENDING, "", []):
                new_plain.append(StatementLineState(statement_line=line))
                continue
            state, old = StatementLineState(statement_line=line), None
        else:
            old = _snapshot(
                state.status,
                state.review_reason,
                sorted(charge.pk for charge in state.proposed_charges.all()),
            )
            if old == new:
                continue
        state.status, state.to_review, state.review_reason = status, bool(reason), reason
        state.save()
        state.proposed_charges.set(charges)
        audit.record(
            STATE_CHANGED,
            actor=audit.system("treasury.reconciliation"),
            target=state,
            old=old,
            new=new,
            details={"line": line.pk},
        )
    StatementLineState.objects.bulk_create(new_plain)


def on_statement_confirmed(sender, batch, **kwargs) -> None:
    """CA-T09.1: les línies d'un extracte confirmat neixen amb estat."""
    refresh()
