"""Resultat del curs, certificat i titulació del club (T-M02-19 i part de la T-M02-31; P-M02-F
passos 5 i 6; RN-M02-16 i RN-M02-31; CA-M02-19; AC12 i AC13). Portat de la branca aparcada.

- **Apte o no apte** (AC12; qui fa classe a l'activitat): l'instructor registra el resultat final
  de l'alumne. «No apte» demana un motiu. Ningú no es posa apte a si mateix: es rebutja i queda al
  registre (M02-4). Es pot corregir mentre no s'hagi emès el certificat.
- **Certificat** (AC13): només per a un alumne **apte** (CA-M02-19). Número únic `C-AAAA-NNNN`
  (l'any i un comptador que comença a 0001 cada any; VC-26, format al codi) [A validar: junta,
  S-M02-09]. És un certificat del club: la titulació oficial es tramita fora (036; addenda de la
  104 per al seguiment).
- **Titulació del club** (RN-M02-31): en emetre'l es crea la titulació de la persona amb origen
  «curs del club», «C.R.I.S.» com a emissor, la data, l'instructor, el nivell o l'especialitat i
  el número del certificat, lligada al resultat del curs.

**Concrecions** (com a la branca aparcada): el «PDF» és la impressió del navegador de la pàgina
del certificat (com el carnet del soci, decisió 079), sense cap fitxer desat; `certificate` en
dona les dades. El nivell que dona un curs es tria de la llista (per defecte, el que es diu com
el text de la fitxa); un curs del catàleg d'especialitats dona aquella especialitat. Un cop emès,
el certificat no es torna a emetre ni canvia de número.

**Fora d'aquesta peça:** el correu a l'alumne (T-M02-21), la primera estrella (T-M02-45) i les
pantalles.
"""

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit

from . import assessment, permissions
from .models import (
    Activity,
    CertificationLevel,
    CourseOutcome,
    DiverCertification,
    Enrolment,
    TrainingCatalogueEntry,
)

S = Enrolment.Status
O = CourseOutcome.Result  # noqa: E741
OUTCOME_RECORDED = "activities.outcome.recorded"
CERTIFICATE_ISSUED = "activities.certificate.issued"
ISSUER = "C.R.I.S."
MAX_REASON = CourseOutcome._meta.get_field("reason").max_length
DECIDABLE = (
    Activity.Status.REGISTRATION_CLOSED,
    Activity.Status.IN_PROGRESS,
    Activity.Status.DONE,
)


def outcome_of(enrolment) -> CourseOutcome | None:
    return CourseOutcome.objects.filter(enrolment=enrolment).first()


def record_outcome(enrolment, *, result, by, reason="", request=None) -> CourseOutcome:
    """L'instructor registra apte o no apte (P-M02-F pas 5)."""
    activity = enrolment.activity
    permissions.require(by, permissions.OUTCOME, activity, request=request)
    assessment.reject_own(by, enrolment, what="outcome", request=request)
    if activity.kind != Activity.Kind.COURSE:
        raise ValidationError(_("Només els cursos tenen resultat."))
    if activity.status not in DECIDABLE:
        raise ValidationError(_("Encara no es pot posar el resultat d'aquest curs."))
    if result not in O.values:
        raise ValidationError(_("Resultat desconegut."))
    reason = (reason or "").strip()
    if result == O.FAIL and not reason:
        raise ValidationError(_("Per posar «no apte» cal un motiu."))
    if len(reason) > MAX_REASON:
        raise ValidationError(
            _("El motiu no pot passar de %(max)s caràcters.") % {"max": MAX_REASON}
        )
    with transaction.atomic():
        row = Enrolment.objects.select_for_update(of=("self",)).get(pk=enrolment.pk)
        if row.status != S.CONFIRMED:
            raise ValidationError(_("Només té resultat qui té la inscripció confirmada."))
        outcome = CourseOutcome.objects.select_for_update().filter(enrolment=row).first()
        if outcome is not None and outcome.certificate_number:
            raise ValidationError(_("El certificat ja s'ha emès: el resultat no es pot canviar."))
        if outcome is not None and (outcome.result, outcome.reason) == (result, reason):
            return outcome
        old = outcome.result if outcome is not None else None
        outcome = outcome or CourseOutcome(enrolment=row)
        outcome.result, outcome.reason = result, reason
        outcome.decided_by, outcome.decided_at = by, timezone.now()
        outcome.save()
        audit.record(
            OUTCOME_RECORDED, actor=by, target=outcome, field="result", old=old, new=result,
            reason=reason, details={"enrolment": row.pk}, request=request,
        )  # fmt: skip
        return outcome


