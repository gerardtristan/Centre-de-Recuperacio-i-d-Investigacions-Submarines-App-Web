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

Tanda del 10/11/2026 (074, RN-M01-74 a 76):
- Baixa amb data futura: queda programada (aprovada, sense `applied_at`) i l'aplica la tasca diària
  `apply_due_leaves` una sola vegada. Aplicar-la: estat «baixa», quotes de la RN-M01-20, carnet
  revocat i correu, tot en una transacció. En validar-la, el canvi de tipus pendent es cancel·la.
- Canvi a ple dret amb una quota sense pagar: es rebutja en demanar-lo i en aprovar-lo.
- El suplement venç `SUPPLEMENT_DUE_DAYS` després d'aprovar-lo; vençut, l'anul·la qui té P7a
  (075, RN-M01-82) o P8 amb edició (`cancel_overdue_supplement`). Mai sol.
- Ruta `/gestio/socis/sollicituds/` confirmada (Q-052): el President hi resol amb P3a i P7.

Pas de ple dret a simpatitzant (073 i 079, RN-M01-73 i RN-M01-93; T-M01-42):
- El demana un soci de ple dret actiu (`request_downgrade`), en qualsevol moment del període, sense
  suplement ni càrrec. Mentre és pendent, el soci el pot retirar (`withdraw_downgrade`: queda
  «cancel·lada», amb registre) i en pot fer un altre; és l'única sol·licitud que el soci retira.
- La secretaria l'accepta o el rebutja amb P7 (`approve_type_change`, `reject`). Acceptar-lo **no
  canvia el tipus** ni crea cap càrrec, cap tasca ni cap avís: el canvi s'aplica en renovar, i això
  és de la T-M01-43 (punts 1, 5 i 7 de la 073, oberts).
- **Contracte per a la T-M01-43** (`accepted_downgrade`): un pas acceptat i encara no aplicat és
  una sol·licitud `change_type` cap al tipus simpatitzant, `approved`, amb `effective_on` buit i
  sense `supplement_fee`. Qui l'apliqui en renovar hi escriu `effective_on` (el dia de la
  renovació), i deixa de sortir.
- Una baixa validada cancel·la el pas **pendent** (RN-M01-74) i també el pas **acceptat** encara
  no aplicat (decisió 081, punt 17, opció A; RN-M01-98): passa a «cancel·lada» amb el motiu
  «baixa», el registre conserva qui l'havia acceptat i quan, i `accepted_downgrade` ja no el troba,
  de manera que la renovació (T-M01-43) no l'aplicarà. Un pas ja aplicat no es toca.

El destinatari del correu de baixa és el de `recipients.email_for` (RN-M01-78, T-M01-41).

Conflicte d'interès (S-M01-22): `ensure_not_own_member` abans d'obrir la transacció, també per
rebutjar. El permís es torna a comprovar aquí, no només a la vista.
"""

import datetime
import logging

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import Account
from apps.core import audit, charges, mail
from apps.core.models import Charge
from apps.core.permissions import has_perm

from . import cards, fees, recipients
from .fee_rules import SUPPORTER, local_today
from .models import AnnualFee, Member, MemberRequest, MembershipType
from .services import _change_status, _check_account_active, ensure_not_own_member

FULL = "full"
VIEW_PERMISSION = "members.requests.view"  # P3a
RESOLVE_PERMISSION = "members.requests.resolve_change"  # P7
CANCEL_SUPPLEMENT_PERMISSION = "members.requests.cancel_supplement"  # P7a (075)
REQUEST_CREATED = "members.request.created"
REQUEST_RESOLVED = "members.request.resolved"
LEAVE_EMAIL = "baixa-efectiva"
RESOLVABLE = (MemberRequest.Kind.CHANGE_TYPE, MemberRequest.Kind.LEAVE)
UNPAID_CHARGE = (Charge.Status.PENDING, Charge.Status.RETURNED)
K, RS = MemberRequest.Kind, MemberRequest.Status
# RN-M01-76 (074, punt 4): dies entre l'aprovació del canvi a ple dret i el venciment del
# suplement. Una sola constant: el model d'ajustos (T-AJ-01) demana declarar la clau i el permís
# amb la seva pantalla (T-AJ-02), que encara no hi és. [Efecte econòmic: A validar, tresorer]
SUPPLEMENT_DUE_DAYS = 7
LEAVES_ORIGIN = "members.apply_due_leaves"
logger = logging.getLogger(__name__)


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
    El pas contrari, de ple dret a simpatitzant, és `downgrade_problem`."""
    if member.status != Member.Status.ACTIVE or member.type.code != SUPPORTER:
        return _("Només un soci simpatitzant actiu pot demanar el canvi a ple dret.")
    if has_unpaid_fees(member):  # RN-M01-75 (L-M01-04)
        return _(
            "Tens una quota sense pagar. Quan l'hagis pagada, podràs demanar el canvi a ple dret."
        )
    return ""


