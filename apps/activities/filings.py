"""Tramitacions a la federació: homologació i llistat (T-M02-44 i T-M02-46; addenda de la 104;
RN-M02-50, 51, 53 i 55; CA-M02-53 i 54).

- **Demanar** (`request_homologation`): el titular (compte personal propi) o qui té AC25 en nom
  seu. Només per a una titulació d'una agència diferent de la de destinació (VC-55) i sense cap
  homologació oberta. Amb VC-56 encès cal la foto de l'anvers: mentre no hi hagi fotos (T-M02-42,
  espera el sí del propietari), es rebutja; apagat, la secretaria comprova el carnet en persona.
- **Tramitar** (AC26): `requested → filed → done`; `requested` o `filed → rejected` amb motiu.
  `done` demana el nivell de destinació, el número i la data i, en una transacció, crea la
  titulació de destinació (`source = federation`, verificada per qui la marca) i verifica la
  d'origen. Una segona vegada no crea res. Rebutjar no verifica l'origen.
- **Preus** (VC-58 i VC-59): amb el cobrament apagat o un preu de 0 no hi ha cap càrrec. Mentre
  P-427 (el departament de l'ingrés) no tingui resposta, si algú encén VC-59 amb un preu més gran
  que 0 la petició es rebutja (conservador, D2).
- **Primera estrella** (`open_course_filing`, RN-M02-52, T-M02-45): en emetre el certificat d'un
  alumne apte d'una fitxa amb `official_level`, es crea la tramitació `course` `requested`, una per
  resultat. No porta cap càrrec: mentre P-427 no tingui resposta, les tramitacions de curs són
  gratuïtes encara que algú encengui VC-59 (conservador, D2). «Titulacions i llicències per
  tramitar» (`course_pending`) diu si la persona té llicència (`licences.current`) o «Cal
  llicència» (RN-M06-28).
- **Primera llicència** (RN-M02-58, RN-M06-28; T-M02-51a): si el curs la inclou
  (`includes_first_licence`), en obrir la tramitació es crea la llicència `paid` a preu 0
  (`licences.first.grant_included`) del tipus de l'ajust `licences.first_licence_type` (P-530).
  Mentre l'ajust és buit no es crea res i la llista ho diu, sense cap camí amb càrrec. Si no la
  inclou, `request_first_licence` la demana amb el càrrec habitual; per a un curs que la inclou,
  es rebutja (mai dos cobraments).
- **Llistat per a la federació** (`federation_csv`, AC26): CSV provisional de les tramitacions
  `requested` d'un tipus, sense cap foto ni document d'identitat. No es desa; l'exportació queda
  al registre amb l'empremta (com RN-M06-11). Format definitiu: P-444.

Sense correus nous. Les pantalles són de les vistes del 02.
"""

import csv
import hashlib
import io

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import Account
from apps.core import audit, business_settings
from apps.core.models import AuditEntry
from apps.licences import first
from apps.licences.models import LicenceType
from apps.licences.services import LicenceRequestError

from . import catalogue, extensions, permissions
from .models import CertificationFiling, CertificationLevel, DiverCertification

F = CertificationFiling
PHOTOS_KEY = "activities.card_photos_enabled"  # VC-56
FEES_KEY = "activities.filing_fees_enabled"  # VC-59
FEE_KEYS = {
    F.Kind.HOMOLOGATION: "activities.homologation_fee_cents",  # VC-58
    F.Kind.COURSE: "activities.course_filing_fee_cents",
}
FIRST_LICENCE_TYPE_KEY = "licences.first_licence_type"  # P-530: buit fins que es triï
COST_NOT_PLANNED = "activities.filing.licence_cost_not_planned"  # RN-M02-59: avís al tresorer
REQUESTED = "activities.filing.requested"
STATUS_CHANGED = "activities.filing.status_changed"
EXPORTED = "activities.filing.exported"


def _own_or_ac25(certification, by) -> None:
    if isinstance(by, Account) and by.kind == Account.Kind.PERSONAL:
        if by.person_id != certification.person_id:
            raise Http404
        return
    permissions.require(by, permissions.CARD_PHOTOS_MANAGE)


