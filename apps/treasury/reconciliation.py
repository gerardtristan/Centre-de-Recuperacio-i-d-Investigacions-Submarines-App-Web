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
- **Proposada amb una liquidació** (T-M04-13b; P-M04-F pas 2; CA-T11.1): línia d'entrada sense
  referències de càrrec amb l'import del net d'una sola liquidació «rebuda» del proveïdor, del
  dia de l'abonament als `SETTLEMENT_DAYS` dies següents (P-364). Només compten les línies
  obertes. Una liquidació amb l'identificador (4 caràcters o més) al concepte d'una sola línia
  és d'aquella línia; per a la resta, si encara n'hi ha més d'una, o la mateixa liquidació
  encaixa amb dues línies, «a revisar» sense proposta. Una parella (línia, liquidació) desfeta no
  es torna a proposar. Es confirma amb `settlements.confirm_line` i es desfà amb `undo`.
- **Pendent**: la resta (sortides, línies sense cap coincidència). Que tota línia sense
  referència vagi a revisar (LT2) és la P-101.
Cada canvi d'estat queda al registre d'activitat (RN-T13), sense el concepte de la línia.
Les línies d'un extracte desfet que eren obertes tornen a pendent, sense proposta.
El criden la importació en confirmar o desfer un extracte (senyal `bank_statement.changed`),
`confirm` i, abans de mostrar res, les pantalles de la T-M04-14 i la T-M04-15.

`confirm()` (T-M04-12; P-M04-E passos 3 i 4; CA-T10.1 a CA-T10.3): el tresorer confirma la
proposta d'una línia. Cada càrrec passa a «pagat» amb un pagament per transferència i el seu
ingrés al banc; si és una quota, s'avisa el 01. `undo()` la desfà (CA-T10.4 a CA-T10.6, 045).

`match()` (T-M04-12e; P-M04-E pas 3; LT2; RN-T17): el tresorer casa a mà una línia d'entrada
pendent amb un o més càrrecs pendents que en sumen l'import exacte, i passa el mateix que en
confirmar una proposta. `pending_charges()` els busca per referència o número de soci.

