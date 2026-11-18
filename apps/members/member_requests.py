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
- El suplement venç els dies de VC-53 (ajust, T-M01-32) després d'aprovar-lo; vençut, l'anul·la
  qui té P7a (075, RN-M01-82) o P8 amb edició (`cancel_overdue_supplement`). Mai sol.
- Ruta `/gestio/socis/sollicituds/` confirmada (Q-052): el President hi resol amb P3a i P7.

Pas de ple dret a simpatitzant (073 i 079, RN-M01-73 i RN-M01-93; T-M01-42):
- El demana un soci de ple dret actiu (`request_downgrade`), en qualsevol moment del període, sense
  suplement ni càrrec. Mentre és pendent, el soci el pot retirar (`withdraw_downgrade`: queda
  «cancel·lada», amb registre) i en pot fer un altre; és l'única sol·licitud que el soci retira.
- La secretaria l'accepta o el rebutja amb P7 (`approve_type_change`, `reject`). Acceptar-lo **no
  canvia el tipus** ni crea cap càrrec: el canvi s'aplica en renovar (T-M01-43). Si la quota de
  renovació ja s'ha generat i no s'ha pagat ni enviat al banc, es torna a generar a preu de
  simpatitzant (085, T-5; `_reprice_renewal_fee`). El dia que venç, `apply_due_downgrades`
  canvia el tipus.
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
from . import settings as values
from .fee_rules import SUPPORTER, local_today
from .models import AnnualFee, FeeReminder, Member, MemberRequest, MembershipType
from .services import (
    _change_status,
    _change_type,
    _check_account_active,
    ensure_not_own_member,
)

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
    pending = downgrades(member).filter(status=RS.APPROVED, effective_on__isnull=True)
    # Només el de la condició de soci actual: un pas acceptat abans de l'última baixa no compta,
    # encara que la baixa no l'hagi cancel·lat (readmissió; RN-M01-98).
    left_at = (
        member.status_changes.filter(to_status=Member.Status.LEFT)
        .order_by("-created_at")
        .values_list("created_at", flat=True)
        .first()
    )
    if left_at is not None:
        pending = pending.filter(resolved_at__gt=left_at)
    return pending.first()


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
    els dies de VC-53 vigents avui (RN-M01-76 i 106), i deixa la sol·licitud aprovada sense data
    efectiva; el canvi es fa quan es paga (`on_fee_paid`). Amb una quota sense pagar, es rebutja
    (RN-M01-75).

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
            # `_lock_pending` ja ha bloquejat el soci; es torna a dir aquí perquè la quota es
            # canvia amb la mateixa fila bloquejada que `generate_due_fees` (cap quota doble).
            Member.objects.select_for_update(of=("self",)).get(pk=member.pk)
            _reprice_renewal_fee(member, locked, by=by, request=request)
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
            due_on=today + datetime.timedelta(days=values.supplement_due_days(today)),
            by=by,
        )
        _close(locked, RS.APPROVED, by=by, reason=(reason or "").strip(), request=request)
        MemberRequest.objects.filter(pk=locked.pk).update(supplement_fee=fee)
    member_request.refresh_from_db()
    return fee


RENEWAL_FEE_IN_PROCESS = "members.downgrade.renewal_fee_in_process"
RENEWAL_FEE_LINKED = "members.downgrade.renewal_fee_linked"
DOWNGRADE_CARD_FAILED = "members.downgrade.card_failed"
DOWNGRADES_ORIGIN = "members.apply_due_downgrades"


def link_renewal_fee(change, fee, *, by, request=None) -> None:
    """Lliga el pas acceptat a la quota de la renovació en què s'aplicarà, amb el valor anterior
    al registre. La criden la generació de renovacions i l'acceptació del pas."""
    old = MemberRequest.objects.filter(pk=change.pk).values_list("renewal_fee_id", flat=True)[0]
    MemberRequest.objects.filter(pk=change.pk).update(renewal_fee=fee)
    audit.record(
        RENEWAL_FEE_LINKED,
        actor=by,
        target=change,
        field="renewal_fee",
        old=old,
        new=fee.pk,
        request=request,
    )


