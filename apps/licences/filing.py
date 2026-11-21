"""Tramitació a la federació (T-M06-10; P-M06-E; RN-M06-02, 09 i 11; LC5). Només serveis: la vista
arriba amb la PR del nucli del 06.

- `mark_filed(licence, actor)`: pagada → tramitada. Una anual comença el dia que es tramita
  (RN-M06-02), tret de la de l'any vinent (comença l'1/1) i la d'un dia (el dia triat).
- `mark_active(licence, federation_number, actor)`: pagada o tramitada → vigent, amb el número
  federatiu (obligatori a les del club, el supòsit prudent de l'[A validar: secretaria]).
- `export(actor, licences)`: el fitxer per enviar a la federació, en un format provisional
  ([P-444](../../docs/decisions/pendents.md)). Es genera a demanda, no es desa i el registre
  n'apunta l'empremta (RN-M06-11, CA-M06-10).
"""

import datetime
import hashlib

from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.core import audit
from apps.core.permissions import effective_permissions, has_perm
from apps.members.roster import to_csv

from .dates import expires_on
from .models import Licence, ValidityRule
from .services import LicenceRequestError

FILE_PERMISSION = "licences.file"  # LC5
BIRTH_DATE_FIELD = "members.field.birth_date"  # C1 (058)
ACTION_FILED = "licences.filed"
ACTION_ACTIVATED = "licences.activated"
ACTION_EXPORTED = "licences.exported"


class WrongStatus(LicenceRequestError):
    message = gettext_lazy("La llicència no és en l'estat que demana aquest pas.")


class FederationNumberRequired(LicenceRequestError):
    message = gettext_lazy("Escriu el número federatiu (30 caràcters com a màxim).")


def _require(actor):
    if not has_perm(actor, FILE_PERMISSION, write=True):
        raise Http404


def _start_on_filing(licence: Licence, today: datetime.date) -> None:
    """RN-M06-02: una anual que començava abans comença avui; la de l'any vinent i la d'un dia
    no canvien. El preu ja és copiat i no es toca (RN-M06-08)."""
    if licence.validity_rule == ValidityRule.SINGLE_DAY or licence.starts_on >= today:
        return
    licence.starts_on = today
    licence.expires_on = expires_on(today, licence.validity_rule)


def _transition(licence, allowed, target, *, actor, action, today, number=None) -> Licence:
    _require(actor)
    today = today or timezone.localdate()
    with transaction.atomic():
        licence = Licence.objects.select_for_update().get(pk=licence.pk)
        if licence.status not in allowed:
            raise WrongStatus
        previous = licence.status
        if previous == Licence.Status.PAID:
            _start_on_filing(licence, today)
        licence.status = target
        now = timezone.now()
        if target == Licence.Status.FILED:
            licence.filed_by, licence.filed_at = actor, now
        else:
            licence.activated_by, licence.activated_at = actor, now
            licence.federation_number = number
        licence.save()
        audit.record(
            action, actor=actor, target=licence, field="status", old=previous, new=target,
            details={"starts_on": licence.starts_on.isoformat(),
                     "expires_on": licence.expires_on.isoformat()},
        )  # fmt: skip
    return licence


def mark_filed(licence: Licence, *, actor, today=None) -> Licence:
    return _transition(
        licence, (Licence.Status.PAID,), Licence.Status.FILED,
        actor=actor, action=ACTION_FILED, today=today,
    )  # fmt: skip


def mark_active(licence: Licence, federation_number: str, *, actor, today=None) -> Licence:
    number = (federation_number or "").strip()
    if len(number) > 30 or (not number and licence.origin == Licence.Origin.CLUB):
        raise FederationNumberRequired
    return _transition(
        licence, (Licence.Status.PAID, Licence.Status.FILED), Licence.Status.ACTIVE,
        actor=actor, action=ACTION_ACTIVATED, today=today, number=number,
    )  # fmt: skip


def export(actor, licences=None) -> tuple[str, bytes]:
    """CSV (UTF-8 amb BOM i «;», com l'exportació de socis) de les llicències pagades per
    tramitar, o de les que es donin. Format provisional (P-444): cognoms, nom, data de naixement
    (només amb C1), tipus, categoria i inici. Cap document ni dada de contacte."""
    perms = effective_permissions(actor)
    if not has_perm(actor, FILE_PERMISSION, write=True, permissions=perms):
        raise Http404
    birth_date = has_perm(actor, BIRTH_DATE_FIELD, permissions=perms)
    if licences is None:
        licences = Licence.objects.filter(status=Licence.Status.PAID)
    licences = list(
        licences.select_related("person", "licence_type").order_by(
            "person__last_name", "person__first_name", "pk"
        )
    )
    headers = [_("Cognoms"), _("Nom")]
    headers += [_("Data de naixement")] if birth_date else []
    headers += [_("Tipus de llicència"), _("Categoria"), _("Inici")]
    rows = []
    for licence in licences:
        person = licence.person
        row = [person.last_name, person.first_name]
        if birth_date:
            row.append(person.birth_date.strftime("%d/%m/%Y") if person.birth_date else "")
        row += [
            licence.licence_type.name,
            licence.licence_type.get_category_display(),
            licence.starts_on.strftime("%d/%m/%Y"),
        ]
        rows.append(row)
    content = to_csv(headers, rows)
    audit.record(
        ACTION_EXPORTED, actor=actor,
        details={"count": len(rows), "sha256": hashlib.sha256(content).hexdigest(),
                 "birth_date": birth_date, "licences": [lic.pk for lic in licences]},
    )  # fmt: skip
    return f"llicencies-federacio-{timezone.localdate():%Y-%m-%d}.csv", content
