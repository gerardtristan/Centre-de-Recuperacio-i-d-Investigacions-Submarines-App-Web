"""Pagament a terminis de la quota de ple dret (T-M01-49; 097, P-61 punts 1 a 4; 085, J-9; 072,
quarta instrucció, punt 2). Construït **apagat**: sense l'ajust `members.instalments.enabled`
ningú no els pot triar i no es crea cap termini. Opcions per defecte: P-396.

- `can_choose(fee)`: una quota anual pendent, sense cap pagament ni cap intent que la pugui
  cobrar, d'un soci de ple dret pendent o actiu, sense cap pas a simpatitzant pendent ni
  acceptat, i amb el mateix import que l'ajust de l'import total (si el preu del tipus és un
  altre, triar canviaria el que deu el soci). Una quota anual només es genera a l'alta, a la
  renovació i al primer pagament d'un menor a qui s'acaba l'exempció (Q-003): punts 3 i 4.
- `choose(fee, by)`: el soci, des de la seva àrea, anul·la la quota anual amb motiu i se'n creen
  els tres terminis sobre càrrecs nous. El primer venç el dia de la quota o avui, si ja ha
  passat; els altres, un i dos mesos després (J-9: «tres terminis mensuals»).
- `plan(total)`: l'import de cada termini (total + recàrrec); els cèntims que sobren, al primer.
- El candidat a «impagat» per un termini el calcula `fees.unpaid_candidates`, el mateix que per
  a la quota anual (T-M01-18d).

Que el soci passi a actiu amb el primer termini pagat i el «vàlid fins al» són de
`services.on_fee_paid` i `validity.instalments_until`.
"""

import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import audit, business_settings, charges
from apps.core.models import Charge

from . import fees
from . import settings as values
from .fee_rules import local_today
from .models import AnnualFee, Member, MemberRequest

COUNT = 3
CHOSEN = "members.fee.instalments_chosen"
K = AnnualFee.Kind
S = Member.Status


def plan(total_cents: int) -> list[int]:
    part, rest = divmod(total_cents, COUNT)
    return [part + rest] + [part] * (COUNT - 1)


def schedule(fee, today=None) -> list[tuple[int, datetime.date]]:
    """(cèntims, venciment) de cada termini, amb l'import vigent dels ajustos."""
    from apps.payments.expiry import months_after

    first = max(fee.due_on, today or local_today())
    amounts = plan(values.instalments_total_cents())
    return [(cents, months_after(first, n)) for n, cents in enumerate(amounts)]


def can_choose(fee) -> bool:
    from apps.payments.attempts import MAY_BE_CHARGED  # el 05b importa el 01

    from .member_requests import downgrades

    member = fee.member
    return (
        values.instalments_enabled()
        and fee.kind == K.ANNUAL
        and fee.charge.status == Charge.Status.PENDING
        and fee.charge.amount_cents == business_settings.get(values.INSTALMENTS_TOTAL)
        and not charges.active_payments(fee.charge)
        and member.type.full_rights
        and member.status in (S.PENDING, S.ACTIVE)
        and not fee.charge.attempts.filter(status__in=MAY_BE_CHARGED).exists()
        and not downgrades(member)
        .filter(
            status__in=(MemberRequest.Status.PENDING, MemberRequest.Status.APPROVED),
            effective_on__isnull=True,
        )
        .exists()
    )


def choose(fee, *, by, request=None) -> list[AnnualFee]:
    """Només el soci mateix amb el compte personal actiu (un altre compte, «no trobat»). Tot o
    res. Un pagament en curs o per revisar de la quota ho impedeix: es podria cobrar dues
    vegades (guarda del 05b)."""
    from apps.payments.attempts import ensure_manual_payment_allowed

    from .member_requests import _is_own_personal
    from .services import _check_account_active

    if not _is_own_personal(fee.member, by):
        raise Http404
    _check_account_active(by)
    with transaction.atomic():
        member = (
            Member.objects.select_for_update(of=("self",))
            .select_related("type")
            .get(pk=fee.member_id)
        )
        locked = AnnualFee.objects.get(pk=fee.pk)
        locked.member = member
        locked.charge = Charge.objects.select_for_update().get(pk=locked.charge_id)
        try:
            ensure_manual_payment_allowed(locked.charge)
        except ValidationError:
            # El text del 05b parla del pagament a mà: és per al tresorer, no per al soci.
            raise ValidationError(
                _("Aquesta quota té un pagament en curs. Quan s'hagi resolt, torna-ho a provar.")
            ) from None
        if not can_choose(locked):
            raise ValidationError(_("Aquesta quota ja no es pot pagar a terminis."))
        charges.cancel(locked.charge, _("Pagament a terminis triat pel soci."), by=by)
        created = [
            fees._issue_fee(
                member,
                kind=K.INSTALMENT,
                amount_cents=cents,
                concept=_("Quota de soci %(period)s, termini %(n)s de %(count)s")
                % {"period": locked.period, "n": n, "count": COUNT},
                period=locked.period,
                due_on=due_on,
                by=by,
                instalment=n,
            )
            for n, (cents, due_on) in enumerate(schedule(locked), start=1)
        ]
        audit.record(
            CHOSEN,
            actor=by,
            target=locked,
            request=request,
            details={"instalments": [f.pk for f in created]},
        )
    return created


