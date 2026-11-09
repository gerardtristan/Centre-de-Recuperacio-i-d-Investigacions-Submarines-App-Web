"""Sol·licituds de canvi de tipus i de baixa: les demana el soci (o la secretaria, una baixa per
decisió de la junta) i les resol l'administració amb P7 (T-M01-17; P-M01-B i P-M01-C; 064).

Fet aquí:
- Demanar el canvi a ple dret (P14, compte personal propi): només un soci simpatitzant actiu
  (pas 1 de P-M01-B, wireframe `socis.html#canvi-tipus`) i cap a un tipus actiu.
- Demanar la baixa (P14, propi) amb motiu obligatori i confirmació, o crear-la des de
  l'administració amb P7 (pas 1 de P-M01-C). Un soci de baixa no en pot demanar cap altra.
- Rebutjar qualsevol de les dues amb motiu (P7; 064, CA-M01-05, CA-M01-47).
- Validar una baixa (P7): estat «baixa» amb la primitiva `_change_status` de la T-M01-12, la
  data efectiva, l'historial i el registre amb el valor anterior, i un correu de confirmació.

Retoc del 09/11/2026 (072):
- Aprovar un canvi a ple dret (P7): crea el suplement, la diferència entre quotes (Q-049, 55 €),
  i el canvi és efectiu quan es paga (Q-050; `services.on_fee_paid`). Un soci de baixa no canvia
  de tipus (Q-053).
- Validar una baixa amb quotes pendents (RN-M01-20, Q-056): les pendents que vencen després de la
  data efectiva s'anul·len amb motiu; les anteriors se segueixen devent.
- Rebutjar i anul·lar quotes: només amb permís d'edició, mai amb només lectura (Q-055, Q-057).

Continua desconnectat: una data efectiva futura (la primitiva no programa canvis); el pas de ple
dret a simpatitzant a la renovació (Q-051, sense sol·licitud); la ruta definitiva i des d'on
resol el President (Q-052).

Conflicte d'interès (S-M01-22): `ensure_not_own_member` abans d'obrir la transacció, també per
rebutjar. El permís es torna a comprovar aquí, no només a la vista.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import Account
from apps.core import audit, charges, mail
from apps.core.models import Charge
from apps.core.permissions import has_perm

from . import fees
from .fee_rules import SUPPORTER, local_today
from .models import AnnualFee, Member, MemberRequest, MembershipType
from .services import _change_status, _check_account_active, ensure_not_own_member

FULL = "full"
VIEW_PERMISSION = "members.requests.view"  # P3a
RESOLVE_PERMISSION = "members.requests.resolve_change"  # P7
REQUEST_CREATED = "members.request.created"
REQUEST_RESOLVED = "members.request.resolved"
LEAVE_EMAIL = "baixa-efectiva"
RESOLVABLE = (MemberRequest.Kind.CHANGE_TYPE, MemberRequest.Kind.LEAVE)
UNPAID_CHARGE = (Charge.Status.PENDING, Charge.Status.RETURNED)
K, RS = MemberRequest.Kind, MemberRequest.Status


class RequestNotAllowed(ValidationError):
    """La sol·licitud no es pot crear o resoldre en l'estat actual."""


# --- Qui pot demanar ------------------------------------------------------------------------


def _is_own_personal(member, by) -> bool:
    return (
        isinstance(by, Account)
        and by.kind == Account.Kind.PERSONAL
        and by.person_id == member.person_id
    )


def type_change_problem(member) -> str:
    """Per què aquest soci no pot demanar el canvi a ple dret, o "" si pot (pas 1 de P-M01-B).
    El canvi de ple dret a simpatitzant no consta enlloc [A validar: junta]."""
    if member.status != Member.Status.ACTIVE:
        return _("Només un soci simpatitzant actiu pot demanar el canvi a ple dret.")
    if member.type.code != SUPPORTER:
        return _("Ja ets soci de ple dret. El canvi a simpatitzant ara no es pot demanar.")
    return ""


