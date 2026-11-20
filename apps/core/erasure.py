"""Sol·licitud d'esborrat de les dades d'una persona (P-M01-F, passos 3 a 5; T-M01-22; decisió
028; HU-19 de la spec 00).

- **Demanar-la** (`request_erasure`): la persona, des del perfil. La reautenticació (RN-M01-57,
  `accounts.reauth.require_recent_auth` amb `minutes=0`) la fa la vista, a la mateixa petició.
- **Atendre-la** (`approve`, `reject`): qui té M11 (`core.gdpr.handle`) amb edició; sense permís,
  «no trobat». Qui és el responsable RGPD és de la junta (Q-15): aquí només compta el permís.
  Ningú no resol la seva pròpia sol·licitud: l'intent es rebutja i queda al registre. La vista
  torna a demanar la contrasenya i el codi abans d'aprovar, perquè no es pot desfer.
- **Aprovar és executar**, en una sola transacció: correu de confirmació a la cua (abans
  d'anonimitzar: RN-A14), `privacy.anonymise_person` i la sol·licitud «executada». Si un pas
  falla, no queda res fet i la sol·licitud continua pendent.
- **No s'executa** (`blockers`) si la persona té càrrecs pendents o retornats: què se n'ha de fer
  no està decidit (CA-19.7, Q-14 [A verificar: gestoria]) i aquí no se'n simula cap regla. Tampoc
  si desactivar-ne el compte deixés la plataforma sense cap administrador operatiu (RN-RP-13).
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from . import audit, mail, privacy
from .models import Charge, ErasureRequest, Person
from .permissions import has_perm

HANDLE_PERMISSION = "core.gdpr.handle"  # M11
DONE_EMAIL = "esborrat-fet"
REJECTED_EMAIL = "esborrat-rebutjat"
OPEN_CHARGE = (Charge.Status.PENDING, Charge.Status.RETURNED)
S = ErasureRequest.Status


class ErasureNotAllowed(ValidationError):
    """La sol·licitud no es pot resoldre en l'estat actual."""


class OwnErasureRequest(PermissionDenied):
    """Conflicte d'interès: el compte és de la persona que demana l'esborrat."""


def pending_request(person) -> ErasureRequest | None:
    return person.erasure_requests.filter(status=S.PENDING).first()


def request_erasure(person, *, by, request=None) -> tuple[ErasureRequest, bool]:
    """Crea la sol·licitud pendent de la persona i la registra. Si ja n'hi ha una de pendent, la
    torna sense crear-ne cap altra. Torna (sol·licitud, creada)."""
    with transaction.atomic():
        # Dues peticions alhora de la mateixa persona: la segona espera i troba la primera.
        Person.objects.select_for_update().filter(pk=person.pk).first()
        existing = pending_request(person)
        if existing is not None:
            return existing, False
        created = ErasureRequest.objects.create(
            person=person, requested_by=by, channel=ErasureRequest.Channel.WEB
        )
        audit.record(
            audit.Action.ERASURE_REQUESTED,
            actor=by,
            target=created,
            details={"channel": created.channel},
            request=request,
        )
    return created, True


# --- Registrar-la en persona (T-M01-22c; 085, A-2) -------------------------------------------

REGISTER_PERMISSION = "core.gdpr.register_in_person"  # M11b (P-417)


def is_under_14(person, today=None) -> bool:
    """Un menor de 14 anys no té compte personal (Q-012): els seus drets es demanen en persona."""
    from apps.accounts.invitations import MIN_AGE

    from .persons import age_on

    if person.birth_date is None:
        return False
    return age_on(person.birth_date, today or timezone.localdate()) < MIN_AGE


def can_register_in_person(person, by, permissions=None) -> bool:
    return (
        has_perm(by, REGISTER_PERMISSION, write=True, permissions=permissions)
        and person.status == Person.Status.ACTIVE
        and person.pk != by.person_id
        and is_under_14(person)
    )


def register_in_person(person, *, by, guardian_checked, request=None) -> ErasureRequest:
    """La secretaria registra la sol·licitud d'esborrat que el pare, la mare o el tutor legal d'un
    menor de 14 anys ha fet en persona (085, A-2). Queda pendent i l'atén qui té M11, com la de la
    web. Sense M11b, «no trobat»; ningú no la registra per a si mateix."""
    if not has_perm(by, REGISTER_PERMISSION, write=True):
        raise Http404
    if person.pk == by.person_id:
        raise ErasureNotAllowed(_("No pots registrar una sol·licitud per a tu mateix."))
    if person.status != Person.Status.ACTIVE or not is_under_14(person):
        raise ErasureNotAllowed(
            _("Només es registra en persona la sol·licitud d'un menor de 14 anys.")
        )
    if not guardian_checked:
        raise ErasureNotAllowed(
            _("Cal comprovar la identitat del pare, la mare o el tutor legal que ho demana.")
        )
    with transaction.atomic():
        Person.objects.select_for_update().filter(pk=person.pk).first()
        if pending_request(person) is not None:
            raise ErasureNotAllowed(_("Aquesta persona ja té una sol·licitud d'esborrat pendent."))
        created = ErasureRequest.objects.create(
            person=person, requested_by=by, channel=ErasureRequest.Channel.IN_PERSON
        )
        audit.record(
            audit.Action.ERASURE_REQUESTED,
            actor=by,
            target=created,
            details={"channel": created.channel, "guardian_checked": True},
            request=request,
        )
    return created


