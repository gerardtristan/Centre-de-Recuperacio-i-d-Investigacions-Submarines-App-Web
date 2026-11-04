"""Serveis d'estat i transicions del M01 (T-M01-12; RN-M01-07 a RN-M01-09; decisió 067).

Decisions de l'aprovació del pla de la T-M01-12 (planning.md, lectura de les tasques
substituïdes):

- Serveis autoritzats del mòdul (`__all__`): `mark_unpaid` i `unmark_unpaid`, amb P9.
- Primitives internes del M01 (`_change_status`, `_change_type`, `_readmit`): no comproven el
  permís del rol i no formen part del contracte de M01-8. Les crida el servei autoritzat de
  cada tasca (T-M01-14, T-M01-17, T-M01-22, T-M01-26) després de comprovar-lo. Actiu ↔ impagat
  només es fa amb P9, també si s'entra per una altra banda; baixa → pendent, només amb
  `_readmit`.
- Actor: un compte o el sistema (`audit.system(origen)`, amb `actor_account` buit a
  l'historial). El sistema no marca ni desmarca l'impagat (RN-M01-09, 040) ni readmet. Un
  compte que no és actiu no fa canvis nous (es llegeix de la base de dades dins la transacció).
- Readmissió: no abans de la data de la baixa actual (el mateix dia, sí).
- Conflicte d'interès (S-M01-22, sense excepcions): `ensure_not_own_member` registra l'intent i
  rebutja. Contracte: cada punt d'entrada el crida ABANS d'obrir la seva transacció; dins d'una
  transacció exterior que es desfà, el rebuig es manté però l'intent registrat es perd.
- Data efectiva obligatòria i no posterior a la data local del projecte (TIME_ZONE). No es
  programen canvis: una data passada canvia l'estat ara i no reconstrueix l'historial ni
  recalcula quotes ni carnets.
- Marcar o desmarcar l'impagat no toca el carnet: la validesa és de la T-M01-19.

Tot el canvi (bloqueig, validació, historial, soci i registre) és en una sola transacció; si
falla qualsevol pas, no queda res escrit.
"""

import datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import Account
from apps.core import audit
from apps.core.models import AuditEntry
from apps.core.permissions import has_perm

from .models import Member, MemberRequest, MemberStatusChange

__all__ = [
    "InactiveAccount",
    "InvalidTransition",
    "OwnMemberChange",
    "ensure_not_own_member",
    "mark_unpaid",
    "unmark_unpaid",
]

S = Member.Status

STATUS_CHANGED = "members.status_changed"
TYPE_CHANGED = "members.type_changed"
OWN_MEMBER_REJECTED = "members.own_member_change_rejected"
UNPAID_PERMISSION = "members.unpaid.mark"  # P9

# RN-M01-07. Qualsevol altre parell es rebutja (CA-M01-07).
TRANSITIONS = {
    (S.PENDING, S.ACTIVE),
    (S.ACTIVE, S.UNPAID),
    (S.UNPAID, S.ACTIVE),
    (S.PENDING, S.LEFT),
    (S.ACTIVE, S.LEFT),
    (S.UNPAID, S.LEFT),
}
UNPAID_TRANSITIONS = {(S.ACTIVE, S.UNPAID), (S.UNPAID, S.ACTIVE)}  # només amb P9
READMISSION = (S.LEFT, S.PENDING)  # 067: només amb `_readmit`


class InvalidTransition(ValidationError):
    """Transició que RN-M01-07 no permet, o dades del soci que no la deixen fer."""


class InactiveAccount(PermissionDenied):
    """El compte que actua no és actiu (desactivat o pendent): no fa canvis nous."""


class OwnMemberChange(PermissionDenied):
    """Conflicte d'interès: el compte és de la persona del soci (S-M01-22)."""


def _not_allowed(old_status, new_status) -> InvalidTransition:
    # Un valor desconegut també és una transició no permesa, no un error de programa.
    labels = dict(S.choices)
    return InvalidTransition(
        _("Un soci «%(old)s» no pot passar a «%(new)s».")
        % {"old": labels.get(old_status, old_status), "new": labels.get(new_status, new_status)}
    )


def _is_own(member, by) -> bool:
    return isinstance(by, Account) and by.person_id == member.person_id


def _check_account_active(by, *, lock=False) -> None:
    # Es llegeix de la base de dades: l'objecte pot estar desfasat. Amb `lock`, FOR NO KEY
    # UPDATE fins al final de la transacció: una desactivació simultània espera, però no les
    # claus foranes que apunten al compte (historial i registre).
    if not isinstance(by, Account):
        return
    accounts = Account.objects.filter(pk=by.pk)
    if lock:
        accounts = accounts.select_for_update(no_key=True)
    if accounts.values_list("status", flat=True).first() != Account.Status.ACTIVE:
        raise InactiveAccount(_("Aquest compte no està actiu i no pot fer canvis."))