def _create(member, *, by, kind, channel, reason="", requested_type=None, request=None):
    try:
        with transaction.atomic():
            created = MemberRequest.objects.create(
                kind=kind,
                person_id=member.person_id,
                member=member,
                requested_type=requested_type,
                request_reason=reason,
                channel=channel,
            )
            audit.record(
                REQUEST_CREATED,
                actor=by,
                target=created,
                details={"kind": kind, "channel": channel},
                request=request,
            )
    except IntegrityError:
        # Una sola pendent de cada tipus per persona (restricció de la base de dades).
        raise RequestNotAllowed(_("Ja hi ha una sol·licitud pendent d'aquest tipus.")) from None
    return created


def request_type_change(member, *, by, request=None) -> MemberRequest:
    """El soci demana el canvi a ple dret (P14). No crea cap càrrec: l'import l'escriu qui aprova
    (RN-M01-15) i l'aprovació està desconnectada."""
    if not _is_own_personal(member, by):
        raise Http404
    _check_account_active(by)
    problem = type_change_problem(member)
    if problem:
        raise RequestNotAllowed(problem)
    target = MembershipType.objects.filter(code=FULL, active=True).first()
    if target is None:
        raise RequestNotAllowed(_("Ara no es pot demanar el canvi a ple dret."))
    return _create(
        member,
        by=by,
        kind=K.CHANGE_TYPE,
        channel=MemberRequest.Channel.WEB,
        requested_type=target,
        request=request,
    )


def request_leave(member, *, by, reason, request=None) -> MemberRequest:
    """Baixa demanada pel soci (P14, web) o creada per la secretaria per decisió de la junta
    (P7, presencial). Motiu obligatori (064)."""
    if _is_own_personal(member, by):
        channel = MemberRequest.Channel.WEB
    elif isinstance(by, Account) and has_perm(by, RESOLVE_PERMISSION, write=True):
        channel = MemberRequest.Channel.IN_PERSON
    else:
        raise Http404
    _check_account_active(by)
    reason = (reason or "").strip()
    if not reason:
        raise RequestNotAllowed(_("Escriu el motiu de la baixa."))
    if member.status == Member.Status.LEFT:
        raise RequestNotAllowed(_("Aquest soci ja és de baixa."))
    return _create(member, by=by, kind=K.LEAVE, channel=channel, reason=reason, request=request)


# --- Resoldre (P7) --------------------------------------------------------------------------


def _check_resolver(member_request, by, request) -> None:
    # Un compte no actiu, sense P7 o una sol·licitud d'alta (P3, T-M01-14): «no trobat».
    if not isinstance(by, Account) or not has_perm(by, RESOLVE_PERMISSION, write=True):
        raise Http404
    if member_request.kind not in RESOLVABLE:
        raise Http404
    ensure_not_own_member(member_request.member, by, request=request)


def _lock_pending(member_request, by) -> MemberRequest:
    # Ordre dels bloquejos de la T-M01-12: compte que actua, soci i després sol·licitud.
    _check_account_active(by, lock=True)
    Member.objects.select_for_update(of=("self",)).get(pk=member_request.member_id)
    locked = MemberRequest.objects.select_for_update().get(pk=member_request.pk)
    if locked.status != RS.PENDING:
        raise RequestNotAllowed(_("Aquesta sol·licitud ja està resolta."))
    return locked


def _close(locked, status, *, by, reason, effective_on=None, request=None) -> None:
    old = locked.status
    locked.status = status
    locked.resolution_reason = reason
    locked.resolved_by = by
    locked.resolved_at = timezone.now()
    locked.effective_on = effective_on
    locked.save(
        update_fields=["status", "resolution_reason", "resolved_by", "resolved_at", "effective_on"]
    )
    audit.record_changes(
        REQUEST_RESOLVED,
        actor=by,
        target=locked,
        changes={"status": (old, status), "effective_on": (None, effective_on)},
        reason=reason,
        request=request,
    )


