"""Preus de les llicències (P-M06-A; RN-M06-05, 06, 08 i 18).

- `applicable(licence_type, starts_on)`: la versió que s'aplica a una llicència que comença
  aquell dia (RN-M06-18).
- `comparison(today)`: els preus de soci i de no soci de cada tipus que es pot demanar avui, per
  a la pàgina pública (RN-M06-07).
- `add_price(...)`: una versió nova, amb nota obligatòria, registre d'activitat i avís al
  tresorer, a la junta i a la secretaria (RN-M06-08, RN-AJ-04). Les llicències ja demanades
  porten la seva còpia del preu i no canvien.

`add_price` demana LC8 amb «Sí» (com `types`); sense, «no trobat» (T-M06-25). La vista també ho
comprova abans.
"""

import datetime
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils.translation import gettext as _

from apps.core import audit, business_settings, mail
from apps.core.charges import euros
from apps.core.models import Role

from . import types
from .models import LicencePrice, LicenceType, ValidityRule

ACTION_PRICE_ADDED = "licences.price_added"


def applicable(licence_type: LicenceType, starts_on: datetime.date) -> LicencePrice | None:
    """RN-M06-18: la versió creada més recentment amb `valid_from ≤ starts_on` i `valid_to`
    buit o `≥ starts_on`."""
    return (
        LicencePrice.objects.filter(licence_type=licence_type, valid_from__lte=starts_on)
        .filter(Q(valid_to__isnull=True) | Q(valid_to__gte=starts_on))
        .order_by("-pk")
        .first()
    )


@dataclass(frozen=True)
class PriceRow:
    name: str
    description: str
    validity: str
    member_cents: int
    non_member_cents: int
    saving_cents: int  # = el recàrrec (RN-M06-07)


def comparison(today: datetime.date) -> list[PriceRow]:
    """RN-M06-07 i P-M06-C, pas 2: els tipus actius amb un preu per a una llicència que comença
    avui. Els d'un dia, només amb `licences.day_enabled` (RN-M06-01)."""
    types = LicenceType.objects.filter(active=True).order_by("category", "name")
    if not business_settings.get("licences.day_enabled"):
        types = types.exclude(validity_rule=ValidityRule.SINGLE_DAY)
    rows = []
    for licence_type in types:
        price = applicable(licence_type, today)
        if price is not None:
            rows.append(PriceRow(
                licence_type.name, licence_type.description,
                licence_type.get_validity_rule_display(),
                price.amount_cents(LicencePrice.Kind.MEMBER),
                price.amount_cents(LicencePrice.Kind.NON_MEMBER),
                price.non_member_surcharge_cents,
            ))  # fmt: skip
    return rows


def _describe(price: LicencePrice | None) -> str:
    if price is None:
        return "—"
    return _("federació %(cost)s, no soci %(non_member)s") % {
        "cost": euros(price.amount_cents(LicencePrice.Kind.MEMBER)),
        "non_member": euros(price.amount_cents(LicencePrice.Kind.NON_MEMBER)),
    }


def _is_cents(value, *, positive: bool) -> bool:
    return (
        not isinstance(value, bool) and isinstance(value, int) and value >= (1 if positive else 0)
    )


def _secretaries():
    """Comptes d'administrador actius amb el rol Secretaria i correu de notificació."""
    from apps.accounts.models import Account

    return (
        Account.objects.filter(
            kind=Account.Kind.ADMIN,
            status=Account.Status.ACTIVE,
            role_assignments__role__code=Role.Code.SECRETARY,
            role_assignments__removed_at__isnull=True,
        )
        .exclude(notification_email="")
        .select_related("person")
        .distinct()
        .order_by("pk")
    )


def add_price(
    licence_type: LicenceType,
    *,
    federation_cost_cents: int,
    non_member_surcharge_cents: int,
    valid_from: datetime.date,
    valid_to: datetime.date | None = None,
    note: str,
    actor,
) -> LicencePrice:
    """Crea una versió de preu. No hi ha cap preu de soci a part: és el de la federació
    (RN-M06-05, CA-M06-04)."""
    types.require(actor)
    note = (note or "").strip()
    if not note:
        raise ValidationError(_("Cal una nota per canviar un preu."))
    if not _is_cents(federation_cost_cents, positive=True):
        raise ValidationError(_("El preu de la federació ha de ser un enter positiu de cèntims."))
    if not _is_cents(non_member_surcharge_cents, positive=False):
        raise ValidationError(_("El recàrrec no pot ser negatiu i va en cèntims."))
    if valid_to is not None and valid_to < valid_from:
        raise ValidationError(_("La data final del tram no pot ser anterior a la inicial."))

    with transaction.atomic():
        previous = applicable(licence_type, valid_from)
        price = LicencePrice.objects.create(
            licence_type=licence_type,
            federation_cost_cents=federation_cost_cents,
            non_member_surcharge_cents=non_member_surcharge_cents,
            valid_from=valid_from,
            valid_to=valid_to,
            note=note,
            created_by=actor,
        )
        audit.record(
            ACTION_PRICE_ADDED,
            actor=actor,
            target=price,
            old=None if previous is None else previous.pk,
            new={
                "licence_type": licence_type.pk,
                "federation_cost_cents": federation_cost_cents,
                "non_member_surcharge_cents": non_member_surcharge_cents,
                "valid_from": valid_from.isoformat(),
                "valid_to": valid_to.isoformat() if valid_to else None,
            },
            reason=note,
        )
        notice = {
            "what": _("Preu de la llicència «%(type)s»") % {"type": licence_type.name},
            "previous": _describe(previous),
            "new": _describe(price),
            "changed_by": actor,
            "note": note,
            "effective_from": valid_from,
        }
        emails = business_settings.notify_money_change(**notice)
        # RN-M06-08: també la secretaria; una adreça rep un sol correu.
        sent = {email.to_address for email in emails}
        context = {**notice, "changed_by": str(actor.person)}
        for account in _secretaries():
            if account.notification_email not in sent:
                sent.add(account.notification_email)
                mail.queue_email(
                    business_settings.EMAIL_TEMPLATE,
                    to=account.notification_email,
                    person=account.person,
                    context=context,
                )
    return price