def open_leaves(member):
    """Baixes pendents o programades (validades, encara sense aplicar) del soci."""
    return member.requests.filter(kind=K.LEAVE).filter(
        Q(status=RS.PENDING) | Q(status=RS.APPROVED, applied_at__isnull=True)
    )


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


# --- Pas de ple dret a simpatitzant (073; RN-M01-73 i RN-M01-93) ----------------------------


def is_downgrade(member_request) -> bool:
    """Un canvi de tipus cap a simpatitzant (073)."""
    return member_request.kind == K.CHANGE_TYPE and member_request.requested_type.code == SUPPORTER


def downgrades(member):
    return member.requests.filter(kind=K.CHANGE_TYPE, requested_type__code=SUPPORTER)


def accepted_downgrade(member) -> MemberRequest | None:
    """Contracte per a la T-M01-43: el pas a simpatitzant acceptat i encara no aplicat, o `None`.
    És la sol·licitud `change_type` cap a simpatitzant, `approved` i amb `effective_on` buit. Qui
    l'apliqui en renovar hi ha d'escriure `effective_on`; aquí no l'aplica ningú."""
    return downgrades(member).filter(status=RS.APPROVED, effective_on__isnull=True).first()


def downgrade_problem(member) -> str:
    """Per què aquest soci no pot demanar el pas a simpatitzant, o "" si pot (CA-M01-68 i 71)."""
    if member.status != Member.Status.ACTIVE or member.type.code != FULL:
        return _("Només un soci de ple dret actiu pot demanar el pas a simpatitzant.")
    if accepted_downgrade(member) is not None:
        return _("Ja tens el pas a simpatitzant acceptat. S'aplicarà en la pròxima renovació.")
    return ""


def request_downgrade(member, *, by, request=None) -> MemberRequest:
    """El soci de ple dret actiu demana el pas a simpatitzant (P14; CA-M01-68): queda pendent,
    sense suplement ni cap càrrec, i el tipus no canvia. Un simpatitzant, un soci que no és actiu
    o un que ja en té un de pendent o d'acceptat no el pot demanar (CA-M01-71)."""
    if not _is_own_personal(member, by):
        raise Http404
    _check_account_active(by)
    problem = downgrade_problem(member)
    if problem:
        raise RequestNotAllowed(problem)
    target = MembershipType.objects.filter(code=SUPPORTER, active=True).first()
    if target is None:
        raise RequestNotAllowed(_("Ara no es pot demanar el pas a simpatitzant."))
    return _create(
        member,
        by=by,
        kind=K.CHANGE_TYPE,
        channel=MemberRequest.Channel.WEB,
        requested_type=target,
        request=request,
    )


