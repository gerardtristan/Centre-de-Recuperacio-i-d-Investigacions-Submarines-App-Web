"""Serveis del 06 per a altres mòduls (M06-8). Cap altra app llegeix ni escriu els models del 06:
ho fa amb aquests serveis.

- `current(person, on)`: la llicència que cobreix una data (RN-M06-13). Només lectura, una sola
  consulta.
- `request(person, licence_type, starts_on, actor)`: demanar una llicència i el seu càrrec
  (P-M06-B, RN-M06-04, 10 i 21). El pagament és el del 05b sobre el càrrec; el pas a «pagada»,
  la T-M06-05.
- `declare_existing(person, licence_type, ...)`: «Ja en tinc una» (RN-M06-14).
- `cancel(licence, reason, actor)` i `decide_refund(proposal, ...)`: cancel·lar i, si estava
  pagada, la proposta de devolució que fa el tresorer amb el 05b (P-M06-G, CA-M06-13).
- `participant_status(account, person, on, context)`: el que pot veure de la llicència d'un
  participant l'instructor («vigent sí o no») o el responsable de l'activitat («vigent», «en
  tràmit» o «no») per a la data de la sessió o de l'activitat (RN-M06-22, LC10). Mai la data de
  venciment, el número federatiu, la categoria ni el document.
"""

import datetime
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.db.models import F, Q, TextChoices
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.core import audit, business_settings, charges, events
from apps.core.models import Charge, Department
from apps.core.permission_catalog import SCOPE_ALL, SCOPE_OWN_SESSIONS
from apps.core.permissions import has_perm, scope_for
from apps.members.services import is_member
from apps.payments import refunds

from . import events as licence_events
from . import prices
from .dates import expires_on
from .models import (
    IN_PROGRESS,
    Licence,
    LicencePrice,
    LicenceRefundProposal,
    LicenceType,
    ValidityRule,
)

PARTICIPANT_PERMISSION = "licences.participant_status"  # LC10


class CurrentStatus(TextChoices):
    ACTIVE = "active", _("Vigent")
    IN_PROGRESS = "in_progress", _("En tràmit")
    UNCONFIRMED = "unconfirmed", _("Pendent de confirmar")  # RN-M06-24


@dataclass(frozen=True)
class CurrentLicence:
    """Resposta de `current` (M06-8). Mai el model ni el número federatiu. `expires_on` és
    buit si la caducitat no està confirmada (RN-M06-24)."""

    status: str
    licence_type: str
    category: str
    validity_rule: str
    expires_on: datetime.date | None
    origin: str


def current(person, on: datetime.date) -> CurrentLicence | None:
    """RN-M06-13: la llicència `active` que cobreix `on` (la que caduca més tard); si no n'hi ha
    cap, una «pendent de confirmar» que ha començat (RN-M06-24, `unconfirmed`); si tampoc, una
    `requested`, `paid` o `filed` que la cobriria, com a «en tràmit»; si no, `None`.
    Les cancel·lades i les no tramitades a temps no compten."""
    candidates = (
        Licence.objects.filter(
            Q(expiry_confirmed=False) | Q(expires_on__gte=on),
            person=person,
            starts_on__lte=on,
            status__in=[Licence.Status.ACTIVE, *IN_PROGRESS],
        )
        .select_related("licence_type")
        .order_by(F("expires_on").desc(nulls_last=True), "-pk")
    )
    rank = {CurrentStatus.ACTIVE: 0, CurrentStatus.UNCONFIRMED: 1, CurrentStatus.IN_PROGRESS: 2}
    chosen, chosen_status = None, None
    for licence in candidates:
        if licence.status != Licence.Status.ACTIVE:
            status = CurrentStatus.IN_PROGRESS
        elif licence.expiry_confirmed:
            status = CurrentStatus.ACTIVE
        else:
            status = CurrentStatus.UNCONFIRMED
        if chosen is None or rank[status] < rank[chosen_status]:
            chosen, chosen_status = licence, status
    if chosen is None:
        return None
    return CurrentLicence(
        status=chosen_status,
        licence_type=chosen.licence_type.name,
        category=chosen.licence_type.category,
        validity_rule=chosen.validity_rule,
        expires_on=chosen.expires_on if chosen.expiry_confirmed else None,
        origin=chosen.origin,
    )


class ParticipantStatus(TextChoices):
    VALID = "valid", _("Vigent")
    IN_PROGRESS = "in_progress", _("En tràmit")
    UNCONFIRMED = "unconfirmed", _("Pendent de confirmar")
    NO = "no", _("No")


