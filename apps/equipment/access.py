"""Permisos del 03 als serveis (T-M03-18, catàleg del nucli). Sense el permís per editar, «no
trobat»; un codi que no fos al catàleg tampoc no deixaria fer res a ningú."""

from django.http import Http404

from apps.core.permission_catalog import CATALOG
from apps.core.permissions import has_perm

INVENTORY = "equipment.inventory.manage"  # MT3
TYPICAL = "equipment.typical.manage"  # MT5
REVIEWS = "equipment.reviews.manage"  # MT11


def allowed(by, code, obj=None) -> bool:
    return code in CATALOG and has_perm(by, code, obj, write=True)


def require(by, code, obj=None) -> None:
    if not allowed(by, code, obj):
        raise Http404