def request_homologation(certification, *, by, now=None, request=None) -> CertificationFiling:
    """RN-M02-50: la tramitació `requested` d'una titulació d'una altra agència."""
    _own_or_ac25(certification, by)
    now = now or timezone.now()
    target = catalogue.target_agency()
    if target is None or certification.agency_id in (None, target.pk):
        raise ValidationError(
            _("Només es pot homologar una titulació d'una agència diferent de la de destinació.")
        )
    if business_settings.get(PHOTOS_KEY):
        raise ValidationError(_("Cal la foto de l'anvers del carnet per demanar l'homologació."))
    if business_settings.get(FEES_KEY) and business_settings.get(FEE_KEYS[F.Kind.HOMOLOGATION]):
        raise ValidationError(_("Ara mateix no es poden demanar homologacions de pagament."))
    try:
        with transaction.atomic():
            filing = F.objects.create(
                kind=F.Kind.HOMOLOGATION,
                person_id=certification.person_id,
                source_certification=certification,
                status=F.Status.REQUESTED,
                requested_by=by,
                requested_at=now,
            )
    except IntegrityError as error:  # una d'oberta (o dues peticions alhora)
        raise ValidationError(_("Aquesta titulació ja té una homologació oberta.")) from error
    audit.record(
        REQUESTED, actor=by, target=filing,
        details={"kind": filing.kind, "source_certification": certification.pk},
        request=request,
    )  # fmt: skip
    return filing


def pending(kind=F.Kind.HOMOLOGATION, *, by):
    """«Homologacions pendents» (o «Titulacions i llicències per tramitar»): les obertes."""
    permissions.require(by, permissions.FILINGS, write=False)
    return (
        F.objects.filter(kind=kind, status__in=F.OPEN)
        .select_related("person", "source_certification__level", "source_certification__agency")
        .order_by("requested_at", "pk")
    )


def open_course_filing(outcome, certification, *, by, request=None) -> CertificationFiling | None:
    """RN-M02-52: la tramitació `course` de la primera estrella, si la fitxa del curs té
    `official_level`. La crida `certificates.issue`, dins la seva transacció; com que el certificat
    només s'emet una vegada, tampoc se'n crea cap segona (i la base de dades ho impedeix)."""
    level = outcome.enrolment.activity.catalogue_entry.official_level
    if level is None:
        return None
    filing = F.objects.create(
        kind=F.Kind.COURSE, person_id=certification.person_id,
        source_certification=certification, target_level=level, status=F.Status.REQUESTED,
        requested_by=by, requested_at=timezone.now(), course_outcome=outcome,
    )  # fmt: skip
    audit.record(
        REQUESTED, actor=by, target=filing,
        details={"kind": filing.kind, "course_outcome": outcome.pk}, request=request,
    )  # fmt: skip
    activity, licence_type = outcome.enrolment.activity, included_licence_type()
    if activity.includes_first_licence and licence_type is not None:
        try:
            first.grant_included(filing, licence_type, actor=by)
        except LicenceRequestError:
            return filing  # ja en té una de vigent o en tràmit: no cal cap primera llicència
        # RN-M02-59: el 09 hi suma el cost previst (o deixa COST_NOT_PLANNED al registre)
        extensions.first_licence_included.send(
            sender=CertificationFiling, activity=activity, filing=filing,
            licence_type=licence_type, by=by,
        )  # fmt: skip
    return filing


def included_licence_type() -> LicenceType | None:
    """El tipus de la primera llicència inclosa (P-530), o `None` mentre l'ajust és buit."""
    name = business_settings.get(FIRST_LICENCE_TYPE_KEY)
    return LicenceType.objects.filter(name=name, active=True).first() if name else None


def check_first_licence_type(value) -> None:
    """La comprovació de l'ajust (la registra `ActivitiesConfig.ready`): buit o un tipus actiu."""
    if value and not LicenceType.objects.filter(name=value, active=True).exists():
        raise ValidationError(_("Ha de ser el nom d'un tipus de llicència actiu."))


def _includes(filing) -> bool:
    outcome = filing.course_outcome
    return outcome is not None and outcome.enrolment.activity.includes_first_licence


def course_pending(*, by, today=None) -> list[dict]:
    """«Titulacions i llicències per tramitar» (AC26): les tramitacions `course` obertes i, per a
    cada una, l'estat de la primera llicència (`first.entry_status`: «Cal llicència» i si es pot
    demanar). En un curs que la inclou, mai el camí amb càrrec; sense el tipus triat (P-530),
    `type_missing` perquè la llista ho digui."""
    today = today or timezone.localdate()
    has_type = included_licence_type() is not None
    unplanned = set(
        AuditEntry.objects.filter(action=COST_NOT_PLANNED).values_list("target_id", flat=True)
    )
    rows = []
    filings = pending(F.Kind.COURSE, by=by).select_related(
        "target_level", "course_outcome__enrolment__activity"
    )
    for filing in filings:
        status, included = first.entry_status(filing, today), _includes(filing)
        missing = included and status.needs_licence and not has_type
        rows.append({
            "filing": filing, "needs_licence": status.needs_licence, "licence": status.licence,
            "included": included, "type_missing": missing,
            "can_request": status.can_request and not included,
            "cost_not_planned": str(filing.pk) in unplanned,  # el tresorer registra la despesa
        })  # fmt: skip
    return rows