# --- Atendre-la (P-M01-F, pas 4) ------------------------------------------------------------


def blockers(person) -> list[str]:
    """Per què no es pot aprovar ara l'esborrat d'aquesta persona (llista buida: es pot). Frases
    sense cap dada personal ni cap import."""
    found = []
    if person.charges.filter(status__in=OPEN_CHARGE).exists():
        found.append(
            _(
                "Té càrrecs pendents de pagament. Què se n'ha de fer en un esborrat encara no "
                "està decidit (pendent de la gestoria): la sol·licitud no es pot aprovar fins "
                "que estiguin pagats o anul·lats."
            )
        )
    return [*found, *privacy.blockers(person)]


def ensure_can_resolve(erasure_request, by, *, request=None) -> None:
    """Sense M11 amb edició (o amb un compte que no és actiu): «no trobat». La sol·licitud
    pròpia es rebutja i l'intent queda al registre. Cal cridar-lo abans d'obrir la transacció de
    l'operació, perquè l'intent registrat no es desfaci amb ella."""
    if not has_perm(by, HANDLE_PERMISSION, write=True):
        raise Http404
    if erasure_request.person_id == by.person_id:
        audit.record(
            audit.Action.ERASURE_OWN_REJECTED, actor=by, target=erasure_request, request=request
        )
        raise OwnErasureRequest(_("No pots resoldre la teva pròpia sol·licitud d'esborrat."))


def _lock_pending(erasure_request) -> tuple[Person, ErasureRequest]:
    # Primer la persona, com `request_erasure` i els serveis que l'editen.
    person = Person.objects.select_for_update().get(pk=erasure_request.person_id)
    locked = ErasureRequest.objects.select_for_update().get(pk=erasure_request.pk)
    if locked.status != S.PENDING:
        raise ErasureNotAllowed(_("Aquesta sol·licitud ja està resolta."))
    return person, locked


def _notify(person, template, context=None) -> None:
    """Avís a qui ho va demanar: al correu d'entrada del seu compte personal i, si no en té, al
    de contacte. Sense cap dada de la persona al text, tret del motiu d'un rebuig."""
    personal = person.accounts.filter(kind="personal").first()
    to = personal.login if personal else person.contact_email
    if to:
        mail.queue_email(template, to=to, person=person, context=context or {})


def reject(erasure_request, *, by, reason, request=None) -> ErasureRequest:
    """Rebutja la sol·licitud amb motiu obligatori. La persona continua activa i rep un correu
    amb el motiu i amb la manera de reclamar (decisió 085, A-3; article 12.4 del RGPD)."""
    ensure_can_resolve(erasure_request, by, request=request)
    reason = (reason or "").strip()
    if not reason:
        raise ErasureNotAllowed(_("Escriu el motiu del rebuig."))
    with transaction.atomic():
        person, locked = _lock_pending(erasure_request)
        locked.status = S.REJECTED
        locked.resolved_by = by
        locked.resolved_at = timezone.now()
        locked.rejection_reason = reason
        locked.save()
        audit.record(
            audit.Action.ERASURE_REJECTED,
            actor=by,
            target=locked,
            field="status",
            old=S.PENDING,
            new=S.REJECTED,
            reason=reason,
            request=request,
        )
        _notify(person, REJECTED_EMAIL, {"reason": reason})
    erasure_request.refresh_from_db()
    return erasure_request


def approve(erasure_request, *, by, request=None) -> ErasureRequest:
    """Aprova la sol·licitud i executa l'esborrat (P-M01-F, passos 4 i 5; CA-M01-19, CA-19.1 a
    CA-19.4). Tot o res. Les dues entrades del registre s'escriuen després d'anonimitzar: només
    porten estats i la referència."""
    ensure_can_resolve(erasure_request, by, request=request)
    with transaction.atomic():
        person, locked = _lock_pending(erasure_request)
        found = blockers(person)
        if found:
            raise ErasureNotAllowed(found)
        locked.status = S.APPROVED
        locked.resolved_by = by
        locked.resolved_at = timezone.now()
        locked.save()
        _notify(person, DONE_EMAIL)  # abans d'anonimitzar: el que ja és a la cua surt (RN-A14)
        anonymised = privacy.anonymise_person(person, by=by, request=request)
        audit.record(
            audit.Action.ERASURE_APPROVED,
            actor=by,
            target=locked,
            field="status",
            old=S.PENDING,
            new=S.APPROVED,
            request=request,
        )
        locked.status = S.EXECUTED
        locked.executed_at = timezone.now()
        locked.save()
        audit.record(
            audit.Action.ERASURE_EXECUTED,
            actor=by,
            target=locked,
            field="status",
            old=S.APPROVED,
            new=S.EXECUTED,
            details={"anonymous_ref": anonymised.anonymous_ref},
            request=request,
        )
    erasure_request.refresh_from_db()
    return erasure_request
