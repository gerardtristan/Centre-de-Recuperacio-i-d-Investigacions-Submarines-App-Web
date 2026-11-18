"""Tipus de soci com a dada (T-M01-52; 091, RN-M01-107): crear, editar i desactivar tipus des
dels ajustos del 01.

- Qui: «Sí» de l'apartat d'ajustos de socis, o `settings.edit.members.membership_types` amb
  l'apartat amb «Cons.» (RN-RP-22, com qualsevol valor dels ajustos) [A validar: P-376]. El
  permís es comprova aquí; sense permís, «no trobat» (i, amb «Cons.», queda al registre).
- Un tipus mai existeix sense preu editable: es crea amb el seu ajust de preu
  (`members.annual_fee_cents.<codi>`, VC-01), a la mateixa transacció. El preu es canvia
  després a l'ajust, amb data, nota i correu (RN-M01-45). El codi no canvia mai.
- Amb socis (pendents, actius o impagats), el tipus no es desactiva [A validar: P-374] i els
  atributs que decideixen regles (ple dret i edat mínima) no canvien [A validar: P-375]; el
  nom, sí. Cap tipus no s'esborra (RN-M01-107; `PROTECT`).
- Cada canvi va al registre d'activitat amb el valor anterior.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import audit, business_settings
from apps.core.models import Setting
from apps.core.permissions import has_perm

from . import settings as values
from .models import Member, MembershipType

SECTION = "members"
EDIT_PERMISSION = "settings.edit.members.membership_types"
CREATED = "members.type.created"
CHANGED = "members.type.changed"
DENIED = "members.type.change_denied"
RULE_FIELDS = ("full_rights", "min_age")


def can_view(user) -> bool:
    return business_settings.can_view(user, SECTION)


def can_edit(user) -> bool:
    """RN-RP-22: «Sí» de l'apartat, o el permís de tipus amb l'apartat amb «Cons.»."""
    return has_perm(user, business_settings.section_code(SECTION), write=True) or (
        can_view(user) and has_perm(user, EDIT_PERMISSION, write=True)
    )


def check_can_edit(user, request=None):
    """Sense permís, «no trobat»; qui veu l'apartat i ho intenta queda al registre."""
    if not can_edit(user):
        if can_view(user):
            audit.record(DENIED, actor=user, request=request)
        raise Http404


def has_members(membership_type) -> bool:
    return membership_type.members.exclude(status=Member.Status.LEFT).exists()


def create(*, code, name, annual_fee_cents, full_rights, min_age, by, request=None):
    check_can_edit(by, request)
    with transaction.atomic():
        created = MembershipType(
            code=code,
            name=name,
            annual_fee_cents=annual_fee_cents,
            full_rights=full_rights,
            min_age=min_age,
        )
        created.full_clean()  # codi únic, preu positiu i 14 anys per al ple dret (RN-M01-64)
        created.save()
        Setting.objects.create(
            key=values.price_key(created),
            module=SECTION,
            value_type=Setting.ValueType.CENTS,
            initial_value=annual_fee_cents,
            min_value=1,
            affects_money=True,
            effective_dated=True,
        )
        audit.record(
            CREATED,
            actor=by,
            target=created,
            details={"code": code, "name": name, "annual_fee_cents": annual_fee_cents,
                     "full_rights": full_rights, "min_age": min_age},
            request=request,
        )  # fmt: skip
    return created


def update(membership_type, *, name, full_rights, min_age, active, by, request=None):
    check_can_edit(by, request)
    with transaction.atomic():
        locked = MembershipType.objects.select_for_update().get(pk=membership_type.pk)
        new = {"name": name, "full_rights": full_rights, "min_age": min_age, "active": active}
        changes = {f: (getattr(locked, f), v) for f, v in new.items() if getattr(locked, f) != v}
        if changes and has_members(locked):
            if changes.keys() & set(RULE_FIELDS):
                raise ValidationError(
                    _("Aquest tipus té socis: el ple dret i l'edat mínima no es poden canviar.")
                )
            if "active" in changes and not active:
                raise ValidationError(_("Aquest tipus té socis: no es pot desactivar."))
        for field, (_old, value) in changes.items():
            setattr(locked, field, value)
        locked.full_clean()
        locked.save()
        audit.record_changes(CHANGED, actor=by, target=locked, changes=changes, request=request)
    return locked
