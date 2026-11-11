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
from dataclasses import dataclass

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Case, DateField, F, Prefetch, When
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import Account
from apps.core import audit
from apps.core.models import AuditEntry, Charge, Person
from apps.core.permissions import has_perm

from . import cards, roster
from .fee_rules import local_today
from .models import (
    AnnualFee,
    LicenceRecord,
    Member,
    MemberRequest,
    MembershipType,
    MemberStatusChange,
)

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


def ensure_not_own_member(member, by, *, request=None, message=None) -> None:
    """Rebutja i registra l'intent si el compte és de la persona del soci. Cal cridar-lo
    abans d'obrir la transacció de l'operació (vegeu el docstring del mòdul). Un compte no
    actiu es rebutja abans (`InactiveAccount`), sense intent registrat, llevat que es desactivi
    just entre aquesta comprovació i la de dins la transacció, que en tot cas impedeix el canvi."""
    _check_account_active(by)
    if _is_own(member, by):
        audit.record(OWN_MEMBER_REJECTED, actor=by, target=member, request=request)
        raise OwnMemberChange(
            message or _("No pots canviar l'estat ni el tipus del teu propi soci.")
        )


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
                if locked.joined_on and effective_on < locked.joined_on:
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


# --- Lectura de la llicència (T-M01-30; decisió 049, M01-8) ---------------------------------
#
# Només lectura: cap escriptura, cap registre d'activitat i cap comprovació de permís (és un
# servei entre mòduls; el permís el comprova la vista de qui el crida). Torna dades immutables,
# mai el model, perquè cap altra app no pugui desar-lo. La marca de caducitat desconeguda és
# `expiry_unknown` (RN-M01-50, T-M01-34). Fora d'aquí: `cancelled_on` (RN-M01-38, T-M01-31).
# Formen part de `__all__` des de la integració amb la T-M01-26 (contracte de M01-8).


@dataclass(frozen=True)
class LicenceInfo:
    """Registre mínim de llicència (RN-M01-29). `expires_on` és None si no se sap (Cluber) o si
    només la sap el soci: una caducitat declarada i no confirmada no és vigent (RN-M01-77) i va a
    `declared_expires_on`, només per mostrar-la com a «declarada pel soci»."""

    record_id: int
    person_id: int
    licence_type: str
    issued_on: datetime.date
    expires_on: datetime.date | None
    declared_expires_on: datetime.date | None = None

    @property
    def expiry_unknown(self) -> bool:
        """Caducitat desconeguda (RN-M01-50). Marca neutra: què vol dir per al 02 («pendent de
        confirmar», no vigent) ho decideix el 02 [A validar: secretaria]."""
        return self.expires_on is None


# Una caducitat declarada pel soci compta com a desconeguda fins que la secretaria la confirma.
_KNOWN = {
    "known_expires_on": Case(
        When(expiry_declared=True, then=None), default=F("expires_on"), output_field=DateField()
    ),
    "declared_on": Case(When(expiry_declared=True, then=F("expires_on")), output_field=DateField()),
}
_LICENCE_FIELDS = (
    "pk",
    "member__person_id",
    "licence_type",
    "issued_on",
    "known_expires_on",
    "declared_on",
)
# Caducitat coneguda més tardana primer; les buides, només si no n'hi ha cap amb data (RN-M01-50).
_LICENCE_ORDER = (F("known_expires_on").desc(nulls_last=True), "-issued_on", "-pk")


def licence_record(person) -> LicenceInfo | None:
    """El registre mínim de la persona, o None si no és sòcia o no en té cap (049)."""
    row = (
        LicenceRecord.objects.filter(member__person=person)
        .annotate(**_KNOWN)
        .order_by(*_LICENCE_ORDER)
        .values_list(*_LICENCE_FIELDS)
        .first()
    )
    return LicenceInfo(*row) if row else None