def ensure_not_own_member(member, by, *, request=None) -> None:
    """Rebutja i registra l'intent si el compte és de la persona del soci. Cal cridar-lo
    abans d'obrir la transacció de l'operació (vegeu el docstring del mòdul). Un compte no
    actiu es rebutja abans (`InactiveAccount`), sense intent registrat, llevat que es desactivi
    just entre aquesta comprovació i la de dins la transacció, que en tot cas impedeix el canvi."""
    _check_account_active(by)
    if _is_own(member, by):
        audit.record(OWN_MEMBER_REJECTED, actor=by, target=member, request=request)
        raise OwnMemberChange(_("No pots canviar l'estat ni el tipus del teu propi soci."))


def _check_actor(by) -> None:
    # RN-M01-08: tot canvi té autor. Un compte o el sistema; ningú més.
    if isinstance(by, Account):
        return
    if isinstance(by, audit.Actor) and by.kind == AuditEntry.ActorKind.SYSTEM:
        return
    raise ValidationError(_("Cal un compte o el sistema com a autor del canvi."))


def _check_effective_on(effective_on) -> None:
    # Un `datetime` també és un `date`: es rebutja per no perdre l'hora en silenci.
    if not isinstance(effective_on, datetime.date) or isinstance(effective_on, datetime.datetime):
        raise ValidationError(_("Cal la data efectiva del canvi."))
    if effective_on > timezone.localdate():
        raise ValidationError(_("La data efectiva no pot ser posterior a avui."))


def _reason_required(from_status, to_status) -> bool:
    # El mateix que la restricció `memberstatuschange_reason_when_required` (M01-6). També
    # s'aplica a un canvi de tipus d'un soci impagat o de baixa: limitació actual del model.
    return to_status in (S.LEFT, S.UNPAID) or (from_status, to_status) == (S.UNPAID, S.ACTIVE)


def _check_readmission(member, join_request, by, effective_on) -> None:
    if not isinstance(by, Account):
        raise ValidationError(_("Una readmissió l'aprova una persona, no el sistema."))
    if join_request is None:
        raise InvalidTransition(_("Una baixa només torna a pendent amb una readmissió."))
    if (
        join_request.kind != MemberRequest.Kind.JOIN
        or join_request.person_id != member.person_id
        or join_request.status != MemberRequest.Status.PENDING
    ):
        raise InvalidTransition(
            _("La readmissió necessita una sol·licitud d'alta pendent de la mateixa persona.")
        )
    # 067: la baixa actual ha de constar a l'historial abans de buidar `left_on`. Val l'últim
    # canvi d'estat (no els canvis de tipus), no qualsevol baixa antiga.
    last = (
        member.status_changes.exclude(from_status=F("to_status"))
        .order_by("-created_at", "-id")
        .first()
    )
    if (
        member.left_on is None
        or last is None
        or last.to_status != S.LEFT
        or last.effective_on != member.left_on
    ):
        raise InvalidTransition(_("La baixa actual del soci no consta a l'historial."))
    # Revisió de la T-M01-12: no abans de la baixa actual; el mateix dia, sí.
    if effective_on < member.left_on:
        raise ValidationError(_("La readmissió no pot ser anterior a la data de la baixa."))


