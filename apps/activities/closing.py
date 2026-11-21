"""Comprovacions de tancament d'una activitat (T-M02-22, part de servei; P-M02-H; RN-M02-22;
CA-M02-23; M02-8: `closing_blockers` i `mark_closed`).

- `closing_blockers(activitat)`: els motius que impedeixen tancar-la econòmicament. Del 02:
  inscripcions pendents de pagament o amb una plaça oferta i propostes de devolució sense fer.
  Altres mòduls hi afegeixen els seus amb `extensions.register_closing_check` (el 03: material
  pendent).
- `mark_closed(activitat, actor=…)`: passa una activitat feta a «tancada». **Només la crida el
  09** (`margins.close_activity`), que és qui comprova el seu permís (MG7): cap pantalla del 02
  la crida. Amb algun motiu pendent, `ClosingBlocked`.

Els motius són frases sense dades personals: diuen quantes coses falten, no de qui són.

Els càrrecs de reforç sense pagar també hi són (T-M02-18).
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from apps.core.models import Charge

from . import extensions, states
from .models import Activity, Enrolment, RefundProposal, ReinforcementRequest

S = Enrolment.Status


class ClosingBlocked(ValidationError):
    """L'activitat no es pot tancar: encara té coses pendents (RN-M02-22)."""

    def __init__(self, reasons):
        super().__init__(list(reasons))
        self.reasons = list(reasons)


def closing_blockers(activity) -> list[str]:
    """Els motius que impedeixen tancar l'activitat. Llista buida = es pot tancar."""
    live = Enrolment.objects.filter(activity=activity)
    unpaid = live.filter(status=S.PENDING_PAYMENT).count()
    offered = live.filter(status=S.OFFERED).count()
    reasons = []
    if unpaid:
        reasons.append(
            ngettext(
                "Hi ha %(count)s inscripció pendent de pagament.",
                "Hi ha %(count)s inscripcions pendents de pagament.",
                unpaid,
            )
            % {"count": unpaid}
        )
    if offered:
        reasons.append(
            ngettext(
                "Hi ha %(count)s plaça oferta sense resposta.",
                "Hi ha %(count)s places ofertes sense resposta.",
                offered,
            )
            % {"count": offered}
        )
    refunds = RefundProposal.objects.filter(
        enrolment__activity=activity, status=RefundProposal.Status.PROPOSED
    ).count()
    if refunds:
        reasons.append(
            ngettext(
                "Hi ha %(count)s proposta de devolució sense fer.",
                "Hi ha %(count)s propostes de devolució sense fer.",
                refunds,
            )
            % {"count": refunds}
        )
    reinforcement = ReinforcementRequest.objects.filter(
        enrolment__activity=activity,
        status=ReinforcementRequest.Status.CONFIRMED,
        charge__status=Charge.Status.PENDING,
    ).count()
    if reinforcement:
        reasons.append(
            ngettext(
                "Hi ha %(count)s càrrec de reforç sense pagar.",
                "Hi ha %(count)s càrrecs de reforç sense pagar.",
                reinforcement,
            )
            % {"count": reinforcement}
        )
    return reasons + extensions.closing_reasons(activity)


@transaction.atomic
def mark_closed(activity, *, actor, now=None, request=None) -> Activity:
    """`done → closed` (M02-8). Només per al 09. `ClosingBlocked` si queda res pendent."""
    locked = states._lock(activity)
    if locked.status != Activity.Status.DONE:
        raise states.InvalidTransition(_("Només es tanca una activitat que ja s'ha fet."))
    reasons = closing_blockers(locked)
    if reasons:
        raise ClosingBlocked(reasons)
    states._apply(
        locked, Activity.Status.CLOSED, actor=actor, now=now or timezone.now(), request=request
    )
    return states._refresh(activity, locked)