def participant_status(account, person, on: datetime.date, context=None) -> str:
    """RN-M06-22 i LC10. `context` és la sessió o l'activitat del 02: amb l'abast «les seves
    sessions» o «les seves activitats», el permís només val si `context` cau dins l'abast (la
    comprovació la registra el 02 amb `register_scope_check`; si no n'hi ha, es nega). Sense
    permís, «no trobat». Que `person` sigui participant de `context` ho comprova el 02."""
    scope = scope_for(account, PARTICIPANT_PERMISSION)
    # Amb un abast per objecte, sense `context` no hi ha res a comprovar: es nega (`has_perm`
    # sense objecte diria que sí).
    if scope is None or (scope != SCOPE_ALL and context is None):
        raise Http404
    if not has_perm(account, PARTICIPANT_PERMISSION, obj=context):
        raise Http404
    info = current(person, on)
    if info is None:
        return ParticipantStatus.NO
    if info.status == CurrentStatus.ACTIVE:
        return ParticipantStatus.VALID
    # Per a l'instructor, una llicència en tràmit o pendent de confirmar és «no» (RN-M06-22,
    # CA-M06-27 i RN-M06-24).
    if scope == SCOPE_OWN_SESSIONS:
        return ParticipantStatus.NO
    if info.status == CurrentStatus.UNCONFIRMED:
        return ParticipantStatus.UNCONFIRMED
    return ParticipantStatus.IN_PROGRESS


# --- Demanar una llicència (T-M06-04) ----------------------------------------------------------

NON_MEMBERS_ENABLED = "licences.non_members_enabled"  # VC-39
DAY_ENABLED = "licences.day_enabled"  # VC-40
NEXT_YEAR_OPENS_ON = "licences.next_year_opens_on"  # VC-42, "MM-DD"
# RN-M06-10: «General / Llicències» (provisional, S-M04-07). Entrada del sistema com «Quotes de
# socis» (P-411): la troba pel nom, com `charges.FEES_COST_CENTRE`.
COST_CENTRE = "Llicències"
ACTION_REQUESTED = "licences.requested"


class LicenceRequestError(Exception):
    message = _("No es pot demanar aquesta llicència.")

    def __str__(self):
        return str(self.message)


class NonMembersDisabled(LicenceRequestError):
    message = _("Ara mateix només els socis poden demanar una llicència.")


class DayLicencesDisabled(LicenceRequestError):
    message = _("La llicència d'un dia no està disponible.")


class AlreadyInProgress(LicenceRequestError):
    message = _("Ja tens una llicència d'aquest tipus en curs.")


class NextYearNotOpen(LicenceRequestError):
    message = _("Encara no es pot demanar la llicència de l'any vinent.")


class DateInPast(LicenceRequestError):
    message = _("La data de la llicència no pot ser passada.")


class NotAvailable(LicenceRequestError):
    message = _("Aquest tipus de llicència no es pot demanar ara mateix.")


class InvalidFederationNumber(LicenceRequestError):
    message = _("Escriu el número de la llicència (30 caràcters com a màxim).")


def _start(licence_type: LicenceType, starts_on, today) -> datetime.date:
    """RN-M06-02 i RN-M06-21. Una anual comença avui (la data definitiva és la de la
    tramitació, T-M06-10) o, la d'any natural, l'1/1 de l'any vinent; la d'un dia, el dia triat."""
    rule = licence_type.validity_rule
    if rule == ValidityRule.SINGLE_DAY:
        if not business_settings.get(DAY_ENABLED):
            raise DayLicencesDisabled
        if starts_on is None or starts_on < today:
            raise DateInPast
        return starts_on
    if starts_on is None or starts_on == today:
        return today
    if rule == ValidityRule.CALENDAR_YEAR and starts_on == datetime.date(today.year + 1, 1, 1):
        month, day = (int(part) for part in business_settings.get(NEXT_YEAR_OPENS_ON).split("-"))
        if today < datetime.date(today.year, month, day):
            raise NextYearNotOpen
        return starts_on
    if starts_on < today:
        raise DateInPast
    raise NotAvailable


def _renewal_of(person, licence_type: LicenceType, today):
    """La llicència vigent que renova (CA-M06-25; P-442): la del mateix tipus que caduca més
    tard i encara no ha caducat."""
    return (
        Licence.objects.filter(
            person=person, licence_type=licence_type, status=Licence.Status.ACTIVE,
            expires_on__gte=today,
        )
        .order_by("-expires_on", "-pk")
        .first()
    )  # fmt: skip


