"""La llista d'espera a mà (T-M02-12b; RN-M02-09; AC16). Portat de la branca aparcada.

- `move`: el responsable canvia la posició d'algú a la llista, amb motiu. Les posicions continuen
  sent 1, 2, 3…, sense forats, i el canvi queda al registre amb la posició anterior.
- `offer_to`: ofereix una plaça lliure a algú de la llista, amb el termini de RN-M02-09
  (`deadlines.offer_deadline`). Si no és el primer, cal motiu. Amb les inscripcions tancades no
  s'ofereix res (decisió 103).

Tots dos demanen AC16 amb edició i, si el rol el té amb l'abast «les seves activitats», que
l'activitat sigui seva (`permissions.require` amb l'objecte, abans de la transacció).
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit

from . import deadlines, permissions
from . import enrolment as enrolments
from .models import Enrolment

S = Enrolment.Status
MOVED = "activities.waitlist.moved"


def _reason(reason) -> str:
    return (reason or "").strip()


def move(enrolment, position, *, by, reason, request=None) -> Enrolment:
    """Canvia la posició d'algú a la llista d'espera, amb motiu (RN-M02-09)."""
    permissions.require(by, permissions.WAITLIST, enrolment.activity, request=request)
    if not _reason(reason):
        raise ValidationError(_("Per canviar l'ordre de la llista d'espera cal un motiu."))
    if isinstance(position, bool) or not isinstance(position, int):
        raise ValidationError(_("La posició ha de ser un número."))
    with transaction.atomic():
        activity = enrolments.lock(enrolment.activity)
        rows = list(enrolments.waitlist(activity).select_for_update(of=("self",)))
        row = next((r for r in rows if r.pk == enrolment.pk), None)
        if row is None:
            raise ValidationError(_("Aquesta inscripció no és a la llista d'espera."))
        if not 1 <= position <= len(rows):
            raise ValidationError(
                _("La posició ha de ser entre 1 i %(last)s.") % {"last": len(rows)}
            )
        old = row.waitlist_position
        if old == position:
            return row
        rows.remove(row)
        rows.insert(position - 1, row)
        for index, other in enumerate(rows, start=1):
            if other.waitlist_position != index:
                Enrolment.objects.filter(pk=other.pk).update(waitlist_position=index)
        audit.record(
            MOVED, actor=by, target=row, field="waitlist_position", old=old, new=position,
            reason=_reason(reason), request=request,
        )  # fmt: skip
    row.refresh_from_db()
    return row


def offer_to(enrolment, *, by, reason="", now=None, request=None) -> Enrolment:
    """Ofereix una plaça lliure a algú de la llista. Si no és el primer, cal un motiu."""
    permissions.require(by, permissions.WAITLIST, enrolment.activity, request=request)
    now = now or timezone.now()
    with transaction.atomic():
        activity = enrolments.lock(enrolment.activity)
        row = Enrolment.objects.select_for_update(of=("self",)).get(pk=enrolment.pk)
        if row.status != S.WAITLISTED:
            raise ValidationError(_("Aquesta inscripció no és a la llista d'espera."))
        if not enrolments.is_open(activity, now):
            raise enrolments.ActivityNotOpen(
                _("Amb les inscripcions tancades no es pot oferir cap plaça. Reobre-les abans.")
            )
        if enrolments.free_places(activity) == 0:
            raise ValidationError(_("No hi ha cap plaça lliure per oferir."))
        if row.waitlist_position != 1 and not _reason(reason):
            raise ValidationError(
                _("Per oferir una plaça saltant l'ordre de la llista cal un motiu.")
            )
        enrolments.change_status(
            row, S.OFFERED, actor=by, reason=_reason(reason),
            details={"waitlist_position": row.waitlist_position}, request=request,
        )  # fmt: skip
        row.waitlist_position = None
        row.offer_expires_at = deadlines.offer_deadline(activity, now)
        row.save(update_fields=["status", "waitlist_position", "offer_expires_at", "updated_at"])
        deadlines.renumber(activity)
    return row