def reject(member_request, *, by, reason, request=None) -> MemberRequest:
    """Rebutja un canvi de tipus o una baixa amb motiu obligatori (064, CA-M01-05)."""
    _check_resolver(member_request, by, request)
    reason = (reason or "").strip()
    if not reason:
        raise RequestNotAllowed(_("Escriu el motiu del rebuig."))
    with transaction.atomic():
        locked = _lock_pending(member_request, by)
        _close(locked, RS.REJECTED, by=by, reason=reason, request=request)
    member_request.refresh_from_db()
    return member_request


def has_unpaid_fees(member) -> bool:
    return AnnualFee.objects.filter(member=member, charge__status__in=UNPAID_CHARGE).exists()


def approve_type_change(member_request, *, by, request=None) -> AnnualFee:
    """Aprova un canvi a ple dret (P7; Q-049, Q-050, Q-053): crea el suplement i deixa la
    sol·licitud aprovada sense data efectiva; el canvi es fa quan es paga (`on_fee_paid`)."""
    _check_resolver(member_request, by, request)
    if member_request.kind != K.CHANGE_TYPE:
        raise RequestNotAllowed(_("Aquesta sol·licitud no és un canvi de tipus."))
    with transaction.atomic():
        locked = _lock_pending(member_request, by)
        member = Member.objects.select_related("person", "type").get(pk=locked.member_id)
        if member.status != Member.Status.ACTIVE:
            raise RequestNotAllowed(_("Només es pot canviar el tipus d'un soci actiu."))
        fee = fees.issue_type_change_supplement(
            member,
            locked.requested_type,
            period=local_today().year,
            due_on=local_today(),
            by=by,
        )
        _close(locked, RS.APPROVED, by=by, reason="", request=request)
        MemberRequest.objects.filter(pk=locked.pk).update(supplement_fee=fee)
    member_request.refresh_from_db()
    return fee


def _cancel_later_fees(member, effective_on, *, by, reason) -> list[int]:
    """RN-M01-20 (Q-056): anul·la amb motiu les quotes sense pagar que vencen després de la data
    efectiva de la baixa. Les anteriors es mantenen: se segueixen devent."""
    later = AnnualFee.objects.filter(
        member=member, charge__status__in=UNPAID_CHARGE, due_on__gt=effective_on
    ).select_related("charge")
    cancelled = []
    for fee in later:
        charges.cancel(fee.charge, reason, by=by)
        cancelled.append(fee.pk)
    return cancelled


def approve_leave(member_request, *, by, effective_on, reason="", request=None) -> MemberRequest:
    """Valida una baixa: el soci passa a «baixa» a la data efectiva (avui o abans), amb
    historial i registre (`_change_status`), i rep un correu. Tot en una transacció."""
    _check_resolver(member_request, by, request)
    if member_request.kind != K.LEAVE:
        raise RequestNotAllowed(_("Aquesta sol·licitud no és una baixa."))
    with transaction.atomic():
        locked = _lock_pending(member_request, by)
        member = Member.objects.select_related("person").get(pk=locked.member_id)
        _cancel_later_fees(
            member,
            effective_on,
            by=by,
            reason=_("Baixa amb data efectiva %(date)s (RN-M01-20).")
            % {"date": effective_on.strftime("%d/%m/%Y")},
        )
        _change_status(
            member,
            Member.Status.LEFT,
            by=by,
            effective_on=effective_on,
            reason=locked.request_reason,
            request=request,
        )
        _close(
            locked,
            RS.APPROVED,
            by=by,
            reason=(reason or "").strip(),
            effective_on=effective_on,
            request=request,
        )
        if member.person.contact_email:
            mail.queue_email(
                LEAVE_EMAIL,
                to=member.person.contact_email,
                person=member.person,
                context={"effective_on": effective_on},
            )
    member_request.refresh_from_db()
    return member_request