def request(person, licence_type: LicenceType, starts_on=None, *, actor, today=None) -> Licence:
    """P-M06-B: crea la llicència `requested` i el seu càrrec pendent. Només la pot demanar la
    mateixa persona (LC1, «Propi»); un altre compte rep «no trobat»."""
    if actor is None or getattr(actor, "person_id", None) != person.pk:
        raise Http404
    today = today or timezone.localdate()
    if not licence_type.active:
        raise NotAvailable
    start = _start(licence_type, starts_on, today)
    # RN-M06-04: soci o no soci el dia que la demana, també per a l'any vinent.
    if is_member(person, on=today):
        kind = LicencePrice.Kind.MEMBER
    elif business_settings.get(NON_MEMBERS_ENABLED):
        kind = LicencePrice.Kind.NON_MEMBER
    else:
        raise NonMembersDisabled
    price = prices.applicable(licence_type, start)
    if price is None:
        raise NotAvailable
    amount = price.amount_cents(kind)
    general = Department.objects.get(name=Department.GENERAL)
    try:
        with transaction.atomic():
            charge = charges.create_charge(
                person,
                kind=Charge.Kind.LICENCE,
                amount_cents=amount,
                concept=gettext("Llicència %(type)s (%(year)s)")
                % {"type": licence_type.name, "year": start.year},
                origin="licences",
                by=actor,
                department=general,
                cost_centre=general.cost_centres.get(name=COST_CENTRE),
            )
            licence = Licence.objects.create(
                person=person,
                licence_type=licence_type,
                validity_rule=licence_type.validity_rule,
                status=Licence.Status.REQUESTED,
                origin=Licence.Origin.CLUB,
                starts_on=start,
                expires_on=expires_on(start, licence_type.validity_rule),
                price_kind=kind,
                price_cents=amount,
                charge=charge,
                renewal_of=_renewal_of(person, licence_type, today),
            )
            audit.record(
                ACTION_REQUESTED,
                actor=actor,
                target=licence,
                new={"licence_type": licence_type.pk, "starts_on": start.isoformat(),
                     "price_kind": kind, "price_cents": amount, "price_version": price.pk},
            )  # fmt: skip
    except IntegrityError as error:
        # RN-M06-19: la restricció única és la que mana, també amb dues peticions alhora.
        if "licences_licence_one" in str(error):
            raise AlreadyInProgress from error
        raise
    return licence


# --- Pagament (T-M06-05) -------------------------------------------------------------------------

ACTION_PAID = "licences.paid"
SYSTEM = audit.system("licences.on_charge_paid")


def on_charge_paid(event) -> None:
    """Subscriptor de `charge.paid` (049, RN-M06-09): una llicència `requested` del càrrec passa
    a `paid`. Si ja ho és (o ja no és sol·licitada), no fa res: la cua ja no repeteix un lliurament
    fet (`EventDelivery`), i aquesta comprovació ho cobreix també si l'esdeveniment es repeteix."""
    payload = event.payload
    if payload.get("origin") != "licences":
        return
    licence = Licence.objects.select_for_update().filter(charge_id=payload.get("charge")).first()
    if licence is None or licence.status != Licence.Status.REQUESTED:
        return
    licence.status = Licence.Status.PAID
    licence.save(update_fields=["status", "updated_at"])
    # CA-M06-07: a qui tramita (LC5), una sola vegada perquè el pas a pagada només passa una.
    licence_events.notify(
        "licences.file", "avis-llicencia-pagada",
        {"licence_id": licence.pk, "licence_type": licence.licence_type.name},
    )  # fmt: skip
    audit.record(
        ACTION_PAID,
        actor=SYSTEM,
        target=licence,
        field="status",
        old=Licence.Status.REQUESTED,
        new=Licence.Status.PAID,
        details={"event": event.pk},
    )


# --- «Ja en tinc una» (T-M06-08) -----------------------------------------------------------------

DECLARE_PERMISSION = "licences.declare_existing"  # LC3 (per a una altra persona)
ACTION_DECLARED = "licences.declared_existing"


def declare_existing(
    person, licence_type: LicenceType, *, federation_number: str, expires_on, actor,
    starts_on=None, today=None,
) -> Licence:  # fmt: skip
    """RN-M06-14 (CA-M06-12): desa una llicència que la persona ja té, `active` i d'origen
    `external`, sense càrrec ni tramitació. La pot declarar la mateixa persona (el «Propi» de
    LC3) o un compte amb LC3; si no, «no trobat». Sense data d'inici, avui (P-443)."""
    own = actor is not None and getattr(actor, "person_id", None) == person.pk
    if not own and not has_perm(actor, DECLARE_PERMISSION, write=True):
        raise Http404
    today = today or timezone.localdate()
    if not licence_type.active:
        raise NotAvailable
    if licence_type.validity_rule == ValidityRule.SINGLE_DAY and not business_settings.get(
        DAY_ENABLED
    ):
        raise DayLicencesDisabled
    number = (federation_number or "").strip()
    if not number or len(number) > 30:
        raise InvalidFederationNumber
    if expires_on < today:
        raise DateInPast
    start = min(starts_on or today, expires_on)
    with transaction.atomic():
        licence = Licence.objects.create(
            person=person,
            licence_type=licence_type,
            validity_rule=licence_type.validity_rule,
            status=Licence.Status.ACTIVE,
            origin=Licence.Origin.EXTERNAL,
            starts_on=start,
            expires_on=expires_on,
            federation_number=number,
        )
        licence_events.activated(licence)
        audit.record(
            ACTION_DECLARED,
            actor=actor,
            target=licence,
            new={"licence_type": licence_type.pk, "starts_on": start.isoformat(),
                 "expires_on": expires_on.isoformat()},
        )  # fmt: skip
    return licence