`exclude()` (T-M04-14; RN-T15, CA-T12.1, LT11): el tresorer exclou una línia pendent amb motiu
obligatori. No crea cap moviment ni toca cap càrrec; la línia surt de la llista «a revisar».
`to_review()` és aquesta llista (CA-T13.1): les línies obertes amb la marca i el motiu. Els
pagaments «a revisar» del 05b encara no hi són (P-191). Permisos: P-190.
"""

import re
from collections import Counter
from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import Count, Exists, Max, OuterRef, Q
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.charges import active_payments, euros, record_payment, revert_paid_transfer
from apps.core.imports import statement_lines
from apps.core.models import Charge, Payment
from apps.core.permissions import has_perm
from apps.members import fees as member_fees
from apps.members import services as members
from apps.payments.models import PaymentAttempt

from . import services
from .models import (
    Movement,
    ProviderSettlement,
    Reconciliation,
    ReconciliationUndo,
    StatementLineState,
    TransferReference,
)
from .references import references_in, transfer_reference

STATE_CHANGED = "treasury.statement_line_state_changed"
CONFIRMED = "treasury.reconciliation_confirmed"
EXCLUDED = "treasury.statement_line_excluded"
UNDONE = "treasury.reconciliation_undone"
RECONCILE = "treasury.reconcile"  # T4, «Conciliar i desfer una conciliació» (M04-4)
# T8, «Excloure una línia»: el mateix permís que T4, perquè la matriu dona totes dues només al
# tresorer i un permís nou seria del nucli (P-190, opció per defecte).
EXCLUDE = RECONCILE
OPEN = (StatementLineState.Status.PENDING, StatementLineState.Status.PROPOSED)
Reason = StatementLineState.ReviewReason
AMBIGUOUS = Reason.SETTLEMENT_AMBIGUOUS
SETTLEMENT_DAYS = 5  # P-364: l'abonament arriba al banc com a molt 5 dies després de la liquidació
NAMED_MIN = 4  # un identificador més curt sortiria a qualsevol concepte


def _evaluate(line, found, charges_by_reference, single_charge_by_amount, taken):
    """(estat, motiu de la revisió, càrrecs proposats) d'una línia; `found`, les seves
    referències vàlides."""
    if line.amount_cents <= 0:
        return StatementLineState.Status.PENDING, "", []
    if not found:
        single = single_charge_by_amount.get(line.amount_cents)
        reason = Reason.AMOUNT_ONLY if single is not None and single not in taken else ""
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


def _snapshot(status, reason, charge_ids, settlement_id=None):
    snapshot = {
        "status": status,
        "to_review": bool(reason),
        "review_reason": reason,
        "charges": charge_ids,
    }
    if settlement_id:
        snapshot["settlement"] = settlement_id
    return snapshot


PLAIN = _snapshot(StatementLineState.Status.PENDING, "", [])


def _apply(
    state,
    status,
    reason,
    charges,
    *,
    created,
    actor=None,
    action=STATE_CHANGED,
    why="",
    settlement=None,
) -> None:
    """Desa l'estat si ha canviat i en deixa l'entrada al registre."""
    charge_ids = sorted(charge.pk for charge in charges)
    new = _snapshot(status, reason, charge_ids, settlement and settlement.pk)
    old = None
    if not created:
        old = _snapshot(
            state.status,
            state.review_reason,
            sorted(charge.pk for charge in state.proposed_charges.all()),
            state.proposed_settlement_id,
        )
        if old == new:
            return
    state.status, state.to_review, state.review_reason = status, bool(reason), reason
    state.proposed_settlement = settlement
    state.save()
    state.proposed_charges.set(charges)
    audit.record(
        action,
        actor=actor or audit.system("treasury.reconciliation"),
        target=state,
        old=old,
        new=new,
        reason=why,
        details={"line": state.statement_line_id},
    )


@transaction.atomic
def refresh() -> None:
    """Estat de totes les línies obertes. Idempotent: si res no ha canviat, no escriu res."""
    with connection.cursor() as cursor:  # dues actualitzacions alhora no es trepitgen
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [STATE_CHANGED])
    current = statement_lines()
    # Línies d'un extracte desfet: deixen de ser a conciliar, i la seva proposta també.
    for state in (
        StatementLineState.objects.filter(status__in=OPEN)
        .exclude(statement_line__in=current)
        .prefetch_related("proposed_charges")
    ):
        _apply(state, StatementLineState.Status.PENDING, "", [], created=False)
    # shortcut: recalcula totes les línies obertes a cada crida (centenars l'any); si en
    # fossin desenes de milers, que només recalculi les dels càrrecs que han canviat.
    lines = list(current.order_by("value_date", "pk"))
    states = {
        state.statement_line_id: state
        for state in StatementLineState.objects.filter(statement_line__in=current).prefetch_related(
            "proposed_charges"
        )
    }
    found = {line.pk: references_in(line.concept) for line in lines}
    charges_by_reference = {
        row.reference: row.charge
        for row in TransferReference.objects.filter(
            reference__in={reference for refs in found.values() for reference in refs}
        ).select_related("charge")
    }
    single_charge_by_amount = {
        row["amount_cents"]: row["charge_id"]
        for row in Charge.objects.filter(
            status=Charge.Status.PENDING,
            amount_cents__in={line.amount_cents for line in lines if line.amount_cents > 0},
        )
        .values("amount_cents")
        .annotate(n=Count("pk"), charge_id=Max("pk"))
        if row["n"] == 1
    }
    settlement_for = _settlement_candidates(
        [
            line
            for line in lines
            if not found[line.pk] and (line.pk not in states or states[line.pk].status in OPEN)
        ]
    )
    taken, new_plain = set(), []
    # Primer les línies amb referència: un càrrec ja proposat no compta per a les que no en
    # tenen (AMOUNT_ONLY).
    for line in sorted(lines, key=lambda line: not found[line.pk]):
        state = states.get(line.pk)
        if state is not None and state.status not in OPEN:
            continue
        settlement, candidates = None, settlement_for.get(line.pk)
        if candidates is None:
            status, reason, charges = _evaluate(
                line, found[line.pk], charges_by_reference, single_charge_by_amount, taken
            )
        elif isinstance(candidates, ProviderSettlement):
            status, reason, charges = StatementLineState.Status.PROPOSED, "", []
            settlement = candidates
        else:
            status, reason, charges = StatementLineState.Status.PENDING, AMBIGUOUS, []
        if state is None and _snapshot(status, reason, []) == PLAIN:
            new_plain.append(StatementLineState(statement_line=line))
            continue
        created = state is None
        _apply(
            state or StatementLineState(statement_line=line),
            status,
            reason,
            charges,
            created=created,
            settlement=settlement,
        )
    StatementLineState.objects.bulk_create(new_plain)


def _candidates(lines) -> dict:
    """{línia: (candidates, nomenades)} de les línies d'entrada (`lines`, obertes) que encaixen
    alguna liquidació rebuda del proveïdor: import exacte del net, dins la finestra (P-364) i
    sense una conciliació desfeta de la mateixa parella."""
    amounts = {line.amount_cents for line in lines if line.amount_cents > 0}
    received = list(
        ProviderSettlement.objects.filter(
            status=ProviderSettlement.Status.RECEIVED, net_cents__in=amounts
        ).exclude(source=ProviderSettlement.Source.REMITTANCE)  # la remesa la concilia el 05b
    )
    undone = set(
        Reconciliation.objects.filter(
            statement_line__in=lines, settlement__in=received, undo__isnull=False
        ).values_list("statement_line_id", "settlement_id")
    )
    found = {}
    for line in lines:
        candidates = [
            s
            for s in received
            if s.net_cents == line.amount_cents
            and s.settled_on <= line.value_date <= s.settled_on + timedelta(days=SETTLEMENT_DAYS)
            and (line.pk, s.pk) not in undone
        ]
        named = [
            s
            for s in candidates
            if len(s.external_id) >= NAMED_MIN
            and s.external_id.casefold() in line.concept.casefold()
        ]
        if candidates:
            found[line.pk] = (candidates, named)
    return found


def _settlement_candidates(lines) -> dict:
    """{línia: la liquidació que se li proposa, o la llista de candidates si no n'hi ha una de
    sola} (P-M04-F pas 2). Primer, la liquidació nomenada al concepte d'una sola línia és
    d'aquella línia i surt de les candidates de les altres; després, la resta per unicitat."""
    found = _candidates(lines)
    claims = Counter(n[0].pk for _c, n in found.values() if len(n) == 1)
    result = {pk: n[0] for pk, (_c, n) in found.items() if len(n) == 1 and claims[n[0].pk] == 1}
    taken = {s.pk for s in result.values()}
    rest = {}
    for pk, (candidates, named) in found.items():
        if pk not in result:
            left = [s for s in (named or candidates) if s.pk not in taken]
            if left:
                rest[pk] = left
    sole = Counter(c[0].pk for c in rest.values() if len(c) == 1)
    result.update({pk: c[0] if len(c) == 1 and sole[c[0].pk] == 1 else c for pk, c in rest.items()})
    return result


