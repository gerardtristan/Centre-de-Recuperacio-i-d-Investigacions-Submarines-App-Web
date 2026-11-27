"""Un sol renderitzador de blocs per a la web pública i la vista prèvia (T-M07-04, decisió 106).

`render_blocks(blocks, page)`: cada bloc es pinta amb `website/blocs/<kind>.html` (DISSENY,
T-M07-19) o, mentre no existeix, amb `website/blocs/_provisional/<kind>.html`, amb el context
`{block, page}`. Contracte amb DISSENY:
- Els blocs amb `hidden` no es passen mai a cap plantilla.
- Els camps «md» arriben com a HTML segur (`blocks.render_markdown`) amb el mateix nom.
- Les fotos (`media`, `thumbnail`) arriben com a `Image` (`url`, `alt_text`, `width`, `height`,
  `focal_x`, `focal_y`); una foto que ja no es pot publicar, o totes amb
  `website.public_images_enabled` apagat, arriben com a `None`.
- Les columnes d'una secció arriben ja pintades (una cadena HTML per columna).
- Dades del club, `block.items` ja resolt i sense noms de persones: les activitats (properes,
  destacades i fetes), `{title, url, start, kind_label, price, photo, places_left}`
  (`price`, text ja formatat com a la fitxa pública, «30,00 €», o `None`; `places_left` 0 vol
  dir «Places exhaurides»); les
  notícies, `{title, url, date, photo}`. `faq_topic` porta `topic_name` i `questions`
  (`{question, answer}`, la resposta com a Markdown segur) i `featured_trip`, `block.activity`
  (o `None`). Sense dades, `items` buit: la plantilla pinta l'estat buit. Les destacades surten
  de `featured.items` i les fetes de `activities.public_past_list` (T-M07-29, RN-M07-21).

No es pinten encara: `video` (T-M07-23) i `file` (els PDF, T-M07-07). El butlletí i el contacte,
només amb el seu ajust encès.
"""

import uuid
from dataclasses import dataclass

from django.template.loader import select_template
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.activities import public as activities
from apps.core import business_settings
from apps.core.charges import euros

from . import blocks as catalog
from . import featured, media, news
from . import help as faq
from .models import FaqTopic, MediaAsset

NOT_YET = {"video", "file"}
IMAGES = "website.public_images_enabled"
SWITCHES = {"newsletter": "website.newsletter_enabled", "contact_form": "website.contact_enabled"}


@dataclass(frozen=True)
class Image:
    url: str
    alt_text: str
    width: int | None = None  # shortcut: sense mides fins que les desi la T-M07-07
    height: int | None = None
    focal_x: float | None = None
    focal_y: float | None = None


def _key(value):
    try:
        return uuid.UUID(value)
    except (TypeError, ValueError, AttributeError):
        return None


def _images(blocks) -> dict:
    """Les fotos que es poden publicar (RN-M07-05), en una sola consulta; cap amb
    `website.public_images_enabled` apagat (com les notícies)."""
    if not business_settings.get(IMAGES):
        return {}
    keys = {_key(k) for k in media.block_media_keys(blocks, public_only=True)} - {None}
    found = MediaAsset.objects.filter(key__in=keys)
    return {str(a.key): _image(a) for a in found if a.publishable}


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


def _image(asset) -> Image:
    return Image(reverse("website:media", args=[asset.key]), asset.alt_text)


def _activity(a) -> dict:
    """Contracte amb DISSENY: només dades de l'activitat, cap nom de persona (RN-M07-21)."""
    return {"title": a.title, "url": reverse("activities:public_detail", args=[a.pk]),
            "start": a.starts_on, "kind_label": a.kind_label, "places_left": a.free_places,
            "price": euros(a.price_cents) if a.price_cents is not None else None,
            # shortcut: la foto d'activitat (`a.photo`) encara no té cap adreça pública que la
            # serveixi; fins llavors, `None` (servei de contingut de la T-M07-30).
            "photo": None}  # fmt: skip


def _data(block: dict) -> dict:
    kind, count = block["kind"], block.get("count") or 0
    filters = block.get("filters") or {}
    if kind == "upcoming_activities":
        found = activities.public_list(
            kind=filters.get("type", ""), department=filters.get("department")
        )
        return {"items": [_activity(a) for a in found[:count]]}
    if kind == "featured_activities":
        return {"items": [_activity(a) for a in featured.items()]}
    if kind == "past_activities":
        return {"items": [_activity(a) for a in activities.public_past_list(filters)[:count]]}
    if kind == "featured_trip":
        try:
            activity = _activity(activities.get_activity(block.get("activity")))
        except activities.NotFound:
            return {"activity": None, "items": []}
        return {"activity": activity, "items": [activity]}
    if kind == "recent_news":
        on = business_settings.get(IMAGES)
        return {"items": [
            {"title": n.title, "url": reverse("website:news_detail", args=[n.slug]),
             "date": n.date, "photo": _image(n.image) if on and n.image and n.image.publishable
             else None} for n in news.published()[:count]
        ]}  # fmt: skip
    if kind == "faq_topic":
        topic_id = block.get("topic")
        topic = FaqTopic.objects.filter(pk=topic_id).first() if topic_id else None
        entries = faq.published_entries(topic) if topic else []
        questions = [{"question": e.question, "answer": catalog.render_markdown(e.answer)}
                     for e in entries]  # fmt: skip
        return {"topic_name": topic.name if topic else "", "questions": questions}
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