def has_unpaid_instalments(member) -> bool:
    """Per al pas a simpatitzant (P-396): mentre hi ha terminis per pagar, no es pot demanar."""
    return AnnualFee.objects.filter(
        member=member, kind=K.INSTALMENT, charge__status__in=fees.UNPAID_CHARGE
    ).exists()


# --- Editar els terminis (T-M01-49c; 072, tercera instrucció, punt 2) -------------------------

EDIT_PERMISSION = "members.fees.edit_instalments"  # P23 (P-413)
EDITED = "members.fee.instalment_edited"


def siblings(fee):
    """Els terminis vigents (no anul·lats) del mateix soci i període, en ordre."""
    return list(
        AnnualFee.objects.filter(member_id=fee.member_id, period=fee.period, kind=K.INSTALMENT)
        .exclude(charge__status=Charge.Status.CANCELLED)
        .select_related("charge")
        .order_by("instalment", "pk")
    )


def is_editable(fee) -> bool:
    """Pendent i sense cap pagament (tampoc un d'anul·lat) ni cap intent que el pugui haver
    cobrat o que l'estigui cobrant (també una remesa enviada). Amb un pagament, només anul·lar i
    crear-ne un de nou."""
    from apps.payments.attempts import ensure_manual_payment_allowed

    if (
        fee.kind != K.INSTALMENT
        or fee.charge.status != Charge.Status.PENDING
        or fee.charge.payments.exists()
    ):
        return False
    try:
        ensure_manual_payment_allowed(fee.charge)
    except ValidationError:
        return False
    return True


def can_edit(by, permissions=None) -> bool:
    from apps.core.permissions import has_perm

    return has_perm(by, EDIT_PERMISSION, write=True, permissions=permissions)


def edit(fee, changes: dict, *, by, reason, request=None) -> list[AnnualFee]:
    """`changes`: {pk del termini: (cèntims, venciment)}. Només terminis editables del mateix
    soci i període; la suma dels terminis vigents no canvia (moure imports entre terminis és
    editar; canviar el total és anul·lar i tornar a generar). Tot o res; cada canvi queda al
    registre amb el valor anterior i el motiu."""
    from .services import _check_account_active, ensure_not_own_member

    if not can_edit(by):
        raise Http404
    _check_account_active(by)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal el motiu per editar els terminis."))
    ensure_not_own_member(fee.member, by, request=request)
    with transaction.atomic():
        Member.objects.select_for_update(of=("self",)).get(pk=fee.member_id)
        plan_fees = siblings(fee)
        by_pk = {f.pk: f for f in plan_fees}
        if fee.pk not in by_pk or not set(changes) <= set(by_pk):
            raise ValidationError(_("Aquests terminis ja no es poden editar."))
        for f in plan_fees:
            f.charge = Charge.objects.select_for_update().get(pk=f.charge_id)
        before = sum(f.charge.amount_cents for f in plan_fees)
        after = before
        for pk, (cents, due_on) in changes.items():
            f = by_pk[pk]
            if (cents, due_on) == (f.charge.amount_cents, f.due_on):
                continue
            if not is_editable(f):
                raise ValidationError(
                    _(
                        "El termini %(n)s té un pagament o un cobrament en curs: no es pot "
                        "editar, només anul·lar."
                    )
                    % {"n": f.instalment}
                )
            if cents < 1:
                raise ValidationError(_("L'import de cada termini ha de ser més gran que zero."))
            after += cents - f.charge.amount_cents
        if after != before:
            raise ValidationError(
                _(
                    "Els terminis han de continuar sumant %(total)s (ara sumen %(sum)s). Per "
                    "canviar el total, cal anul·lar-los i tornar-los a generar."
                )
                % {"total": charges.euros(before), "sum": charges.euros(after)}
            )
        edited = []
        for pk, (cents, due_on) in changes.items():
            f = by_pk[pk]
            old = (f.charge.amount_cents, f.due_on)
            if (cents, due_on) == old:
                continue
            charges.change_amount(f.charge, cents, by=by, reason=reason)
            f.due_on = due_on
            f.save(update_fields=["due_on"])
            audit.record_changes(
                EDITED,
                actor=by,
                target=f,
                changes={"amount_cents": (old[0], cents), "due_on": (str(old[1]), str(due_on))},
                reason=reason,
                request=request,
            )
            edited.append(f)
    return edited