class ReconciliationRejected(ValidationError):
    """La línia no té cap proposta per confirmar, o ja està conciliada (CA-T10.3)."""


def _ensure_can_reconcile(by) -> None:
    if not has_perm(by, RECONCILE, write=True):
        raise Http404


@transaction.atomic
def confirm(line, *, by) -> Reconciliation:
    """Confirma la proposta de la línia (RN-T16: sempre un compte amb T4, mai el sistema).
    Abans la torna a calcular: si un càrrec ha canviat o la suma ja no és exacta, no hi ha
    proposta (CA-T10.2). Tot o res."""
    _ensure_can_reconcile(by)
    refresh()  # també agafa el pany: dues confirmacions de la mateixa línia no es trepitgen
    state = (
        StatementLineState.objects.select_for_update()
        .filter(statement_line=line)
        .select_related("statement_line")
        .first()
    )
    if state is not None and state.status == StatementLineState.Status.RECONCILED:
        raise ReconciliationRejected(_("Aquesta línia ja està conciliada."))
    if (
        state is None
        or state.status != StatementLineState.Status.PROPOSED
        or state.proposed_settlement_id  # es confirma amb `settlements.confirm_line`
    ):
        raise ReconciliationRejected(_("Aquesta línia no té cap proposta per confirmar."))
    return _reconcile(state, list(state.proposed_charges.order_by("pk")), by=by)