def _in_payment(charge) -> bool:
    """No és pendent, té algun pagament o un intent obert: d'un altre mètode (targeta, Bizum o
    remesa), o de la targeta guardada si ja ha arribat al proveïdor. Una targeta que no ha
    cobrat (avís de rebutjada o caducada) no compta. Aleshores ja no s'anul·la ni es torna a
    generar. `charge` ha de ser la fila bloquejada."""
    from apps.payments.models import AttemptStatus, SavedCardAttempt

    open_attempts = (
        AttemptStatus.CREATED,
        AttemptStatus.IN_PROGRESS,
        AttemptStatus.SENT_TO_BANK,
        AttemptStatus.TO_REVIEW,
    )
    attempts = charge.attempts.filter(status__in=open_attempts)
    saved = SavedCardAttempt.objects.filter(attempt__in=attempts)
    return bool(
        charge.status != Charge.Status.PENDING
        or charges.active_payments(charge)
        or attempts.exclude(pk__in=saved.values("attempt_id")).exists()
        or saved.filter(reached_provider=True).exists()
    )


def _renewal_fee(member) -> AnnualFee | None:
    """La quota de la renovació que ve: una quota anual no anul·lada que encara no ha vençut
    (la que `generate_due_fees` ha generat, o una de pagada abans d'hora). Una quota vençuda és
    la del període en curs: no es lliga ni es torna a generar mai (res de retroactiu); el pas
    s'aplica a la renovació següent."""
    return (
        AnnualFee.objects.filter(
            member=member, kind=AnnualFee.Kind.ANNUAL, due_on__gt=local_today()
        )
        .exclude(charge__status=Charge.Status.CANCELLED)
        .order_by("-due_on")
        .first()
    )


def _reprice_renewal_fee(member, change, *, by, request=None) -> None:
    """085, T-5: si el pas s'accepta amb la quota de renovació ja generada, sense pagar ni enviar
    al banc, s'anul·la i se'n genera una a preu de simpatitzant, amb el mateix venciment i els
    recordatoris ja enviats. Si ja està pagada, retornada o en curs de pagament (llegit amb el
    càrrec bloquejat), no es toca (P-334, opció per defecte): el pas s'hi lliga igualment, de
    manera que el tipus canvia el dia de la renovació, queda al registre i s'avisa qui pot
    editar les quotes."""
    fee = _renewal_fee(member)
    if fee is None:
        return  # encara no s'ha generat: ho farà `generate_due_fees` amb el preu nou
    charge = Charge.objects.select_for_update().get(pk=fee.charge_id)
    if _in_payment(charge):
        audit.record(RENEWAL_FEE_IN_PROCESS, actor=by, target=fee, request=request)
        fees.notify_fee_editors(fee, fees.NOTICE_DOWNGRADE_FULL_PRICE)
        link_renewal_fee(change, fee, by=by, request=request)
        return
    charges.cancel(
        charge,
        _("Pas a simpatitzant acceptat: es genera la quota a preu de simpatitzant (085, T-5)."),
        by=by,
    )
    new = fees.issue_annual_fee(
        member, period=fee.period, due_on=fee.due_on, by=by, fee_type=change.requested_type
    )
    FeeReminder.objects.bulk_create(
        FeeReminder(fee=new, offset_days=sent.offset_days, sent_on=sent.sent_on)
        for sent in FeeReminder.objects.filter(fee=fee)
    )
    link_renewal_fee(change, new, by=by, request=request)