def licence_records() -> list[LicenceInfo]:
    """Tots els registres mínims de tots els socis, un per registre, per al pas únic al 06
    (P-M06-H: cada llicència recorda de quin registre surt). Ordenats per persona i amb el mateix
    ordre que `licence_record`: el primer de cada persona és el que torna `licence_record`."""
    rows = (
        LicenceRecord.objects.annotate(**_KNOWN)
        .order_by("member__person_id", *_LICENCE_ORDER)
        .values_list(*_LICENCE_FIELDS)
    )
    return [LicenceInfo(*row) for row in rows]


# --- Serveis oferts a altres mòduls (M01-8; T-M01-26) ---------------------------------------
#
# Cap altra app escriu als models del M01: ho fa amb aquests serveis. Els de lectura no escriuen
# res i no comproven cap permís: el comprova la vista del mòdul que els crida. No tornen
# objectes del model (que es podrien desar), sinó dades. Fora d'aquesta tasca:
# `licence_record` i `licence_records` (T-M01-30), i `export_personal_data` i `anonymise`
# (T-M01-22, RGPD del M01, a `privacy.py`).

__all__ += [
    "MemberStats",
    "MemberSummary",
    "LicenceInfo",
    "NotAMember",
    "active_members_for_mandates",
    "get_member_summary",
    "is_member",
    "licence_record",
    "licence_records",
    "on_fee_paid",
    "on_fee_returned",
    "stats",
    "verify_card",
]

FEE_PAID_ORIGIN = "members.on_fee_paid"
FEE_RETURNED_ORIGIN = "members.on_fee_returned"
FEE_PAID_WHILE_UNPAID = "members.fee_paid_while_unpaid"
FEE_PAID_AFTER_LEAVING = "members.fee_paid_after_leaving"  # 079 (A-17): llista de revisió
SUPPLEMENT_PAID_NOT_ACTIVE = "members.supplement_paid_not_active"
FEE_RETURNED = "members.fee_returned"
MEMBER_STATUSES = (S.ACTIVE, S.UNPAID)  # «és soci» a M01-8: actiu o impagat


class NotAMember(LookupError):
    """La persona no té cap registre de soci."""


@dataclass(frozen=True)
class MemberSummary:
    person_id: int
    number: int | None
    type: str  # codi del tipus
    type_name: str
    status: str
    valid_until: datetime.date | None  # «vàlid fins al» del carnet (070, 072); no és l'estat


@dataclass(frozen=True)
class MemberStats:
    by_type_and_status: dict  # {(codi del tipus, estat): recompte}, a la data
    joined: int  # altes del mes fins a la data (`joined_on`)
    left: int  # baixes del mes fins a la data (historial)


def _summary(member) -> MemberSummary:
    # `member` ve de `roster.with_fee_data` (quotes i pagaments precarregats).
    return MemberSummary(
        person_id=member.person_id,
        number=member.member_number,
        type=member.type.code,
        type_name=member.type.name,
        status=member.status,
        valid_until=cards.valid_until(member),
    )


def _ordered_changes():
    return MemberStatusChange.objects.order_by("created_at", "id")


def _state_on(member, on, changes):
    """(estat, id del tipus) del soci a la data `on`, o `None` si encara no ho era. Avui o
    després, l'estat actual. Abans, l'historial: l'últim canvi desat amb data efectiva fins a
    `on` (ordre de desar: un canvi amb data passada no reordena els anteriors); si no n'hi ha
    cap, l'estat d'abans del primer canvi. `changes` ve per ordre de desar."""
    if on >= local_today():
        return member.status, member.type_id
    before = [c for c in changes if c.effective_on <= on]
    if before:
        return before[-1].to_status, before[-1].to_type_id
    if member.joined_on and member.joined_on > on:
        return None
    if not changes:
        return member.status, member.type_id
    first = changes[0]
    return (first.from_status, first.from_type_id) if first.from_status else None


def is_member(person, on=None) -> bool:
    """Cert si la persona és sòcia activa o impagada a la data `on` (per defecte, avui)."""
    member = Member.objects.filter(person=person).first()
    if member is None:
        return False
    state = _state_on(member, on or local_today(), list(_ordered_changes().filter(member=member)))
    return state is not None and state[0] in MEMBER_STATUSES


