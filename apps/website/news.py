"""Notícies (T-M07-08; P-M07-B, RN-M07-02, 05 i 14; CA-M07-01 per a notícies).

- `save_news`, `publish` i `retire`: WP2 (`website.news`, «Sí») al servidor.
- `published()`, `home_news()` i `get_published(slug)`: el que pot veure el visitant. Un
  esborrany, una retirada o una que no existeix donen el mateix «no trobat» (RN-M07-02).
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import audit, business_settings
from apps.core.permissions import has_perm

from . import media
from .models import NewsItem

PERMISSION = "website.news"  # WP2
ACTION_PUBLISHED = "website.news_published"
ACTION_RETIRED = "website.news_retired"
NEWS_ON_HOME = "website.news_on_home"
EDITABLE_FIELDS = {"title", "slug", "date", "body", "image"}
S = NewsItem.Status


def require(actor):
    if not has_perm(actor, PERMISSION, write=True):
        raise Http404


def _check_image(item: NewsItem) -> None:
    """RN-M07-05: una notícia publicada no porta cap foto que no es pugui publicar."""
    if item.image_id is not None:
        media.check_publishable([str(item.image.key)])


def save_news(item: NewsItem | None, *, actor, **fields) -> NewsItem:
    """Crea (`item=None`, en esborrany) o canvia una notícia que no és retirada."""
    require(actor)
    if set(fields) - EDITABLE_FIELDS:
        raise ValueError(f"Camps no editables: {sorted(set(fields) - EDITABLE_FIELDS)}")
    # Des de la base de dades: un canvi rebutjat abans no s'arrossega.
    item = NewsItem.objects.get(pk=item.pk) if item else NewsItem()
    if item.status == S.RETIRED:
        raise ValidationError(_("Una notícia retirada no es pot canviar."))
    for name, value in fields.items():
        setattr(item, name, value)
    item.full_clean()
    if item.status == S.PUBLISHED:
        _check_image(item)
    item.save()
    return item


@transaction.atomic
def publish(item: NewsItem, *, actor) -> NewsItem:
    require(actor)
    item = NewsItem.objects.select_for_update().get(pk=item.pk)
    if item.status != S.DRAFT:
        raise ValidationError(_("Només es pot publicar un esborrany."))
    _check_image(item)
    item.status = S.PUBLISHED
    item.save(update_fields=["status"])
    audit.record(ACTION_PUBLISHED, actor=actor, target=item, field="status", old=S.DRAFT,
                 new=S.PUBLISHED)  # fmt: skip
    return item


@transaction.atomic
def retire(item: NewsItem, *, actor, reason: str) -> NewsItem:
    """P-M07-B: amb motiu i registre (RN-M07-14). Retirar-la dues vegades no canvia res."""
    require(actor)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal el motiu de la retirada."))
    item = NewsItem.objects.select_for_update().get(pk=item.pk)
    if item.status == S.RETIRED:
        return item
    previous = item.status
    item.status, item.retired_reason = S.RETIRED, reason
    item.save(update_fields=["status", "retired_reason"])
    audit.record(ACTION_RETIRED, actor=actor, target=item, field="status", old=previous,
                 new=S.RETIRED, reason=reason)  # fmt: skip
    return item


def published():
    """Les publicades, de la més recent a la més antiga."""
    return NewsItem.objects.filter(status=S.PUBLISHED).select_related("image")


def home_news() -> list[NewsItem]:
    """P-M07-B: les més recents per a la portada (`website.news_on_home`)."""
    return list(published()[: business_settings.get(NEWS_ON_HOME)])


def get_published(slug: str) -> NewsItem:
    item = published().filter(slug=slug).first()
    if item is None:
        raise Http404
    return item