# --- Cancel·lar i proposta de devolució (T-M06-12) ----------------------------------------------

CANCEL_PERMISSION = "licences.cancel"  # LC6
REFUND_PERMISSION = "licences.refund"  # LC7
ACTION_CANCELLED = "licences.cancelled"
ACTION_REFUND_DECIDED = "licences.refund_decided"
CANCELLABLE = (Licence.Status.REQUESTED, Licence.Status.PAID, Licence.Status.FILED)


def notify_refund(licence: Licence, amount_cents: int) -> None:
    """CA-M06-13 i CA-M06-23: l'avís de la proposta de devolució a qui la fa (LC7)."""
    licence_events.notify(
        REFUND_PERMISSION, "avis-devolucio-llicencia",
        {"licence_id": licence.pk, "amount": charges.euros(amount_cents)},
    )  # fmt: skip


class CannotCancel(LicenceRequestError):
    message = _("Aquesta llicència no es pot cancel·lar: una de vigent es deixa caducar.")


class MissingReason(LicenceRequestError):
    message = _("Cal un motiu.")


class AlreadyDecided(LicenceRequestError):
    message = _("Aquesta proposta de devolució ja està decidida.")


@transaction.atomic
def cancel(licence: Licence, reason: str, *, actor) -> Licence:
    """RN-M06-09 (P-M06-G): sol·licitada, pagada o tramitada → cancel·lada amb motiu. Si el
    càrrec és pendent, s'anul·la; si ja s'havia pagat, es crea la proposta de devolució per al
    tresorer, sense cap devolució automàtica (CA-M06-13)."""
    if not has_perm(actor, CANCEL_PERMISSION, write=True):
        raise Http404
    reason = (reason or "").strip()
    if not reason:
        raise MissingReason
    licence = Licence.objects.select_for_update().get(pk=licence.pk)
    if licence.status not in CANCELLABLE:
        raise CannotCancel
    previous = licence.status
    licence.status = Licence.Status.CANCELLED
    licence.cancellation_reason, licence.cancelled_by = reason, actor
    licence.save(update_fields=["status", "cancellation_reason", "cancelled_by", "updated_at"])
    charge = licence.charge
    if charge is not None and charge.status == Charge.Status.PENDING:
        charges.cancel(charge, reason, by=actor)
    elif charge is not None and charge.status == Charge.Status.PAID:
        LicenceRefundProposal.objects.create(
            licence=licence, amount_cents=charge.amount_cents, reason=reason
        )
        notify_refund(licence, charge.amount_cents)
    licence_events.emit(licence, events.LICENCE_CANCELLED)
    audit.record(
        ACTION_CANCELLED, actor=actor, target=licence, field="status", old=previous,
        new=Licence.Status.CANCELLED, reason=reason,
    )  # fmt: skip
    return licence


def decide_refund(proposal: LicenceRefundProposal, *, approve: bool, note: str, actor):
    """LC7: el tresorer fa la devolució amb el 05b (`payments.refund`, que també demana B5 i
    és idempotent per `refund_key`) o la rebutja amb una nota. Si el 05b falla, la proposta
    continua «proposada» i es pot tornar a provar."""
    if not has_perm(actor, REFUND_PERMISSION, write=True):
        raise Http404
    note = (note or "").strip()
    if not note:
        raise MissingReason
    if proposal.status != LicenceRefundProposal.Status.PROPOSED:
        raise AlreadyDecided
    if approve:
        (payment,) = charges.active_payments(proposal.licence.charge)
        refunds.refund(
            payment, proposal.amount_cents, reason=note, key=proposal.refund_key, by=actor
        )
    with transaction.atomic():
        locked = LicenceRefundProposal.objects.select_for_update().get(pk=proposal.pk)
        if locked.status != LicenceRefundProposal.Status.PROPOSED:
            return locked
        locked.status = (
            LicenceRefundProposal.Status.DONE if approve else LicenceRefundProposal.Status.REJECTED
        )
        locked.decision_note, locked.decided_by = note, actor
        locked.decided_at = timezone.now()
        locked.save(update_fields=["status", "decision_note", "decided_by", "decided_at"])
        audit.record(
            ACTION_REFUND_DECIDED, actor=actor, target=locked.licence, field="refund",
            old=LicenceRefundProposal.Status.PROPOSED, new=locked.status, reason=note,
        )  # fmt: skip
    return locked
