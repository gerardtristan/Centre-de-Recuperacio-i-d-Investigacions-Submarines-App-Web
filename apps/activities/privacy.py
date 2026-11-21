"""RGPD del 02 (M02-8: `activities.export_personal_data` i `activities.anonymise`; L-M02-07;
decisió 028). Es registra a la base comuna des de `ActivitiesConfig.ready`; la 00 no importa mai
el mòdul.

Què guarda el 02 d'una persona, avui: les seves **titulacions** i el vincle amb les **sessions on
fa classe** i les **activitats de què és responsable**.

- **Exportació:** les tres coses, sense dades d'altres persones.
- **Anonimització** (amb la persona ja anonimitzada, dins la transacció de la 00): de les
  titulacions s'esborra el número, l'única dada que identifica; el nivell, la data i l'origen es
  conserven. Les activitats de què era responsable no es reassignen soles: el resum de qui aprova
  l'esborrat ho diu. Treure-la de les sessions futures on feia classe és de la T-M02-04 (decisió
  101).
- Quan hi hagi inscripcions i assistència (T-M02-11 i següents), s'hi afegiran (L-M02-07).
"""

from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from apps.core import audit

from . import states
from .models import Activity, DiverCertification, Session

CERTIFICATION_ANONYMISED = "activities.certification.anonymised"


def _certifications(person):
    return DiverCertification.objects.filter(person=person).select_related("level", "speciality")


def export(person) -> dict:
    return {
        "titulacions": [
            {
                "nivell": c.level.name if c.level_id else None,
                "especialitat": c.speciality.name if c.speciality_id else None,
                "agencia": c.agency.name if c.agency_id else None,
                "emesa_per": c.issuer,
                "numero": c.number,
                "numero_del_certificat": c.certificate_number,
                "data": c.issued_on,
                "origen": c.get_source_display(),
                "verificada": c.is_verified,
            }
            for c in _certifications(person)
        ],
        "sessions_on_fa_classe": [
            {"activitat": s.activity.title, "comenca": s.starts_at, "classe": s.get_kind_display()}
            for s in Session.objects.filter(instructors=person).select_related("activity")
        ],
        "activitats_de_que_es_responsable": [
            {"activitat": a.title, "data_d_inici": a.starts_on, "estat": a.get_status_display()}
            for a in Activity.objects.filter(responsible=person)
        ],
    }


def audit_targets(person) -> dict:
    ids = [str(pk) for pk in _certifications(person).values_list("pk", flat=True)]
    return {"activities.divercertification": ids} if ids else {}


def describe(person) -> list[str]:
    lines = []
    if count := _certifications(person).count():
        lines.append(
            ngettext(
                "Té %(count)s titulació: se n'esborrarà el número.",
                "Té %(count)s titulacions: se n'esborrarà el número.",
                count,
            )
            % {"count": count}
        )
    live = Activity.objects.filter(responsible=person, status__in=states.EDITABLE_STATUSES)
    if count := live.count():
        lines.append(
            ngettext(
                "És responsable de %(count)s activitat en preparació o en marxa: cal posar-hi "
                "una altra persona.",
                "És responsable de %(count)s activitats en preparació o en marxa: cal posar-hi "
                "una altra persona.",
                count,
            )
            % {"count": count}
        )
    return [str(line) for line in lines]


def anonymise(person, *, by, request=None) -> None:
    for certification in _certifications(person).exclude(number=""):
        certification.number = ""
        certification.save(update_fields=["number"])
        audit.record(
            CERTIFICATION_ANONYMISED,
            actor=by,
            target=certification,
            field="number",
            reason=_("Esborrat RGPD de la persona."),
            request=request,
        )
