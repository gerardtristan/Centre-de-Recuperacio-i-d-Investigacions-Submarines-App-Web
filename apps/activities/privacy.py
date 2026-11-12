"""RGPD del mòdul 02 (M02-8: `activities.export_personal_data` i `activities.anonymise`; L-M02-07;
decisió 028). El 02 les registra a la base comuna des del seu `AppConfig.ready`, i la 00 no
importa mai el mòdul.

Què guarda el 02 d'una persona, avui:

- les seves **titulacions** (`DiverCertification`);
- les **sessions on fa classe** i les **activitats de què és responsable** (el vincle, no cap
  altra dada).

**Exportació.** Les titulacions, les sessions on fa classe i les activitats de què és
responsable. Cap dada d'altres persones.

**Anonimització** (amb la persona ja anonimitzada, dins la transacció de la 00):

1. de les titulacions se n'esborra el número, que és l'única dada que identifica; el nivell, la
   data i l'origen es conserven, lligats a la persona anonimitzada;
2. surt de les sessions futures on feia classe (les passades conserven el vincle, que ja no porta
   cap nom);
3. les activitats de què era responsable no es reassignen soles: el resum de qui aprova
   l'esborrat ho diu, perquè hi posi una altra persona.

Quan existeixin inscripcions, assistència i avaluacions (T-M02-11 i següents), s'hi afegiran:
L-M02-07 diu que s'anonimitzen i que els recomptes de places no canvien.
"""

from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from . import sessions, states
from .models import Activity, DiverCertification, Session

CERTIFICATION_ANONYMISED = "activities.certification.anonymised"


def _certifications(person):
    return DiverCertification.objects.filter(person=person).select_related("level", "speciality")


def _live_responsibilities(person):
    return Activity.objects.filter(responsible=person, status__in=states.EDITABLE_STATUSES)


def export_personal_data(person) -> dict:
    """Diccionari per a l'exportació RGPD (M02-8). Només dades de la persona."""
    return {
        "titulacions": [
            {
                "nivell": c.level.name if c.level_id else None,
                "especialitat": c.speciality.name if c.speciality_id else None,
                "agencia": c.agency,
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
    """Objectes no econòmics del 02 lligats a la persona: els valors de les seves entrades del
    registre d'activitat se substitueixen per la referència."""
    ids = [str(pk) for pk in _certifications(person).values_list("pk", flat=True)]
    return {"activities.divercertification": ids} if ids else {}


def describe(person) -> list[str]:
    """Frases sense dades personals per a qui aprova l'esborrat."""
    lines = []
    count = _certifications(person).count()
    if count:
        lines.append(
            ngettext(
                "Té %(count)s titulació: se n'esborrarà el número.",
                "Té %(count)s titulacions: se n'esborrarà el número.",
                count,
            )
            % {"count": count}
        )
    teaching = sessions._future_sessions(_now()).filter(instructors=person).count()
    if teaching:
        lines.append(
            ngettext(
                "Fa classe en %(count)s sessió futura: quedarà sense instructor.",
                "Fa classe en %(count)s sessions futures: quedaran sense instructor.",
                teaching,
            )
            % {"count": teaching}
        )
    responsible = _live_responsibilities(person).count()
    if responsible:
        lines.append(
            ngettext(
                "És responsable de %(count)s activitat en preparació o en marxa: cal posar-hi "
                "una altra persona.",
                "És responsable de %(count)s activitats en preparació o en marxa: cal posar-hi "
                "una altra persona.",
                responsible,
            )
            % {"count": responsible}
        )
    return [str(line) for line in lines]


def _now():
    from django.utils import timezone

    return timezone.now()


def anonymise(person, *, by, request=None) -> None:
    """La part del 02 de l'esborrat d'una persona ja anonimitzada. Qui crida ja ha comprovat el
    permís i és dins d'una transacció: si res falla, es desfà tot."""
    from apps.core import audit

    if not person.anonymous_ref:
        raise ValueError("La persona encara no està anonimitzada.")
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
    # Una persona anonimitzada ja no pot fer classe: surt de les sessions futures.
    sessions.release_former_instructors(actor=by)
