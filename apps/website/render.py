"""Un sol renderitzador de blocs per a la web pública i la vista prèvia (T-M07-04, decisió 106).

`render_blocks(blocks, page)`: cada bloc es pinta amb `website/blocs/<kind>.html` (DISSENY,
T-M07-19) o, mentre no existeix, amb `website/blocs/_provisional/<kind>.html`, amb el context
`{block, page}`. Contracte amb DISSENY:
- Els blocs amb `hidden` no es passen mai a cap plantilla.
- Els camps «md» arriben com a HTML segur (`blocks.render_markdown`) amb el mateix nom.
- Les fotos (`media`, `thumbnail`) arriben com a `Image` (`url`, `alt_text`, `width`, `height`,
  `focal_x`, `focal_y`); una foto que ja no es pot publicar arriba com a `None`.
- Les columnes d'una secció arriben ja pintades (una cadena HTML per columna).
- Dades: `upcoming_activities` porta `activities` (del 02), `recent_news` porta `news` i
  `faq_topic` porta `entries`.

No es pinten encara: `featured_activities`, `past_activities` i `featured_trip` (necessiten
serveis del 02, T-M07-29), `video` (T-M07-23) i `file` (els PDF, T-M07-07). El butlletí i el
contacte, només amb el seu ajust encès.
"""

import uuid
from dataclasses import dataclass

from django.template.loader import select_template
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.activities import public as activities
from apps.core import business_settings

from . import blocks as catalog
from . import help as faq
from . import media, news
from .models import FaqTopic, MediaAsset

NOT_YET = {"featured_activities", "past_activities", "featured_trip", "video", "file"}
SWITCHES = {"newsletter": "website.newsletter_enabled", "contact_form": "website.contact_enabled"}


@dataclass(frozen=True)
class Image:
    url: str
    alt_text: str
    width: int | None = None  # shortcut: sense mides fins que les desi la T-M07-07
    height: int | None = None
    focal_x: float | None = None
    focal_y: float | None = None


def _images(blocks) -> dict:
    """Les fotos que es poden publicar (RN-M07-05), en una sola consulta."""
    keys = {uuid.UUID(k) for k in media.block_media_keys(blocks, public_only=True)}
    found = MediaAsset.objects.filter(key__in=keys)
    return {
        str(a.key): Image(reverse("website:media", args=[a.key]), a.alt_text)
        for a in found
        if a.publishable
    }


def _fields(schema: dict, data: dict, images: dict) -> dict:
    """Markdown convertit i fotos resoltes, amb el mateix nom de camp."""
    out = dict(data)
    for name, field in schema.items():
        value = data.get(name)
        if field.type == "md":
            out[name] = catalog.render_markdown(value)
        elif field.type == "media":
            out[name] = images.get(value)
        elif field.type == "items" and isinstance(field.item, dict):
            out[name] = [_fields(field.item, item, images) for item in value or []]
        elif field.type == "items" and field.item.type == "media":  # galeria
            out[name] = [images[k] for k in value or [] if k in images]
    return out


def _data(block: dict) -> dict:
    kind = block["kind"]
    if kind == "upcoming_activities":
        kind_filter = (block.get("filters") or {}).get("type", "")
        return {"activities": activities.public_list(kind=kind_filter)[: block.get("count") or 0]}
    if kind == "recent_news":
        return {"news": list(news.published()[: block.get("count") or 0])}
    if kind == "faq_topic":
        topic = FaqTopic.objects.filter(pk=block.get("topic")).first()
        return {"entries": list(faq.published_entries(topic)) if topic else []}
    return {}


def _render(blocks, page, images) -> str:
    parts = []
    for block in blocks:
        kind = block["kind"]
        if block.get("hidden") or kind in NOT_YET:
            continue
        if kind in SWITCHES and not business_settings.get(SWITCHES[kind]):
            continue
        context = _fields(catalog.CATALOG[kind], block, images) | _data(block)
        if kind == "section":
            context["columns"] = [_render(c, page, images) for c in block.get("columns") or []]
        template = select_template(
            [f"website/blocs/{kind}.html", f"website/blocs/_provisional/{kind}.html"]
        )
        parts.append(template.render({"block": context, "page": page}))
    return mark_safe("".join(parts))  # noqa: S308 (plantilles amb l'escapament automàtic)


def render_blocks(blocks, page) -> str:
    """`blocks`: els d'una versió o els de l'esborrany, tal com es van desar."""
    blocks = catalog.upgrade_all(blocks)
    return _render(blocks, page, _images(blocks))
