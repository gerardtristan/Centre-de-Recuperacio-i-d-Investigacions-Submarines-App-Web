"""Ordre i blocs amagats per compte (T-M08-12; P-M08-D; CA-M08-13; P-490).

- `save(account, order, hidden)` desa la preferència del compte que fa la petició: cap paràmetre
  permet tocar la d'un altre (RN-M08-06). Només codis del catàleg que el compte pot veure: amb
  DB1, tots (M08-4); sense DB1, cap. Un codi desconegut o que no pot veure, «no trobat».
- `arrange(account, blocks)` aplica la preferència als blocs d'un panell: primer els de l'ordre
  desat, després la resta en l'ordre del catàleg, i sense els amagats.
La vista i el gest d'arrossegar són de la T-M08-09 i el sistema de disseny."""

from django.http import Http404

from apps.core.permissions import has_perm

from .indicators import CATALOG
from .models import DashboardLayout

VIEW = "dashboard.view"  # DB1


def _clean(codes, visible) -> list:
    if not isinstance(codes, list) or not all(isinstance(code, str) for code in codes):
        raise Http404
    if not set(codes) <= visible:
        raise Http404
    return list(dict.fromkeys(codes))  # sense repetits, en el mateix ordre


def save(account, order, hidden) -> DashboardLayout:
    if not has_perm(account, VIEW, write=False):
        raise Http404  # sense DB1, ni tan sols una preferència buida
    visible = set(CATALOG)
    layout, _ = DashboardLayout.objects.update_or_create(
        account=account,
        defaults={"order": _clean(order, visible), "hidden": _clean(hidden, visible)},
    )
    return layout


def arrange(account, blocks: dict) -> dict:
    layout = DashboardLayout.objects.filter(account=account).first()
    if layout is None:
        return dict(blocks)
    first = [code for code in layout.order if code in blocks]
    codes = first + [code for code in blocks if code not in first]
    return {code: blocks[code] for code in codes if code not in layout.hidden}