def withdraw_downgrade(member, *, by, request=None) -> MemberRequest:
    """El soci retira el seu pas a simpatitzant mentre és pendent (RN-M01-93, punt 4;
    CA-M01-106): passa a «cancel·lada», amb registre, i en pot fer un altre. Un cop acceptat o
    rebutjat, ja no es pot retirar. Cap altra sol·licitud no la retira el soci."""
    if not _is_own_personal(member, by):
        raise Http404
    with transaction.atomic():
        _check_account_active(by, lock=True)
        Member.objects.select_for_update(of=("self",)).get(pk=member.pk)
        locked = (
            downgrades(member).select_for_update(of=("self",)).filter(status=RS.PENDING).first()
        )
        if locked is None:
            raise RequestNotAllowed(
                _("No tens cap pas a simpatitzant pendent. Un cop acceptat, ja no es pot retirar.")
            )
        _close(locked, RS.CANCELLED, by=by, reason=_("Retirada pel soci"), request=request)
    return locked


def request_leave(member, *, by, reason, request=None) -> MemberRequest:
    """Baixa demanada pel soci (P14, web) o creada per la secretaria per decisió de la junta
    (P7, presencial). Motiu obligatori (064)."""
    if _is_own_personal(member, by):
        channel = MemberRequest.Channel.WEB
    elif isinstance(by, Account) and has_perm(by, RESOLVE_PERMISSION, write=True):
        channel = MemberRequest.Channel.IN_PERSON
        # S-M01-22: ningú no crea una baixa per al seu propi soci des de l'administració.
        ensure_not_own_member(
            member, by, request=request, message=_("No pots crear una baixa per al teu propi soci.")
        )
    else:
        raise Http404
    _check_account_active(by)
    reason = (reason or "").strip()
    if not reason:
        raise RequestNotAllowed(_("Escriu el motiu de la baixa."))
    if member.status == Member.Status.LEFT:
        raise RequestNotAllowed(_("Aquest soci ja és de baixa."))
    if open_leaves(member).filter(status=RS.APPROVED).exists():
        raise RequestNotAllowed(_("Aquest soci ja té una baixa programada."))
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
    changes = {"status": (old, status), "effective_on": (None, effective_on)}
    if old != RS.PENDING:
        # Una sol·licitud ja resolta que es torna a tancar (el pas acceptat que cancel·la una
        # baixa, decisió 081): el registre conserva qui l'havia resolt, quan i amb quin motiu.
        now = timezone.now()
        changes.update(
            {
                "resolved_by": (locked.resolved_by_id, by.pk),
                "resolved_at": (
                    locked.resolved_at.isoformat() if locked.resolved_at else None,
                    now.isoformat(),
                ),
                "resolution_reason": (locked.resolution_reason, reason),
            }
        )
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
        changes=changes,
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


def approve_type_change(member_request, *, by, reason="", request=None) -> AnnualFee | None:
    """Aprova un canvi a ple dret (P7; Q-049, Q-050, Q-053): crea el suplement, que venç d'aquí a
    `SUPPLEMENT_DUE_DAYS` (RN-M01-76), i deixa la sol·licitud aprovada sense data efectiva; el
    canvi es fa quan es paga (`on_fee_paid`). Amb una quota sense pagar, es rebutja (RN-M01-75).

    Un pas a simpatitzant (073; RN-M01-93, punt 2) s'accepta sense suplement ni cap càrrec i
    torna `None`: el tipus no canvia i la sol·licitud queda com diu `accepted_downgrade`, perquè
    la T-M01-43 l'apliqui en renovar."""
    _check_resolver(member_request, by, request)
    if member_request.kind != K.CHANGE_TYPE:
        raise RequestNotAllowed(_("Aquesta sol·licitud no és un canvi de tipus."))
    with transaction.atomic():
        locked = _lock_pending(member_request, by)
        member = Member.objects.select_related("person", "type").get(pk=locked.member_id)
        if member.status != Member.Status.ACTIVE:
            raise RequestNotAllowed(_("Només es pot canviar el tipus d'un soci actiu."))
        if is_downgrade(locked):
            if member.type.code != FULL:
                raise RequestNotAllowed(_("Aquest soci ja no és de ple dret."))
            _close(locked, RS.APPROVED, by=by, reason=(reason or "").strip(), request=request)
            member_request.refresh_from_db()
            return None
        if has_unpaid_fees(member):
            raise RequestNotAllowed(
                _(
                    "El soci té alguna quota sense pagar: el canvi a ple dret no es pot aprovar "
                    "fins que la pagui."
                )
            )
        today = local_today()
        fee = fees.issue_type_change_supplement(
            member,
            locked.requested_type,
            period=today.year,
            due_on=today + datetime.timedelta(days=SUPPLEMENT_DUE_DAYS),
            by=by,
        )
        _close(locked, RS.APPROVED, by=by, reason=(reason or "").strip(), request=request)
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