def _next_number(year: int) -> str:
    """`C-AAAA-NNNN`. Dins d'una transacció, amb un pany: dos certificats alhora no reben el
    mateix número."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ["activities.certificate"])
    prefix = f"C-{year}-"
    last = (
        CourseOutcome.objects.filter(certificate_number__startswith=prefix)
        .order_by("-certificate_number")
        .values_list("certificate_number", flat=True)
        .first()
    )
    number = int(last.rsplit("-", 1)[1]) + 1 if last else 1
    return f"{prefix}{number:04d}"


def default_level(activity) -> CertificationLevel | None:
    """El nivell de la llista que es diu com el text de la fitxa del curs, si n'hi ha un."""
    entry = activity.catalogue_entry
    if entry.kind != TrainingCatalogueEntry.Kind.COURSE or not entry.level:
        return None
    return CertificationLevel.objects.filter(name=entry.level, active=True).first()


@transaction.atomic
def issue(enrolment, *, by, level=None, today=None, request=None) -> CourseOutcome:
    """Emet el certificat d'un alumne apte i en crea la titulació del club (CA-M02-19).
    `level`: el nivell que dona el curs, si no és una especialitat."""
    permissions.require(by, permissions.CERTIFICATE)
    today = today or timezone.localdate()
    row = (
        Enrolment.objects.select_for_update(of=("self",))
        .select_related("activity__catalogue_entry", "person")
        .get(pk=enrolment.pk)
    )
    activity = row.activity
    if activity.kind != Activity.Kind.COURSE:
        raise ValidationError(_("Només els cursos tenen certificat."))
    outcome = CourseOutcome.objects.select_for_update().filter(enrolment=row).first()
    if outcome is None or outcome.result != O.PASS:
        raise ValidationError(_("No es pot emetre el certificat: l'alumne no consta com a apte."))
    if outcome.certificate_number:
        return outcome
    entry, speciality = activity.catalogue_entry, None
    if entry.kind == TrainingCatalogueEntry.Kind.COURSE:
        level = level or default_level(activity)
        if level is None:
            raise ValidationError(_("Cal triar el nivell que dona aquest curs."))
        if not level.active:
            raise ValidationError(_("Aquest nivell està desactivat."))
    else:
        level, speciality = None, entry
    outcome.certificate_number = _next_number(today.year)
    outcome.certificate_issued_by, outcome.certificate_issued_at = by, timezone.now()
    outcome.save()
    certification = DiverCertification.objects.create(
        person=row.person, level=level, speciality=speciality, issuer=ISSUER,
        certificate_number=outcome.certificate_number, issued_on=today,
        source=DiverCertification.Source.CLUB_COURSE, instructor=outcome.decided_by.person,
        course_outcome=outcome,
    )  # fmt: skip
    audit.record(
        CERTIFICATE_ISSUED, actor=by, target=outcome,
        details={"enrolment": row.pk, "certificate_number": outcome.certificate_number,
                 "certification": certification.pk},
        request=request,
    )  # fmt: skip
    return outcome


def certificate(enrolment) -> dict | None:
    """Les dades del certificat d'una inscripció, per a la pàgina que s'imprimeix; `None` si
    encara no s'ha emès. Qui la mostra comprova que és de l'alumne o que té AC13."""
    outcome = (
        CourseOutcome.objects.filter(enrolment=enrolment)
        .exclude(certificate_number="")
        .select_related("decided_by__person", "certificate_issued_by__person")
        .first()
    )
    if outcome is None:
        return None
    certification = (
        DiverCertification.objects.filter(course_outcome=outcome)
        .select_related("level", "speciality")
        .first()
    )
    person = enrolment.person
    grants = ""
    if certification is not None:
        grants = (certification.level or certification.speciality).name
    return {
        "number": outcome.certificate_number,
        "name": f"{person.first_name} {person.last_name}".strip(),
        "course": enrolment.activity.title,
        "grants": grants,
        "issued_on": timezone.localdate(outcome.certificate_issued_at),
        "instructor": str(outcome.decided_by.person),
        "issued_by": str(outcome.certificate_issued_by.person),
        "issuer": ISSUER,
    }