def get_member_summary(person) -> MemberSummary:
    """Número, tipus, estat i «vàlid fins al» del soci de la persona, sigui quin sigui l'estat
    (també pendent o de baixa). `NotAMember` si la persona no té soci."""
    member = (
        roster.with_fee_data(Member.objects.select_related("type")).filter(person=person).first()
    )
    if member is None:
        raise NotAMember(_("Aquesta persona no és sòcia."))
    return _summary(member)


def active_members_for_mandates() -> list[MemberSummary]:
    """Socis actius per a la campanya de mandats (P-M05a-E), per número. Ni pendents, ni
    impagats, ni de baixa, ni persones anonimitzades."""
    members = roster.with_fee_data(
        Member.objects.select_related("type")
        .filter(status=S.ACTIVE, person__status=Person.Status.ACTIVE)
        .order_by("member_number", "pk")
    )
    return [_summary(m) for m in members]


INVALID_CARD = {"valid": False, "member_number": "", "first_name": ""}


def verify_card(token) -> dict:
    """Verificació pública (RN-M01-26, RN-M01-27; 072, Q-063 i Q-064, confirmades per la junta):
    sempre `{"valid", "member_number", "first_name"}`. Si és vàlid, el número de soci sencer i el
    nom de pila; res més. Un testimoni desconegut, revocat, d'un impagat o caducat dona
    `INVALID_CARD`, igual. Igualar el temps i limitar les peticions és de la vista (T-M01-20)."""
    card = cards.valid_card_for_token(token)
    if card is None or card.member.member_number is None:
        return dict(INVALID_CARD)
    member = card.member
    return {
        "valid": True,
        "member_number": str(member.member_number),
        "first_name": member.person.first_name,
    }


def stats(on=None) -> MemberStats:
    """Recomptes per al dashboard (08), sense cap dada personal."""
    on = on or local_today()
    month_start = on.replace(day=1)
    codes = dict(MembershipType.objects.values_list("pk", "code"))
    counts = {}
    members = Member.objects.prefetch_related(Prefetch("status_changes", _ordered_changes()))
    for member in members:
        state = _state_on(member, on, list(member.status_changes.all()))
        if state is not None:
            key = (codes[state[1]], state[0])
            counts[key] = counts.get(key, 0) + 1
    joined = Member.objects.filter(joined_on__range=(month_start, on)).count()
    left = (
        MemberStatusChange.objects.filter(to_status=S.LEFT, effective_on__range=(month_start, on))
        .exclude(from_status=S.LEFT)
        .values("member")
        .distinct()
        .count()
    )
    return MemberStats(by_type_and_status=counts, joined=joined, left=left)


