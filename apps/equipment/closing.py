"""«Material pendent» i cancel·lacions (T-M03-15, part de tancament, i T-M03-16; RN-M03-13 i 20;
L-M03-05; CA-M03-09 i 14).

- `pending_reasons(activity)`: es registra al 02 amb `extensions.register_closing_check` (el 02 el
  crida a `closing_blockers`, i el 09 abans de tancar). Motius sense dades personals: peces
  previstes o lliurades sense tancar (CA-M03-09), necessitats «necessito» sense cap assignació i
  llistes de lloguer no enviades. Els càrrecs de lloguer sense pagar (CA-M03-19) arribaran amb la
  T-M03-11, si la junta aprova RN-M03-11.
- Quan una inscripció deixa d'estar viva (cancel·lada o caducada) o l'activitat es cancel·la, les
  assignacions previstes passen a «cancel·lades» i les peces queden lliures (CA-M03-14). Les ja
  lliurades no es toquen: s'han de retornar. El 03 escolta el `post_save` dels models del 02
  (com el material típic), sense que el 02 l'importi; quan existeixin els esdeveniments
  `enrolment.cancelled` i `activity.cancelled` de la 049 (T-M02-35), s'hi pot subscriure.
"""

from django.db.models import Exists, OuterRef
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from apps.activities.models import Activity, Enrolment
from apps.core import audit

from .models import EquipmentAssignment, EquipmentNeed
from .rentals import unsent

A = EquipmentAssignment.Status
ACTOR = audit.system("equipment.cancellation")
RELEASED = "equipment.assignment_released"


def pending_reasons(activity) -> list[str]:
    reasons = []
    live = EquipmentAssignment.objects.filter(
        activity=activity, status__in=EquipmentAssignment.LIVE
    )
    if count := live.count():
        reasons.append(
            ngettext(
                "Hi ha %(count)s peça de material prevista o lliurada sense tancar.",
                "Hi ha %(count)s peces de material previstes o lliurades sense tancar.",
                count,
            )
            % {"count": count}
        )
    covered = EquipmentAssignment.objects.filter(
        enrolment=OuterRef("enrolment"), equipment_type=OuterRef("equipment_type")
    ).exclude(status=A.CANCELLED)
    needs = EquipmentNeed.objects.filter(
        enrolment__activity=activity,
        enrolment__status=Enrolment.Status.CONFIRMED,
        brings_own=False,
    ).exclude(Exists(covered))
    if count := needs.count():
        reasons.append(
            ngettext(
                "Hi ha %(count)s necessitat de material sense assignar.",
                "Hi ha %(count)s necessitats de material sense assignar.",
                count,
            )
            % {"count": count}
        )
    if count := len(unsent(activity)):
        reasons.append(
            ngettext(
                "Hi ha %(count)s llista de lloguer sense enviar.",
                "Hi ha %(count)s llistes de lloguer sense enviar.",
                count,
            )
            % {"count": count}
        )
    return reasons


def _release(rows, reason) -> int:
    released = 0
    for row in rows.filter(status=A.PLANNED):
        row.status = A.CANCELLED
        row.note = (f"{row.note}\n{reason}").strip()
        row.save(update_fields=["status", "note"])
        audit.record(RELEASED, actor=ACTOR, target=row, field="status", old=A.PLANNED,
                     new=A.CANCELLED, reason=reason)  # fmt: skip
        released += 1
    return released


def on_enrolment_saved(sender, instance, created, raw=False, **kwargs) -> None:
    if not raw and instance.status in Enrolment.ENDED:
        _release(
            EquipmentAssignment.objects.filter(enrolment=instance),
            _("La inscripció ja no és viva."),
        )


def on_activity_saved(sender, instance, created, raw=False, **kwargs) -> None:
    if not raw and instance.status == Activity.Status.CANCELLED:
        _release(
            EquipmentAssignment.objects.filter(activity=instance), _("L'activitat s'ha cancel·lat.")
        )
