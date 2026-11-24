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
- **Fotos dels carnets** (T-M02-43; RN-M02-48 i 54; P-552): a l'exportació, només les dades
  de cada foto (titulació, cara i data); la foto es descarrega a part per la vista amb registre.
  En anonimitzar, se n'esborren les files; el fitxer el fa caducar la 00 (`ERASABLE_KINDS`).
- **Inscripcions i assistència** (T-M02-16c; L-M02-07): a l'exportació, les seves inscripcions
  (activitat, estat, canal, preu, data i motiu de la cancel·lació) i la seva assistència (activitat,
  dia i si hi era). En anonimitzar, el motiu de la cancel·lació (text lliure, que pot dir alguna
  cosa de la persona) se substitueix per un text neutre; l'estat, el preu i l'assistència es
  queden.
"""

from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from apps.core import audit

from . import states
from .attendance import day_of
from .models import (
    Activity,
    Attendance,
    CertificationCardPhoto,
    DiverCertification,
    Enrolment,
    PracticeAssessment,
    ReinforcementRequest,
    Session,
)

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
        # T-M02-43 (P-552): les dades de la foto; la foto, des de «Les meves titulacions».
        "fotos_dels_carnets": [
            {
                "titulacio": str(p.certification.level or p.certification.speciality or ""),
                "cara": p.get_side_display(),
                "pujada_el": p.uploaded_at,
            }
            for p in CertificationCardPhoto.objects.filter(certification__person=person)
            .select_related("certification__level", "certification__speciality")
            .order_by("uploaded_at", "pk")
        ],  # fmt: skip
        "sessions_on_fa_classe": [
            {"activitat": s.activity.title, "comenca": s.starts_at, "classe": s.get_kind_display()}
            for s in Session.objects.filter(instructors=person).select_related("activity")
        ],
        # T-M02-17: les avaluacions de les seves pràctiques, amb l'observació.
        "avaluacions": [
            {
                "activitat": a.session.activity.title,
                "sessio": a.session.starts_at,
                "resultat": a.get_result_display(),
                "observacio": a.notes,
            }
            for a in PracticeAssessment.objects.filter(enrolment__person=person)
            .select_related("session__activity")
            .order_by("session__starts_at", "pk")
        ],  # fmt: skip
        # T-M02-18: les propostes de reforç, amb el motiu pedagògic.
        "propostes_de_reforc": [
            {
                "activitat": r.enrolment.activity.title,
                "classes": r.classes,
                "motiu": r.reason,
                "estat": r.get_status_display(),
                "preu_centims": r.price_cents,
            }
            for r in ReinforcementRequest.objects.filter(enrolment__person=person)
            .select_related("enrolment__activity")
            .order_by("created_at", "pk")
        ],  # fmt: skip
        # T-M02-16c: les seves inscripcions i la seva assistència, sense cap altra persona.
        "inscripcions": [
            {
                "activitat": e.activity.title,
                "estat": e.get_status_display(),
                "canal": e.get_channel_display(),
                "preu_centims": e.price_cents,
                "inscrita_el": e.created_at,
                "motiu_de_la_cancellacio": e.cancelled_reason,
            }
            for e in Enrolment.objects.filter(person=person)
            .select_related("activity")
            .order_by("created_at", "pk")
        ],  # fmt: skip
        "assistencia": [
            {
                "activitat": a.enrolment.activity.title,
                "dia": day_of(a.enrolment.activity, a.session),
                "hi_era": a.present,
            }
            for a in Attendance.objects.filter(enrolment__person=person)
            .select_related("enrolment__activity", "session")
            .order_by("enrolment__activity__starts_on", "session__starts_at", "pk")
        ],  # fmt: skip
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
    # T-M02-43 (RN-M02-54): les fotos dels carnets s'esborren al moment. La 00 fa caducar els
    # fitxers (`ERASABLE_KINDS`) a la mateixa transacció i els esborra en confirmar-la.
    CertificationCardPhoto.objects.filter(certification__person=person).delete()
    # T-M02-16c: el motiu de la cancel·lació és text lliure; l'estat i el preu es queden. Una
    # inscripció cancel·lada ha de tenir motiu (restricció de la base de dades): un text neutre.
    Enrolment.objects.filter(person=person).exclude(cancelled_reason="").update(
        cancelled_reason=_("Esborrat RGPD de la persona.")
    )
    # T-M02-17: l'observació pot dir alguna cosa de la persona; el resultat es queda.
    PracticeAssessment.objects.filter(enrolment__person=person).exclude(notes="").update(notes="")
    # T-M02-18: el motiu del reforç també pot dir alguna cosa de la persona.
    ReinforcementRequest.objects.filter(enrolment__person=person).exclude(reason="").update(
        reason=""
    )
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
