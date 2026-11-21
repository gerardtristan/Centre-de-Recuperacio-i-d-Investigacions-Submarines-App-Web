"""Tipus de llicència (P-M06-A, pas 1; RN-M06-01; LC8). Una llista que és una dada: el tresorer, el
President i l'administrador la mantenen des de l'app (VC-38). Cada canvi, al registre."""

from django.db import transaction
from django.http import Http404

from apps.core import audit
from apps.core.permissions import has_perm

from .models import LicenceType

PERMISSION = "licences.prices"  # LC8 («Cons.» només la veu)
ACTION_CREATED = "licences.type_created"
ACTION_ACTIVE = "licences.type_active_changed"


def _require(actor):
    if not has_perm(actor, PERMISSION, write=True):
        raise Http404


@transaction.atomic
def create_type(*, name, category, validity_rule, description="", actor) -> LicenceType:
    """Valida el model (nom únic, categoria, regla i, sense l'opció, cap d'un dia actiu)."""
    _require(actor)
    licence_type = LicenceType(
        name=(name or "").strip(), category=category, validity_rule=validity_rule,
        description=description.strip(),
    )  # fmt: skip
    licence_type.full_clean()
    licence_type.save()
    audit.record(
        ACTION_CREATED, actor=actor, target=licence_type,
        new={"name": licence_type.name, "category": category, "validity_rule": validity_rule},
    )  # fmt: skip
    return licence_type


@transaction.atomic
def set_active(licence_type: LicenceType, active: bool, *, actor) -> LicenceType:
    """Desactivar un tipus el treu de les sol·licituds noves; les ja demanades no canvien."""
    _require(actor)
    licence_type = LicenceType.objects.select_for_update().get(pk=licence_type.pk)
    previous = licence_type.active
    licence_type.active = active
    licence_type.full_clean()
    licence_type.save(update_fields=["active"])
    audit.record(ACTION_ACTIVE, actor=actor, target=licence_type, field="active",
                 old=previous, new=active)  # fmt: skip
    return licence_type