def _apply(
    member,
    *,
    by,
    effective_on,
    reason="",
    request=None,
    to_status=None,
    to_type=None,
    join_request=None,
    with_p9=False,
) -> Member:
    _check_actor(by)
    _check_effective_on(effective_on)
    reason = (reason or "").strip()
    with transaction.atomic():
        # Ordre dels bloquejos: compte que actua, soci i després sol·licitud. Es valida amb les
        # files bloquejades.
        _check_account_active(by, lock=True)
        # `of=("self",)`: només la fila del soci, no la del tipus que s'hi uneix.
        locked = (
            Member.objects.select_for_update(of=("self",)).select_related("type").get(pk=member.pk)
        )
        if join_request is not None:
            join_request = MemberRequest.objects.select_for_update().get(pk=join_request.pk)
        if _is_own(locked, by):  # defensa: el registre de l'intent és d'`ensure_not_own_member`
            raise OwnMemberChange(_("No pots canviar l'estat ni el tipus del teu propi soci."))

        old_status, old_type, old_left_on = locked.status, locked.type, locked.left_on
        new_status, new_type, new_left_on = old_status, old_type, old_left_on
        if to_type is not None:
            if to_type.pk == old_type.pk:
                raise InvalidTransition(_("El soci ja és d'aquest tipus."))
            new_type, action = to_type, TYPE_CHANGED
        else:
            new_status, action = to_status, STATUS_CHANGED
            pair = (old_status, new_status)
            # Amb P9 només els dos parells de l'impagat (mai activar un pendent), i aquests dos
            # només amb P9, entri qui entri.
            if pair not in TRANSITIONS | {READMISSION} or with_p9 != (pair in UNPAID_TRANSITIONS):
                raise _not_allowed(old_status, new_status)
            if with_p9 and not has_perm(by, UNPAID_PERMISSION):
                raise Http404
            if pair == READMISSION:
                _check_readmission(locked, join_request, by, effective_on)
                new_left_on = None
            if new_status == S.LEFT:
                if effective_on < locked.joined_on:
                    raise ValidationError(_("La baixa no pot ser anterior a la data d'alta."))
                new_left_on = effective_on

        if new_left_on is not None and new_status != S.LEFT:
            raise InvalidTransition(_("El soci té data de baixa però no és de baixa."))
        if _reason_required(old_status, new_status) and not reason:
            raise ValidationError(_("Aquest canvi necessita un motiu."))

        MemberStatusChange.objects.create(
            member=locked,
            from_status=old_status,
            to_status=new_status,
            from_type=old_type,
            to_type=new_type,
            effective_on=effective_on,
            reason=reason,
            actor_account=by if isinstance(by, Account) else None,
        )
        audit.record_changes(
            action,
            actor=by,
            target=locked,
            changes={
                "status": (old_status, new_status),
                "type": (old_type.code, new_type.code),
                "left_on": (old_left_on, new_left_on),
            },
            reason=reason,
            request=request,
        )
        locked.status, locked.type, locked.left_on = new_status, new_type, new_left_on
        # Mai `avatar_seed` ni cap altre camp (members/0004).
        locked.save(update_fields=["status", "type", "left_on", "updated_at"])
    member.refresh_from_db()
    return member


# --- Serveis autoritzats --------------------------------------------------------------------


def _unpaid(member, to_status, *, by, effective_on, reason, request) -> Member:
    # Abans del permís: un compte no actiu rep sempre la mateixa resposta.
    _check_account_active(by)
    if not has_perm(by, UNPAID_PERMISSION):
        raise Http404
    ensure_not_own_member(member, by, request=request)
    return _apply(
        member,
        to_status=to_status,
        by=by,
        effective_on=effective_on,
        reason=reason,
        request=request,
        with_p9=True,
    )


def mark_unpaid(member, *, by, effective_on, reason, request=None) -> Member:
    """Actiu → impagat, a mà i amb motiu (RN-M01-09, P9). No revoca el carnet."""
    return _unpaid(
        member, S.UNPAID, by=by, effective_on=effective_on, reason=reason, request=request
    )


def unmark_unpaid(member, *, by, effective_on, reason, request=None) -> Member:
    """Impagat → actiu, a mà i amb motiu (RN-M01-09, P9)."""
    return _unpaid(
        member, S.ACTIVE, by=by, effective_on=effective_on, reason=reason, request=request
    )


# --- Primitives internes del M01 (sense comprovació de rol) ---------------------------------


def _change_status(member, to_status, *, by, effective_on, reason="", request=None) -> Member:
    """Pendent → actiu i pendent, actiu o impagat → baixa (RN-M01-07)."""
    ensure_not_own_member(member, by, request=request)
    return _apply(
        member,
        to_status=to_status,
        by=by,
        effective_on=effective_on,
        reason=reason,
        request=request,
    )


def _change_type(member, new_type, *, by, effective_on, reason="", request=None) -> Member:
    """Canvi de tipus amb historial (RN-M01-08). Les regles del canvi són de la T-M01-17."""
    ensure_not_own_member(member, by, request=request)
    return _apply(
        member,
        to_type=new_type,
        by=by,
        effective_on=effective_on,
        reason=reason,
        request=request,
    )


def _readmit(member, join_request, *, by, effective_on, reason="", request=None) -> Member:
    """Baixa → pendent amb el mateix registre i número (067). No aprova la sol·licitud ni crea
    quotes: ho fa la T-M01-14 dins la mateixa transacció (P-54)."""
    ensure_not_own_member(member, by, request=request)
    return _apply(
        member,
        to_status=S.PENDING,
        by=by,
        effective_on=effective_on,
        reason=reason,
        request=request,
        join_request=join_request,
    )
