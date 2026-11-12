"""Duplicar una activitat (T-M02-07; decisió 026; RN-M02-21; CA-M02-04; L-M02-10).

`duplicate(activity, new_start, by=…)` crea una activitat nova en esborrany a partir d'una altra:

- **Copia:** títol, descripció, tipus, subtipus, projecte, fitxa del catàleg, departament, places,
  preus i el motiu del preu, requisits, termini de pagament, lloc, punt de trobada, persona
  responsable, enllaç a la previsió, el programa del dia i les sessions amb els seus instructors.
- **Desplaça** totes les dates i hores per la diferència entre la data d'inici nova i l'antiga.
  L'hora del rellotge es conserva encara que pel mig hi hagi un canvi d'hora.
- **No copia:** l'estat (la còpia és `draft`), les dates de publicació i de final, el motiu de
  cancel·lació ni res del que encara no existeix (inscripcions, pagaments, assistència,
  avaluacions, resultats, incidències i fotos). Quan existeixin, tampoc s'hi copiaran.
- La còpia guarda `duplicated_from`. Es pot duplicar una activitat en qualsevol estat, també una
  de cancel·lada (L-M02-10).
- **Permís:** AC7 amb edició; sense, «no trobat».
- **Senyal:** `extensions.activity_duplicated(original, copy, by)`, dins la mateixa transacció,
  perquè el 03 hi copiï el material típic.

**Concrecions d'implementació** (dins de les regles; al diari de la T-M02-07)

- Les sessions cancel·lades no es copien: ja no formen part del pla de l'activitat.
- Un instructor que ja no pot fer classe no es copia: la sessió de la còpia surt «sense
  instructor» (L-M02-05).
- Una fitxa, un tipus o un subtipus desactivat no es pot triar per a una activitat nova, i una
  còpia ho és: es rebutja i es diu què cal tornar a activar.
- Els preus es copien de l'activitat, no del catàleg d'avui (RN-M02-21). Si ara són diferents del
  catàleg, s'avisa el tresorer com en qualsevol activitat amb un preu diferent (RN-M02-06) i la
  fitxa ho mostra.
- El centre de cost (04) i les sessions de reforç (T-M02-18) encara no existeixen.
"""

import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit

from . import catalogue, extensions, permissions, services, sessions
from .models import Activity, ProgrammeBlock, Session

ACTIVITY_DUPLICATED = "activities.activity.duplicated"

COPIED_FIELDS = (
    "kind",
    "title",
    "description",
    "catalogue_entry",
    "outing_type",
    "subtype",
    "project",
    "department",
    "location",
    "meeting_point",
    "max_places",
    "payment_window_hours",
    "price_member_cents",
    "price_non_member_cents",
    "price_override_note",
    "open_to_non_members",
    "required_level",
    "min_level",
    "specialities_rule",
    "min_age",
    "licence_required",
    "requirements_mode",
    "responsible",
    "forecast_url",
)


def shift(moment: datetime.datetime, days: int) -> datetime.datetime:
    """El mateix dia i hora del rellotge, `days` dies més tard (o abans, si és negatiu)."""
    local = timezone.localtime(moment).replace(tzinfo=None)
    return timezone.make_aware(local + datetime.timedelta(days=days))


def _check_still_available(activity) -> None:
    if activity.kind == Activity.Kind.COURSE:
        if not activity.catalogue_entry.active:
            raise ValidationError(
                _("La fitxa del catàleg d'aquesta activitat està desactivada: torna-la a activar.")
            )
        return
    catalogue.check_outing_classification(activity.outing_type, activity.subtype, activity.project)


@transaction.atomic
def duplicate(activity, new_start, *, by, today=None, request=None) -> Activity:
    """Crea una còpia en esborrany que comença el dia `new_start` (RN-M02-21)."""
    permissions.require(by, permissions.MANAGE)
    if not isinstance(new_start, datetime.date) or isinstance(new_start, datetime.datetime):
        raise ValidationError(_("Escriu la data d'inici de la còpia."))
    original = Activity.objects.select_related(
        "catalogue_entry", "outing_type", "subtype", "project"
    ).get(pk=activity.pk)
    _check_still_available(original)
    days = (new_start - original.starts_on).days
    copy = Activity.objects.create(
        **{name: getattr(original, name) for name in COPIED_FIELDS},
        starts_on=new_start,
        ends_on=original.ends_on + datetime.timedelta(days=days),
        registration_closes_at=shift(original.registration_closes_at, days),
        duplicated_from=original,
    )
    copy.required_specialities.set(original.required_specialities.all())
    blocks = ProgrammeBlock.objects.bulk_create(
        ProgrammeBlock(
            activity=copy,
            order=block.order,
            starts_at=block.starts_at,
            ends_at=block.ends_at,
            label=block.label,
            location=block.location,
            responsible_label=block.responsible_label,
        )
        for block in original.programme_blocks.all()
    )
    still_teaching = set(sessions.instructor_people().values_list("pk", flat=True))
    copied_sessions = 0
    for session in original.sessions.filter(cancelled=False).prefetch_related("instructors"):
        new = Session.objects.create(
            activity=copy,
            kind=session.kind,
            starts_at=shift(session.starts_at, days),
            ends_at=shift(session.ends_at, days),
            location=session.location,
            is_practice=session.is_practice,
        )
        new.instructors.set([p for p in session.instructors.all() if p.pk in still_teaching])
        copied_sessions += 1
    audit.record(
        ACTIVITY_DUPLICATED,
        actor=by,
        target=copy,
        details={
            "original": original.pk,
            "days": days,
            "sessions": copied_sessions,
            "blocks": len(blocks),
        },
        request=request,
    )
    if copy.kind == Activity.Kind.COURSE:
        current = catalogue.price_on(copy.catalogue_entry, today or timezone.localdate())
        if (current.member_cents, current.non_member_cents) != (
            copy.price_member_cents,
            copy.price_non_member_cents,
        ):
            services._notify_price_override(copy, by=by, catalogue_price=current)
    extensions.activity_duplicated.send(sender=Activity, original=original, copy=copy, by=by)
    return copy