def _apply_leave(locked, *, by, request=None) -> None:
    """Fa efectiva una baixa validada (pas 3 de P-M01-C): quotes de la RN-M01-20, estat «baixa»
    amb historial i registre, carnet revocat (RN-M01-25), marca d'aplicada i correu. Qui crida
    ja és dins la transacció que bloqueja el soci i la sol·licitud."""
    effective_on = locked.effective_on
    date = effective_on.strftime("%d/%m/%Y")
    member = Member.objects.select_related("person").get(pk=locked.member_id)
    _cancel_later_fees(
        member,
        effective_on,
        by=by,
        reason=_("Baixa amb data efectiva %(date)s (RN-M01-20).") % {"date": date},
    )
    _change_status(
        member,
        Member.Status.LEFT,
        by=by,
        effective_on=effective_on,
        reason=locked.request_reason,
        request=request,
    )
    cards.revoke_card(
        member,
        by=by,
        reason=_("Baixa del soci amb data efectiva %(date)s.") % {"date": date},
        request=request,
    )
    locked.applied_at = timezone.now()
    locked.save(update_fields=["applied_at"])
    to = recipients.email_for(member.person)  # RN-M01-78
    if to:
        mail.queue_email(
            LEAVE_EMAIL,
            to=to,
            person=member.person,
            context={"effective_on": effective_on},
        )


def _cancel_pending_type_change(member, *, by, request=None) -> None:
    """RN-M01-74 (074, punt 5): en validar una baixa, el canvi de tipus pendent es cancel·la
    amb el motiu «baixa». Decisió 081, punt 17 (RN-M01-98): també el pas a simpatitzant acceptat
    i encara no aplicat; el registre guarda qui l'havia acceptat i quan."""
    pending = MemberRequest.objects.select_for_update().filter(
        member=member, kind=K.CHANGE_TYPE, status=RS.PENDING
    )
    for change in pending:
        _close(change, RS.CANCELLED, by=by, reason=_("Baixa"), request=request)
    accepted = (
        downgrades(member)
        .select_for_update(of=("self",))
        .filter(status=RS.APPROVED, effective_on__isnull=True, applied_at__isnull=True)
    )
    for change in accepted:
        _close(change, RS.CANCELLED, by=by, reason=_("Baixa"), request=request)


