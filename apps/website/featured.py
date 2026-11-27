"""Activitats destacades de la web (T-M07-29; RN-M07-21 i CA-M07-30 de l'addenda de la 106).

- Qui: WP1 (`website.pages`) amb «Sí», al servidor. Quan la T-M07-26 parteixi el WP1, passarà a
  WP1a («triar les activitats destacades»).
- Què es desa: només la referència a l'activitat del 02, l'ordre i les dates de visibilitat
  (`FeaturedActivity`). Cap còpia de les dades del 02.
- `items(today)`: les destacades visibles avui, en ordre, resoltes amb el servei públic del 02
  (`activities.public.get_activity`) a cada petició. Una activitat que el 02 retira (o que ja no
  és pública) no surt, sense esperar res (CA-M07-30).
- Treure-la de les destacades esborra la referència (no és cap dada del club) i queda al
  registre, com afegir-la i canviar-ne l'ordre.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.activities import public as activities
from apps.core import audit
from apps.core.permissions import has_perm

from .models import FeaturedActivity
from .pages import PERMISSION  # WP1; WP1a amb la T-M07-26

ADDED = "website.featured_added"
REMOVED = "website.featured_removed"
MOVED = "website.featured_moved"


def require(actor):
    if not has_perm(actor, PERMISSION, write=True):
        raise Http404


@transaction.atomic
def add(activity_pk, *, actor, visible_from=None, visible_until=None) -> FeaturedActivity:
    require(actor)
    try:
        activities.get_activity(activity_pk)
    except activities.NotFound:
        raise ValidationError(_("Només es pot destacar una activitat publicada.")) from None
    if visible_from and visible_until and visible_until < visible_from:
        raise ValidationError(_("La data final no pot ser anterior a la inicial."))
    if FeaturedActivity.objects.filter(activity_ref=activity_pk).exists():
        raise ValidationError(_("Aquesta activitat ja és destacada."))
    last = FeaturedActivity.objects.select_for_update().aggregate(m=Max("order"))["m"]
    row = FeaturedActivity.objects.create(
        activity_ref=activity_pk, order=0 if last is None else last + 1,
        visible_from=visible_from, visible_until=visible_until,
    )  # fmt: skip
    audit.record(ADDED, actor=actor, target=row, details={"activity": activity_pk})
    return row


@transaction.atomic
def remove(row: FeaturedActivity, *, actor) -> None:
    require(actor)
    audit.record(REMOVED, actor=actor, target=row, details={"activity": row.activity_ref})
    row.delete()


@transaction.atomic
def move(row: FeaturedActivity, *, actor, up: bool) -> None:
    """Puja o baixa una posició; a la primera o a l'última, no fa res."""
    require(actor)
    rows = list(FeaturedActivity.objects.select_for_update())
    index = next(i for i, r in enumerate(rows) if r.pk == row.pk)
    other = index - 1 if up else index + 1
    if not 0 <= other < len(rows):
        return
    rows[index], rows[other] = rows[other], rows[index]
    for order, item in enumerate(rows):
        if item.order != order:
            item.order = order
            item.save(update_fields=["order"])
    audit.record(MOVED, actor=actor, target=row, details={"up": up})


def visible(today=None):
    today = today or timezone.localdate()
    return [
        row for row in FeaturedActivity.objects.all()
        if (row.visible_from is None or row.visible_from <= today)
        and (row.visible_until is None or today <= row.visible_until)
    ]  # fmt: skip


def items(today=None) -> list:
    """CA-M07-30: les dades públiques del 02 de cada destacada visible, a cada petició."""
    found = []
    for row in visible(today):
        try:
            found.append(activities.get_activity(row.activity_ref, today=today))
        except activities.NotFound:
            continue  # retirada o ja no pública al 02: no surt
    return found
