"""Pagament a terminis de la quota de ple dret (T-M01-49; 097, P-61 punts 1 a 4; 085, J-9; 072,
quarta instrucció, punt 2). Construït **apagat**: sense l'ajust `members.instalments.enabled`
ningú no els pot triar i no es crea cap termini.

- `can_choose(fee)`: una quota anual pendent i sense cap pagament, d'un soci de ple dret pendent
  o actiu, sense cap pas a simpatitzant acceptat. Una quota anual només es genera a l'alta, a la
  renovació i al primer pagament d'un menor a qui s'acaba l'exempció (Q-003): són els punts 3 i 4.
- `choose(fee, by)`: el soci, des de la seva àrea, anul·la la quota anual amb motiu i se'n creen
  els tres terminis sobre càrrecs nous. El primer venç el dia de la quota; els altres, un i dos
  mesos després (J-9: «tres terminis mensuals»).
- `plan(total)`: l'import de cada termini; els cèntims que sobren van al primer (P-394).
- `unpaid_candidates(today)`: socis actius amb un termini vençut fa els dies de l'ajust i sense
  pagar (o retornat). Només es proposen: el tresorer marca l'impagat a mà, amb motiu (040).

Que el soci passi a actiu amb el primer termini i el «vàlid fins al» són de `services.on_fee_paid`
i `validity.instalments_until`.
"""

import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import audit, charges
from apps.core.models import Charge

from . import fees
from . import settings as values
from .models import AnnualFee, Member

COUNT = 3
CHOSEN = "members.fee.instalments_chosen"
K = AnnualFee.Kind
S = Member.Status


def plan(total_cents: int) -> list[int]:
    part, rest = divmod(total_cents, COUNT)
    return [part + rest] + [part] * (COUNT - 1)


def schedule(fee) -> list[tuple[int, datetime.date]]:
    """(cèntims, venciment) de cada termini, amb l'import vigent dels ajustos."""
    from apps.payments.expiry import months_after

    amounts = plan(values.instalments_total_cents())
    return [(cents, months_after(fee.due_on, n)) for n, cents in enumerate(amounts)]


def can_choose(fee) -> bool:
    from .member_requests import accepted_downgrade

    member = fee.member
    return (
        values.instalments_enabled()
        and fee.kind == K.ANNUAL
        and fee.charge.status == Charge.Status.PENDING
        and not charges.active_payments(fee.charge)
        and member.type.full_rights
        and member.status in (S.PENDING, S.ACTIVE)
        and accepted_downgrade(member) is None
    )


def choose(fee, *, by, request=None) -> list[AnnualFee]:
    """Només el soci mateix (una quota d'un altre, «no trobat»). Tot o res. Un pagament en curs o
    per revisar de la quota ho impedeix: es podria cobrar dues vegades (guarda del 05b)."""
    from apps.payments.attempts import ensure_manual_payment_allowed

    if fee.member.person_id != by.person_id:
        raise Http404
    with transaction.atomic():
        member = (
            Member.objects.select_for_update(of=("self",))
            .select_related("type")
            .get(pk=fee.member_id)
        )
        locked = AnnualFee.objects.get(pk=fee.pk)
        locked.member = member
        locked.charge = Charge.objects.select_for_update().get(pk=locked.charge_id)
        if not can_choose(locked):
            raise ValidationError(_("Aquesta quota ja no es pot pagar a terminis."))
        ensure_manual_payment_allowed(locked.charge)
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


def unpaid_candidates(today: datetime.date) -> set[int]:
    """Ids dels socis actius candidats a «impagat» per un termini (097, P-61 punt 2)."""
    limit = today - datetime.timedelta(days=values.instalments_unpaid_days())
    return set(
        AnnualFee.objects.filter(
            kind=K.INSTALMENT,
            charge__status__in=fees.UNPAID_CHARGE,
            due_on__lte=limit,
            member__status=S.ACTIVE,
        ).values_list("member_id", flat=True)
    )