def approve_leave(member_request, *, by, effective_on, reason="", request=None) -> MemberRequest:
    """Valida una baixa (P7). Amb data d'avui o anterior, s'aplica ara (`_apply_leave`); amb una
    data futura, queda programada i l'aplica la tasca diària aquell dia (RN-M01-74). En tots dos
    casos es cancel·la el canvi de tipus pendent. Tot en una transacció."""
    _check_resolver(member_request, by, request)
    if member_request.kind != K.LEAVE:
        raise RequestNotAllowed(_("Aquesta sol·licitud no és una baixa."))
    if not isinstance(effective_on, datetime.date) or isinstance(effective_on, datetime.datetime):
        raise RequestNotAllowed(_("Escriu la data efectiva."))
    with transaction.atomic():
        locked = _lock_pending(member_request, by)
        member = Member.objects.get(pk=locked.member_id)
        if member.status == Member.Status.LEFT:
            raise RequestNotAllowed(_("Aquest soci ja és de baixa."))
        if member.joined_on and effective_on < member.joined_on:
            raise RequestNotAllowed(_("La baixa no pot ser anterior a la data d'alta."))
        _cancel_pending_type_change(member, by=by, request=request)
        _close(
            locked,
            RS.APPROVED,
            by=by,
            reason=(reason or "").strip(),
            effective_on=effective_on,
            request=request,
        )
        if effective_on <= local_today():
            _apply_leave(locked, by=by, request=request)
    member_request.refresh_from_db()
    return member_request


def is_scheduled(member_request) -> bool:
    """Baixa validada amb data futura que encara no s'ha aplicat."""
    return (
        member_request.kind == K.LEAVE
        and member_request.status == RS.APPROVED
        and member_request.applied_at is None
    )


def apply_due_leaves(today=None) -> list[MemberRequest]:
    """Tasca diària (RN-M01-74, CA-M01-72): aplica les baixes programades que vencen avui o abans.
    Idempotent: la marca `applied_at`, comprovada amb la fila bloquejada, impedeix aplicar-ne cap
    dues vegades. Si una no es pot aplicar (p. ex. el soci ja és de baixa), queda al registre de
    l'aplicació i es continua amb les altres."""
    today = today or local_today()
    by = audit.system(LEAVES_ORIGIN)
    due = MemberRequest.objects.filter(
        kind=K.LEAVE, status=RS.APPROVED, applied_at__isnull=True, effective_on__lte=today
    ).order_by("effective_on", "pk")
    applied = []
    for item in due:
        try:
            with transaction.atomic():
                Member.objects.select_for_update(of=("self",)).get(pk=item.member_id)
                locked = MemberRequest.objects.select_for_update().get(pk=item.pk)
                if locked.applied_at is not None:
                    continue
                _apply_leave(locked, by=by)
        except ValidationError as exc:
            logger.warning("Baixa %s no aplicada: %s", item.pk, exc.messages[0])
            continue
        applied.append(locked)
    return applied


# --- Suplement vençut (RN-M01-76, CA-M01-75) ------------------------------------------------


def supplement_overdue(fee, today=None) -> bool:
    return fee.charge.status in UNPAID_CHARGE and fee.due_on < (today or local_today())


def can_cancel_supplement(account, permissions=None) -> bool:
    """P7a (075, RN-M01-82) o P8, tots dos amb edició."""
    return isinstance(account, Account) and any(
        has_perm(account, code, write=True, permissions=permissions)
        for code in (CANCEL_SUPPLEMENT_PERMISSION, fees.EDIT_PERMISSION)
    )


def cancel_overdue_supplement(member_request, *, by, reason, request=None) -> AnnualFee:
    """Anul·la el suplement vençut i sense pagar d'un canvi aprovat, amb motiu (Q-057): ho fa qui
    té P7a (la secretaria, 075) o P8 amb edició, amb el nucli de `fees.cancel_fee` (motiu,
    conflicte d'interès i anul·lació del càrrec, mai esborrat). P7a només serveix aquí: per a
    qualsevol altra quota, `fees.cancel_fee` continua exigint P8. Abans del venciment, es
    rebutja: mai no s'anul·la sol."""
    if not can_cancel_supplement(by):
        raise Http404
    fee = member_request.supplement_fee
    if member_request.kind != K.CHANGE_TYPE or fee is None:
        raise Http404
    ensure_not_own_member(member_request.member, by, request=request)
    if not supplement_overdue(fee):
        raise RequestNotAllowed(_("Només es pot anul·lar un suplement vençut i sense pagar."))
    return fees.cancel_fee_checked(fee, by=by, reason=reason, request=request)