def _flagged(charges):
    """Els càrrecs amb dues marques: `collecting`, un cobrament en curs que el pagaria per una
    altra banda (targeta o Bizum en curs o «a revisar», que potser ja s'ha cobrat, o una
    domiciliació d'una remesa enviada al banc; la transferència que s'espera no, que és la que es
    casa); `proposed`, a la proposta d'una línia."""
    attempts = PaymentAttempt.objects.filter(charge=OuterRef("pk"))
    S = PaymentAttempt.Status
    collecting = attempts.filter(
        Q(status=S.SENT_TO_BANK)
        | Q(status__in=[S.IN_PROGRESS, S.TO_REVIEW]) & ~Q(method=PaymentAttempt.Method.TRANSFER)
    )
    proposed = StatementLineState.objects.filter(
        status=StatementLineState.Status.PROPOSED, proposed_charges=OuterRef("pk")
    )
    return charges.annotate(collecting=Exists(collecting), proposed=Exists(proposed))


def match_problem(line) -> str:
    """Per què la línia no es pot casar a mà, o "" si es pot (d'entrada, pendent, d'un extracte
    vigent). Llegeix l'estat desat: `match` el torna a calcular abans de pagar res."""
    state = (
        StatementLineState.objects.filter(statement_line=line, statement_line__in=statement_lines())
        .select_related("statement_line")
        .first()
    )
    if state is not None and state.status == StatementLineState.Status.PROPOSED:
        return _("Aquesta línia ja té una proposta: revisa-la i confirma-la.")
    if (
        state is None
        or state.status != StatementLineState.Status.PENDING
        or state.statement_line.amount_cents <= 0
    ):
        return _("Aquesta línia no està pendent o no és d'entrada: no es pot casar.")
    return ""


def _matchable(line, charge_ids, *, lock):
    """(estat, càrrecs) d'un casament a mà, o `ReconciliationRejected`: una línia d'entrada
    pendent d'un extracte vigent i càrrecs pendents, sense cap cobrament en curs ni a cap altra
    proposta, que sumin exactament l'import (RN-T17, RN-T17b)."""
    if lock:  # bloqueja la línia i els càrrecs fins que acabi la transacció
        StatementLineState.objects.select_for_update().filter(statement_line=line).first()
        # Sempre en el mateix ordre: dos casaments alhora no es bloquegen l'un a l'altre.
        list(Charge.objects.select_for_update().filter(pk__in=set(charge_ids)).order_by("pk"))
    if problem := match_problem(line):
        raise ReconciliationRejected(problem)
    state = StatementLineState.objects.select_related("statement_line").get(statement_line=line)
    matched = list(_flagged(Charge.objects.filter(pk__in=set(charge_ids))).order_by("pk"))
    if not matched or len(matched) != len(set(charge_ids)):
        raise ReconciliationRejected(_("Tria un o més càrrecs pendents."))
    if any(charge.status != Charge.Status.PENDING for charge in matched):
        raise ReconciliationRejected(_("Un dels càrrecs ja no està pendent."))
    if any(charge.collecting for charge in matched):
        raise ReconciliationRejected(
            _("Un dels càrrecs té un cobrament en curs (targeta, Bizum o domiciliació).")
        )
    if any(charge.proposed for charge in matched):
        raise ReconciliationRejected(
            _("Un dels càrrecs ja és a la proposta d'una altra línia: confirma aquella.")
        )
    total = sum(charge.amount_cents for charge in matched)
    if total != state.statement_line.amount_cents:
        raise ReconciliationRejected(
            _("Els càrrecs sumen %(total)s i la línia és de %(amount)s: han de coincidir.")
            % {"total": euros(total), "amount": euros(state.statement_line.amount_cents)}
        )
    return state, matched


def check_match(line, charge_ids, *, by) -> list[Charge]:
    """Pas de revisió del casament a mà: les mateixes comprovacions que `match` sobre l'estat
    desat, sense pagar res ni recalcular les propostes."""
    _ensure_can_reconcile(by)
    return _matchable(line, charge_ids, lock=False)[1]


@transaction.atomic
def match(line, charge_ids, *, by) -> Reconciliation:
    """Casar a mà (T-M04-12e; P-M04-E pas 3; LT2): el tresorer casa una línia pendent amb un o
    més càrrecs pendents que en sumen l'import exacte. Després, el mateix que `confirm` (i es
    desfà amb `undo`), sense inventar cap referència que la línia no porti."""
    _ensure_can_reconcile(by)
    refresh()  # també agafa el pany
    state, matched = _matchable(line, charge_ids, lock=True)
    return _reconcile(state, matched, by=by, manual=True)