def _notify_cancelled_renewal_fees(today) -> None:
    """Un pas lligat a una quota anul·lada per un altre camí (correcció, exempció) que ningú no
    ha substituït quan arriba la renovació: s'avisa una sola vegada qui pot editar les quotes.
    Si la generació en fa una de nova, la torna a lligar i el pas s'aplica amb aquella."""
    from apps.core.models import AuditEntry

    stuck = MemberRequest.objects.filter(
        kind=K.CHANGE_TYPE,
        requested_type__code=SUPPORTER,
        status=RS.APPROVED,
        effective_on__isnull=True,
        renewal_fee__due_on__lte=today,
        renewal_fee__charge__status=Charge.Status.CANCELLED,
    ).select_related("renewal_fee__member")
    for item in stuck:
        fee = item.renewal_fee
        if AuditEntry.objects.filter(
            action=fees.NOTICE_SENT,
            target_type=AnnualFee._meta.label_lower,
            target_id=str(fee.pk),
            details__event=fees.NOTICE_DOWNGRADE_FEE_CANCELLED,
        ).exists():
            continue
        fees.notify_fee_editors(fee, fees.NOTICE_DOWNGRADE_FEE_CANCELLED)


def apply_due_downgrades(today=None) -> list[MemberRequest]:
    """Tasca diària (073; RN-M01-73, CA-M01-69): el dia que venç la quota de renovació lligada al
    pas, el tipus canvia amb aquella data efectiva, amb historial i registre, i carnet nou si en
    tenia un. La quota anterior no es toca. Idempotent: `effective_on`, comprovat amb la fila
    bloquejada, marca el pas com a aplicat i `accepted_downgrade` ja no el troba. Si el soci ja
    és simpatitzant (canviat a mà), només es marca. El carnet va a part: si falla, el canvi de
    tipus es manté i l'error queda al registre. Un error en un soci queda al registre de
    l'aplicació i es continua amb els altres."""
    today = today or local_today()
    by = audit.system(DOWNGRADES_ORIGIN)
    due = (
        MemberRequest.objects.filter(
            kind=K.CHANGE_TYPE,
            requested_type__code=SUPPORTER,
            status=RS.APPROVED,
            effective_on__isnull=True,
            renewal_fee__due_on__lte=today,
        )
        .exclude(renewal_fee__charge__status=Charge.Status.CANCELLED)
        .order_by("pk")
    )
    applied = []
    for item in due:
        try:
            with transaction.atomic():
                member = (
                    Member.objects.select_for_update(of=("self",))
                    .select_related("type")
                    .get(pk=item.member_id)
                )
                locked = MemberRequest.objects.select_for_update().get(pk=item.pk)
                if locked.effective_on is not None or locked != accepted_downgrade(member):
                    continue  # ja aplicat, o d'abans d'una baixa (no compta)
                renews_on = locked.renewal_fee.due_on
                changed = member.type_id != locked.requested_type_id
                if changed:
                    _change_type(
                        member,
                        locked.requested_type,
                        by=by,
                        effective_on=renews_on,
                        reason=_("Pas a simpatitzant en renovar la quota (073)."),
                    )
                locked.effective_on = renews_on
                locked.save(update_fields=["effective_on"])
                if changed and member.status == Member.Status.ACTIVE:
                    _replace_card_after_downgrade(member, locked, by=by)
        except Exception:
            logger.exception("Pas a simpatitzant %s no aplicat", item.pk)
            continue
        applied.append(locked)
    try:
        _notify_cancelled_renewal_fees(today)
    except Exception:
        logger.exception("Avís de quotes de renovació anul·lades no enviat")
    return applied


def _replace_card_after_downgrade(member, change, *, by) -> None:
    """Carnet nou pel canvi de tipus, en un punt de desat propi: si falla, el canvi de tipus
    continua fet i l'error queda al registre d'activitat i al de l'aplicació."""
    try:
        with transaction.atomic():
            if cards.active_card(member):
                cards.replace_card(member, by=by, reason=_("Carnet nou pel canvi de tipus."))
    except Exception as exc:
        logger.exception("Carnet nou del pas a simpatitzant %s no emès", change.pk)
        audit.record(
            DOWNGRADE_CARD_FAILED, actor=by, target=change, details={"error": type(exc).__name__}
        )


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
