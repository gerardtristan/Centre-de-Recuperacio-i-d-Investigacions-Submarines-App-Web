"""Primera llicència d'un alumne nou (T-M06-26 i T-M06-27; RN-M06-28; CA-M06-34 i 35).

L'entrada és una fila de la llista «Titulacions i llicències per tramitar» del 02 (una
`CertificationFiling`). La llicència hi queda lligada (`Licence.list_entry`) i n'hi pot haver una
sola per entrada: ho garanteix la base de dades, també amb dues peticions alhora.

- `entry_status(entry, on)`: el que la llista del 02 mostra. «Cal llicència» mentre la persona no
  tingui cap llicència vigent; desapareix quan la lligada (o una altra) es marca vigent amb el
  número (T-M06-27). `can_request` diu si hi ha d'haver el botó «Demana la primera llicència».
- `request_first(entry, licence_type, actor)`: no inclosa al curs. La secretaria (LC5) la
  demana en nom de l'alumne amb el càrrec habitual (P-M06-B o C), sense `renewal_of`.
- `grant_included(entry, licence_type, actor)`: inclosa al curs. `paid` directament, preu 0,
  `price_kind = included` i sense càrrec. La crida el 02 quan l'alumne queda apte en un curs que
  la inclou (T-M02-45 i T-M02-50); tornar-la a cridar no en crea cap altra.
"""

from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit

from .dates import expires_on
from .filing import _require
from .models import Licence, LicencePrice
from .services import (
    AlreadyInProgress,
    CurrentStatus,
    LicenceRequestError,
    current,
    place_request,
)

ACTION_INCLUDED = "licences.first_included"
ACTION_REQUESTED_FIRST = "licences.first_requested"


class AlreadyLicensed(LicenceRequestError):
    message = _("Aquesta persona ja té una llicència vigent.")


class EntryHasLicence(LicenceRequestError):
    message = _("Aquesta entrada ja té la seva primera llicència.")


@dataclass(frozen=True)
class EntryStatus:
    needs_licence: bool  # «Cal llicència»
    licence: Licence | None  # la lligada a l'entrada, si n'hi ha
    can_request: bool  # el botó «Demana la primera llicència»


def _linked(entry) -> Licence | None:
    return Licence.objects.filter(list_entry=entry).first()


def _has_valid(person, on) -> bool:
    found = current(person, on)
    return found is not None and found.status in (CurrentStatus.ACTIVE, CurrentStatus.UNCONFIRMED)


def entry_status(entry, on=None) -> EntryStatus:
    on = on or timezone.localdate()
    needs = not _has_valid(entry.person, on)
    linked = _linked(entry)
    return EntryStatus(needs, linked, needs and linked is None)


def _check(entry, today) -> None:
    if _has_valid(entry.person, today):
        raise AlreadyLicensed
    if _linked(entry) is not None:
        raise EntryHasLicence


def _link(licence, entry) -> Licence:
    """Lliga la llicència a l'entrada; la restricció única decideix si ja n'hi havia una."""
    licence.list_entry = entry
    try:
        with transaction.atomic():
            licence.save(update_fields=["list_entry"])
    except IntegrityError as error:
        raise EntryHasLicence from error
    return licence


@transaction.atomic
def request_first(entry, licence_type, *, actor, today=None) -> Licence:
    """CA-M06-34 (primera part): `requested` amb el seu càrrec, lligada a l'entrada."""
    _require(actor)
    today = today or timezone.localdate()
    _check(entry, today)
    licence = place_request(entry.person, licence_type, actor=actor, today=today)
    _link(licence, entry)
    audit.record(
        ACTION_REQUESTED_FIRST, actor=actor, target=licence, new={"list_entry": entry.pk},
    )  # fmt: skip
    return licence


@transaction.atomic
def grant_included(entry, licence_type, *, actor, today=None) -> Licence:
    """CA-M06-35: `paid`, preu 0 i sense càrrec. Idempotent per entrada. No comprova cap permís:
    és el 02 qui la crida en registrar el resultat (amb AC12), no una pantalla."""
    today = today or timezone.localdate()
    linked = _linked(entry)
    if linked is not None:
        return linked
    if _has_valid(entry.person, today):
        raise AlreadyLicensed
    try:
        with transaction.atomic():
            licence = Licence.objects.create(
                person=entry.person,
                licence_type=licence_type,
                validity_rule=licence_type.validity_rule,
                status=Licence.Status.PAID,
                origin=Licence.Origin.CLUB,
                starts_on=today,
                expires_on=expires_on(today, licence_type.validity_rule),
                price_kind=LicencePrice.Kind.INCLUDED,
                price_cents=0,
                list_entry=entry,
            )
    except IntegrityError as error:
        if "list_entry" in str(error):  # una altra crida alhora ja l'ha creada
            return _linked(entry)
        raise AlreadyInProgress from error  # ja en té una en tràmit d'aquest tipus
    audit.record(
        ACTION_INCLUDED, actor=actor, target=licence,
        new={"licence_type": licence_type.pk, "list_entry": entry.pk, "price_cents": 0},
    )  # fmt: skip
    return licence