def _reconcile(state, matched, *, by, manual=False) -> Reconciliation:
    """Pagament per transferència, ingrés al banc i avís al 01 de cada càrrec; conciliació i
    línia «conciliada». Dins la transacció de qui la crida."""
    line_date = state.statement_line.value_date
    if manual:  # només la referència que porta la línia (RN-T20: no se n'inventa cap)
        carried = set(references_in(state.statement_line.concept))
        found = TransferReference.objects.filter(charge__in=matched, reference__in=carried)
        references = {charge.pk: "" for charge in matched}
        references.update(found.values_list("charge_id", "reference"))
    else:
        references = {charge.pk: transfer_reference(charge) for charge in matched}
    for charge in matched:
        payment = record_payment(
            charge,
            method=Payment.Method.TRANSFER,
            origin="reconciliation",
            by=by,
            transfer_reference=references[charge.pk],
            # P-111 (095): el dia de valor de la línia, perquè el saldo quadri amb l'extracte.
            paid_at=timezone.make_aware(datetime.combine(line_date, time.min)),
        )
        services.record_income(payment, origin="reconciliation", by=by)
        fee = getattr(charge, "annual_fee", None)
        if fee is not None:
            members.on_fee_paid(fee.pk)
    reconciliation = Reconciliation.objects.create(
        statement_line=state.statement_line, confirmed_by=by
    )
    reconciliation.matched_charges.set(matched)
    _apply(state, StatementLineState.Status.RECONCILED, "", matched, created=False, actor=by)
    audit.record(
        CONFIRMED,
        actor=by,
        target=reconciliation,
        details={
            "line": state.statement_line_id,
            "charges": [charge.pk for charge in matched],
            "amount_cents": state.statement_line.amount_cents,
            **({"manual": True} if manual else {}),  # casada a mà (T-M04-12e)
        },
    )
    return reconciliation


@transaction.atomic
def undo(reconciliation: Reconciliation, *, reason: str, by) -> ReconciliationUndo:
    """Desfà una conciliació vigent amb motiu (RN-T19; 045; CA-T10.4 i CA-T10.5), tot o res:
    per a cada càrrec casat, el contramoviment de l'ingrés i «pagat → pendent» amb el pagament
    anul·lat (`charges.revert_paid_transfer`; el 05b hi reacciona sol); si és una quota, l'avís
    a qui edita les quotes, sense tocar el soci ni el carnet (P-110, opció per defecte). La línia
    torna a «pendent» i es torna a calcular: amb la mateixa referència, es tornarà a proposar."""
    _ensure_can_reconcile(by)
    reason = (reason or "").strip()
    if not reason:
        raise ReconciliationRejected(_("Per desfer una conciliació cal escriure'n el motiu."))
    refresh()  # també agafa el pany
    reconciliation = Reconciliation.objects.select_for_update().get(pk=reconciliation.pk)
    if ReconciliationUndo.objects.filter(reconciliation=reconciliation).exists():
        raise ReconciliationRejected(_("Aquesta conciliació ja està desfeta."))
    matched = list(reconciliation.matched_charges.order_by("pk"))
    settlement = reconciliation.settlement
    if settlement is not None and settlement.source == ProviderSettlement.Source.REMITTANCE:
        raise ReconciliationRejected(
            _("Una remesa no es desfà: es corregeix amb un retorn o una devolució.")
        )
    if settlement is not None:
        _undo_settlement(settlement, reason, by)
        matched = []  # els cobraments ja eren pagats (targeta o Bizum) i no es toquen
    for charge in matched:
        transfers = [
            payment
            for payment in active_payments(charge)
            if payment.method == Payment.Method.TRANSFER
        ]
        if charge.status != Charge.Status.PAID or len(transfers) != 1:
            raise ReconciliationRejected(
                _("Un dels càrrecs ja no està pagat per aquesta transferència: no es pot desfer.")
            )
        income = Movement.objects.get(payment=transfers[0], kind=Movement.Kind.INCOME)
        services.reverse(income, reason=reason, by=by, origin=services.RECONCILIATION)
        revert_paid_transfer(charge, reason, by=by)
        fee = getattr(charge, "annual_fee", None)
        if fee is not None:
            member_fees.notify_fee_editors(fee, member_fees.NOTICE_TRANSFER_REVERTED)
    done = ReconciliationUndo.objects.create(
        reconciliation=reconciliation, reason=reason, undone_by=by
    )
    state = StatementLineState.objects.select_for_update().get(
        statement_line=reconciliation.statement_line_id
    )
    _apply(state, StatementLineState.Status.PENDING, "", [], created=False, actor=by)
    audit.record(
        UNDONE,
        actor=by,
        target=reconciliation,
        reason=reason,
        details={"line": reconciliation.statement_line_id, "charges": [c.pk for c in matched]},
    )
    refresh()
    return done