def on_fee_paid(annual_fee_id) -> Member:
    """La 05b o la 04 (en conciliar) l'avisen quan el càrrec d'una quota passa a «pagat», dins
    la mateixa transacció. Comprova a la base de dades que el càrrec està pagat: mai no dona un
    pagament per fet per la crida. Idempotent.

    Segons l'estat del soci (079, RN-M01-89; substitueix la fila del contracte de M01-8):
    - Pendent, quota anual pagada → actiu (actor: el sistema; data efectiva: avui) i carnet nou
      (P-M01-A, pas 7; CA-M01-06), tot o res. `replace_card` revoca abans un carnet que hagi
      quedat d'abans.
    - Actiu → «vàlid fins al» es recalcula amb el pagament nou (070) i, si no té cap carnet no
      revocat, se n'emet un (A-06, CA-M01-96).
    - Impagat → continua impagat (040, RN-M01-09); queda al registre i s'avisa per correu qui pot
      editar les quotes (A-07, CA-M01-97).
    - Baixa → **cap error**: no canvia res, queda al registre i el pagament surt a la llista
      «Pagaments per revisar» del tresorer (A-17, CA-M01-98; `fees.payments_to_review`).
    - Suplement de canvi de tipus → el canvi de tipus, si escau (T-M01-17).
    - Pagaments parcials (terminis, P-61; T-M01-49) → `InvalidTransition`: no hi ha cap regla
      aprovada. És l'únic `InvalidTransition`, a part del càrrec que no consta com a pagat: mai
      per l'estat del soci.
    """
    from . import fees

    by = audit.system(FEE_PAID_ORIGIN)
    with transaction.atomic():
        fee = AnnualFee.objects.select_related("charge").get(pk=annual_fee_id)
        member = Member.objects.select_for_update(of=("self",)).get(pk=fee.member_id)
        if fee.charge.status != Charge.Status.PAID or fee.charge.person_id != member.person_id:
            raise InvalidTransition(_("El càrrec d'aquesta quota no consta com a pagat."))
        if fee.kind == AnnualFee.Kind.TYPE_CHANGE_SUPPLEMENT:
            return _apply_paid_supplement(fee, member, by=by)
        if fee.kind != AnnualFee.Kind.ANNUAL:
            return member
        if member.status == S.ACTIVE:
            # A-06: un actiu sense carnet que paga la renovació en rep un.
            loaded = cards.load_member(member.pk)
            if cards.active_card(loaded) is None and cards.valid_until(loaded) is not None:
                cards.issue_card(member, by=by)
            return member
        if member.status in (S.UNPAID, S.LEFT):
            # Idempotent: una segona crida per la mateixa quota no torna a avisar ni a anotar.
            action = FEE_PAID_WHILE_UNPAID if member.status == S.UNPAID else FEE_PAID_AFTER_LEAVING
            if _already_recorded(action, fee):
                return member
            audit.record(action, actor=by, target=fee)
            if member.status == S.UNPAID:
                fees.notify_fee_editors(fee, fees.NOTICE_PAID_WHILE_UNPAID)
            return member
        if cards._paid_until(cards.load_member(member.pk)) is None:
            raise InvalidTransition(
                _("La quota té pagaments parcials: falta la regla del pagament en tres quotes.")
            )
        _change_status(member, S.ACTIVE, by=by, effective_on=local_today())
        cards.replace_card(
            member, by=by, reason=_("Carnet nou en confirmar-se el pagament de la quota.")
        )
    member.refresh_from_db()
    return member


def _already_recorded(action, fee) -> bool:
    return AuditEntry.objects.filter(
        action=action, target_type=fee._meta.label_lower, target_id=str(fee.pk)
    ).exists()


def _apply_paid_supplement(fee, member, *, by) -> Member:
    """Q-050 (072): el canvi a ple dret és efectiu quan es paga el suplement. Només una vegada i
    només si el soci continua actiu; si no, queda al registre perquè ho revisi la secretaria."""
    change = (
        MemberRequest.objects.select_for_update(of=("self",))
        .select_related("requested_type")
        .filter(supplement_fee=fee, status=MemberRequest.Status.APPROVED, effective_on=None)
        .first()
    )
    if change is None:
        return member
    if member.status != S.ACTIVE:
        audit.record(SUPPLEMENT_PAID_NOT_ACTIVE, actor=by, target=fee)
        return member
    today = local_today()
    _change_type(
        member,
        change.requested_type,
        by=by,
        effective_on=today,
        reason=_("Suplement del canvi de tipus pagat."),
    )
    change.effective_on = today
    change.save(update_fields=["effective_on"])
    # RN-M01-25: amb el canvi de tipus, carnet nou si en tenia un (si escau).
    if cards.active_card(member) is not None:
        cards.replace_card(member, by=by, reason=_("Carnet nou pel canvi de tipus."))
    member.refresh_from_db()
    return member


def on_fee_returned(annual_fee_id) -> None:
    """La 05b l'avisa quan una quota es retorna. El M01 no canvia l'estat del soci: l'impagat
    continua sent manual (040). Queda al registre i s'avisa per correu qui pot editar les quotes
    (079, A-07; RN-M01-89), només amb el número de soci i la quota."""
    from . import fees

    with transaction.atomic():
        fee = AnnualFee.objects.select_related("member").get(pk=annual_fee_id)
        audit.record(FEE_RETURNED, actor=audit.system(FEE_RETURNED_ORIGIN), target=fee)
        fees.notify_fee_editors(fee, fees.NOTICE_RETURNED)