def request_first_licence(filing, licence_type, *, by) -> object:
    """«Demana la primera llicència» amb el càrrec habitual (RN-M06-28, no inclosa). Per a un curs
    que la inclou es rebutja: mai dos cobraments (RN-M02-58). El permís (LC5) el comprova el 06."""
    if _includes(filing):
        raise ValidationError(_("La primera llicència és inclosa al curs: no es cobra a part."))
    return first.request_first(filing, licence_type, actor=by)


def _locked(filing, by):
    permissions.require(by, permissions.FILINGS)
    return F.objects.select_for_update().get(pk=filing.pk)


def _change(locked, new, *, by, reason="", details=None, request=None) -> None:
    audit.record(
        STATUS_CHANGED, actor=by, target=locked, field="status", old=locked.status, new=new,
        reason=reason, details=details, request=request,
    )  # fmt: skip
    locked.status = new


@transaction.atomic
def mark_filed(filing, *, by, now=None, request=None) -> CertificationFiling:
    locked = _locked(filing, by)
    if locked.status != F.Status.REQUESTED:
        raise ValidationError(_("Només es pot marcar tramitada una tramitació demanada."))
    _change(locked, F.Status.FILED, by=by, request=request)
    locked.filed_by, locked.filed_at = by, now or timezone.now()
    locked.save()
    return locked


@transaction.atomic
def mark_done(
    filing, *, by, target_level, number, issued_on, now=None, request=None
) -> CertificationFiling:
    """RN-M02-51 i CA-M02-53. Una tramitació ja feta no torna a crear res."""
    locked = _locked(filing, by)
    if locked.status == F.Status.DONE:
        return locked
    if locked.status not in F.OPEN:
        raise ValidationError(_("Aquesta tramitació ja està tancada."))
    number = (number or "").strip()
    target = catalogue.target_agency()
    if not isinstance(target_level, CertificationLevel) or not number or issued_on is None:
        raise ValidationError(_("Cal el nivell de destinació, el número i la data."))
    if target is None or target_level.agency_id != target.pk:
        raise ValidationError(_("El nivell ha de ser de l'agència de destinació."))
    now = now or timezone.now()
    result = DiverCertification.objects.create(
        person_id=locked.person_id, level=target_level, agency=target, number=number[:40],
        issued_on=issued_on, source=DiverCertification.Source.FEDERATION,
        verified_by=by, verified_at=now,
    )  # fmt: skip
    source = locked.source_certification
    if source is not None and not source.is_verified:
        DiverCertification.objects.filter(pk=source.pk).update(verified_by=by, verified_at=now)
    _change(locked, F.Status.DONE, by=by, details={"result": result.pk}, request=request)
    locked.target_level, locked.result_certification = target_level, result
    locked.closed_by, locked.closed_at = by, now
    locked.save()
    return locked


@transaction.atomic
def reject(filing, *, by, reason, now=None, request=None) -> CertificationFiling:
    """CA-M02-54: amb motiu obligatori; l'origen no queda verificat."""
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Per rebutjar una tramitació cal un motiu."))
    locked = _locked(filing, by)
    if locked.status not in F.OPEN:
        raise ValidationError(_("Aquesta tramitació ja està tancada."))
    _change(locked, F.Status.REJECTED, by=by, reason=reason, request=request)
    locked.reason, locked.closed_by, locked.closed_at = reason, by, now or timezone.now()
    locked.save()
    return locked


# --- Llistat per a la federació (T-M02-46; RN-M02-53) ------------------------------------------

CSV_HEADER = (
    "cognoms", "nom", "data_de_naixement", "agencia_origen", "nivell_origen", "numero_origen",
    "nivell_desti",
)  # fmt: skip


def federation_csv(kind=F.Kind.HOMOLOGATION, *, by, request=None) -> str:
    """El CSV de les tramitacions `requested` d'un tipus. Cap foto ni document d'identitat."""
    permissions.require(by, permissions.FILINGS)
    rows = (
        F.objects.filter(kind=kind, status=F.Status.REQUESTED)
        .select_related(
            "person", "target_level", "source_certification__level",
            "source_certification__agency",
        )
        .order_by("person__last_name", "person__first_name", "pk")
    )  # fmt: skip
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";", lineterminator="\n")
    writer.writerow(CSV_HEADER)
    count = 0
    for filing in rows:
        person, source = filing.person, filing.source_certification
        writer.writerow([
            person.last_name, person.first_name,
            person.birth_date.isoformat() if person.birth_date else "",
            source.agency.name if source and source.agency_id else "",
            str(source.level or source.speciality) if source else "",
            source.number if source else "",
            filing.target_level.name if filing.target_level_id else "",
        ])  # fmt: skip
        count += 1
    content = out.getvalue()
    audit.record(
        EXPORTED, actor=by,
        details={"kind": kind, "rows": count,
                 "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()},
        request=request,
    )  # fmt: skip
    return content