def _undo_settlement(settlement, reason, by) -> None:
    """La liquidació torna a «rebuda» i les dues potes del traspàs del net es compensen amb motiu
    (RN-T25). Les comissions es queden: són dels cobraments, no de la línia, i en tornar-la a
    confirmar `record_fee` no les repeteix (P-365)."""
    settlement = ProviderSettlement.objects.select_for_update().get(pk=settlement.pk)
    legs = list(settlement.movements.filter(kind=Movement.Kind.TRANSFER, reversal__isnull=True))
    if settlement.status != ProviderSettlement.Status.RECONCILED or len(legs) != 2:
        raise ReconciliationRejected(_("Aquesta liquidació ja no està conciliada."))
    for leg in legs:
        services.reverse(leg, reason=reason, by=by, origin=services.RECONCILIATION)
    settlement.status = ProviderSettlement.Status.RECEIVED
    settlement.save(update_fields=["status"])


SEARCH_LIMIT = 20


def pending_charges(query: str) -> tuple[list[Charge], bool]:
    """Càrrecs pendents per casar a mà, els més recents primer: per referències de transferència
    (amb les variants que llegeix `references_in`) o números de soci, diversos separats per
    espais. Cap cerca per nom. Com a màxim `SEARCH_LIMIT`, i si n'hi ha més. Cada càrrec porta
    les marques de `_flagged`."""
    query = (query or "")[:200]
    numbers = [
        int(word)
        for word in re.split(r"[\s,;]+", query)
        if word.isascii() and word.isdigit() and len(word) < 10
    ]
    found = Q(person__member__member_number__in=numbers) | Q(
        pk__in=TransferReference.objects.filter(reference__in=references_in(query)).values("charge")
    )
    pending = Charge.objects.filter(found, status=Charge.Status.PENDING).select_related("person")
    charges = list(_flagged(pending).order_by("-pk")[: SEARCH_LIMIT + 1])
    return charges[:SEARCH_LIMIT], len(charges) > SEARCH_LIMIT


def has_live_reconciliations(sender, batch, **kwargs) -> bool:
    """V-06 (`bank_statement.reconciled_lines`): el lot té alguna línia amb una conciliació
    vigent, sense desfeta? Llavors l'extracte no es pot desfer."""
    return Reconciliation.objects.filter(statement_line__batch=batch, undo__isnull=True).exists()


def on_statement_changed(sender, batch, **kwargs) -> None:
    """CA-T09.1: les línies d'un extracte confirmat neixen amb estat; les d'un de desfet deixen
    de ser proposades."""
    refresh()


@transaction.atomic
def exclude(line, *, reason: str, by) -> StatementLineState:
    """CA-T12.1: estat «exclosa» amb el motiu, i res més: cap moviment, cap càrrec (RN-T14).
    Només una línia pendent d'un extracte vigent (RN-T15; una proposada, P-192). Una línia
    exclosa no torna enrere ni la toca `refresh()`."""
    if not has_perm(by, EXCLUDE, write=True):
        raise Http404
    reason = (reason or "").strip()
    if not reason:
        raise ReconciliationRejected(_("Per excloure una línia cal escriure'n el motiu."))
    refresh()  # també agafa el pany
    state = (
        StatementLineState.objects.select_for_update()
        .filter(statement_line=line, statement_line__in=statement_lines())
        .prefetch_related("proposed_charges")
        .first()
    )
    if state is None or state.status != StatementLineState.Status.PENDING:
        raise ReconciliationRejected(_("Aquesta línia ja no està pendent: no es pot excloure."))
    state.exclusion_reason = reason
    _apply(
        state,
        StatementLineState.Status.EXCLUDED,
        "",
        [],
        created=False,
        actor=by,
        action=EXCLUDED,
        why=reason,
    )
    return state


def to_review():
    """CA-T13.1: les línies obertes d'un extracte vigent marcades «a revisar», per data."""
    return (
        StatementLineState.objects.filter(
            to_review=True, status__in=OPEN, statement_line__in=statement_lines()
        )
        .select_related("statement_line")
        .order_by("statement_line__value_date", "statement_line__pk")
    )
