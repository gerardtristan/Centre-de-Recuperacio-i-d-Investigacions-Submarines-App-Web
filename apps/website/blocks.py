"""Catàleg de blocs de la web (T-M07-04 i decisió 106: RN-M07-10 i 15; CA-M07-23 i 24).

- `CATALOG`: els 26 tipus de l'addenda de la 106 (`planning.md#M07-addenda-106`), amb els camps,
  els límits i les variants tancades de cadascun. La llista és codi (RN-M07-15). Tot bloc porta
  també `hidden`: es desa, però no surt a la web pública.
- `validate(blocks, publishing=...)`: un tipus, un camp o una variant que no són a l'esquema es
  rebutgen sempre (CA-M07-23). En desar un esborrany, un camp que encara no s'ha omplert (absent,
  buit o sense prou elements) es deixa passar perquè el desat automàtic no perdi la feina; en
  publicar, no (P-680).
- `upgrade_all(blocks)`: tradueix els tipus de la llista inicial de M07-6 en llegir-los; les
  versions desades són només d'INSERT i no es reescriuen.
- `render_markdown(text)`: el Markdown restringit de RN-M07-10, amb l'HTML desactivat.

Els valors de les variants són els codis d'aquest fitxer (el primer de cada llista és el que val
si no se'n tria cap); les plantilles de disseny (`website/blocs/<kind>.html`) els fan servir tal
qual.
"""

import re
import uuid

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from markdown_it import MarkdownIt

from apps.activities.models import Activity
from apps.core import business_settings

# Límits de format i de seguretat (no són valors de negoci).
TITLE_MAX = 120  # el mateix que el títol d'una pàgina
MD_MAX = 20_000  # un text llarg no pot fer créixer sense límit una versió
CODE_MAX = 60

BACKGROUND = ("none", "soft", "marine", "accent")
WIDTH = ("normal", "wide", "full")
LAYOUT = ("list", "cards")


class Field:
    """`type`: text, md, int, choice, media, ref, youtube, target, filters, items o columns."""

    def __init__(self, type, *, required=True, max=None, min=None, choices=(), item=None,
                 max_setting=None):  # fmt: skip
        self.type, self.required, self.max, self.min = type, required, max, min
        self.choices, self.item, self.max_setting = choices, item, max_setting


def text(max=TITLE_MAX, required=True):
    return Field("text", max=max, required=required)


def md():
    return Field("md", max=MD_MAX)


def variant(*choices):
    return Field("choice", required=False, choices=choices)


def items(item, min, max):
    return Field("items", item=item, min=min, max=max)


OPTIONAL_TITLE = text(required=False)
MEDIA = Field("media")
TARGET = Field("target")
FILTERS = Field("filters", required=False)
HOME_COUNT = Field("int", min=1, max_setting="website.home_activities_count")
NEWS_COUNT = Field("int", min=1, max_setting="website.news_on_home")

CATALOG = {
    # Text
    "heading": {"text": text(120), "level": Field("choice", choices=(2, 3))},
    "text": {"title": OPTIONAL_TITLE, "body": md(), "width": variant(*WIDTH)},
    "quote": {"text": text(400), "attribution": OPTIONAL_TITLE, "background": variant(*BACKGROUND)},
    "list": {"title": OPTIONAL_TITLE, "items": items(text(200), 1, 20),
             "style": variant("bullets", "numbers", "checks")},
    "disclosure": {"question": text(200), "answer": md()},
    "callout": {"title": OPTIONAL_TITLE, "body": md(), "tone": variant("info", "warning")},
    # Mitjans
    "image": {"media": MEDIA, "caption": OPTIONAL_TITLE, "width": variant(*WIDTH)},
    "gallery": {"media": items(MEDIA, 2, 24), "caption": OPTIONAL_TITLE,
                "columns": variant(2, 3, 4)},
    "image_text": {"media": MEDIA, "title": text(), "body": md(),
                   "image_side": variant("left", "right"), "background": variant(*BACKGROUND)},
    "video": {"source": Field("choice", choices=("youtube", "own")),
              "youtube_id": Field("youtube", required=False),
              "video": Field("ref", required=False), "title": text(),
              "thumbnail": Field("media", required=False), "width": variant(*WIDTH)},
    "file": {"file": Field("ref"), "label": text()},
    # Disposició
    "section": {"columns": Field("columns", min=1, max=3), "background": variant(*BACKGROUND),
                "width": variant(*WIDTH)},
    "divider": {},
    "spacer": {"size": variant("small", "medium", "large")},
    # Acció
    "button": {"label": text(40), "target": TARGET, "style": variant("secondary", "primary")},
    "join_cta": {"title": text(), "body": md(), "background": variant(*BACKGROUND)},
    "newsletter": {"title": OPTIONAL_TITLE},
    "contact_form": {"title": OPTIONAL_TITLE},
    # Dades del club
    "upcoming_activities": {"title": text(), "filters": FILTERS,
                            "count": HOME_COUNT,
                            "layout": variant(*LAYOUT)},
    "featured_activities": {"title": text(), "layout": variant(*LAYOUT)},
    "past_activities": {"title": text(), "filters": FILTERS, "count": Field("int", min=1, max=12),
                        "layout": variant(*LAYOUT)},
    "recent_news": {"title": text(), "count": NEWS_COUNT,
                    "layout": variant(*LAYOUT)},
    "faq_topic": {"topic": Field("int", min=1)},  # un `FaqTopic`
    "key_figures": {"items": items({"value": text(12), "label": text(40)}, 2, 4),
                    "background": variant(*BACKGROUND)},
    "project_cards": {"items": items({"title": text(), "body": md(), "media": MEDIA,
                                      "target": TARGET}, 1, 6),
                      "columns": variant(2, 3)},
    "featured_trip": {"activity": Field("int", min=1), "title": OPTIONAL_TITLE,
                      "background": variant(*BACKGROUND)},
    # Referència a un bloc compartit (`SharedBlock`, T-M07-20a; P-688): el contingut és el seu.
    "shared": {"shared": Field("int", min=1)},
}  # fmt: skip
COMMON = {"kind", "hidden"}
EMPTY = (None, "", [], {})
YOUTUBE_ID = re.compile(r"[A-Za-z0-9_-]{11}")
INTERNAL_PATH = re.compile(r"/(?:[a-z0-9-]+/)*")
_https = URLValidator(schemes=["https"])


class _Bad(Exception):
    """Un valor fora d'esquema; el converteix en `ValidationError` qui sap de quin bloc és."""


def _check_target(value) -> None:
    if not isinstance(value, str):
        raise _Bad
    if INTERNAL_PATH.fullmatch(value):
        return
    try:
        _https(value)
    except ValidationError:
        raise _Bad from None


def _check(field: Field, value, publishing: bool) -> None:
    """Valor present (no buit) d'un camp. `_Bad` si és fora d'esquema."""
    t = field.type
    if t in ("text", "md"):
        if not isinstance(value, str) or len(value) > field.max:
            raise _Bad
    elif t == "choice":
        if not any(value == c and type(value) is type(c) for c in field.choices):
            raise _Bad
    elif t == "int":
        top = business_settings.get(field.max_setting) if field.max_setting else field.max
        if type(value) is not int or value < field.min or (top is not None and value > top):
            raise _Bad
    elif t in ("media", "ref"):
        try:
            canonical = str(uuid.UUID(value)) == value  # la forma que busca `media._is_published`
        except (TypeError, ValueError, AttributeError):
            raise _Bad from None
        if not canonical:
            raise _Bad
    elif t == "youtube":
        if not isinstance(value, str) or not YOUTUBE_ID.fullmatch(value):
            raise _Bad
    elif t == "target":
        _check_target(value)
    elif t == "filters":  # `type`: curs o sortida (02); `department`: un departament de la 00
        if not isinstance(value, dict) or set(value) - {"type", "department"}:
            raise _Bad
        if value.get("type") not in (None, "", *Activity.Kind.values):
            raise _Bad
        department = value.get("department")
        if department is not None and (type(department) is not int or department < 1):
            raise _Bad
    elif t == "items":
        if not isinstance(value, list) or len(value) > field.max:
            raise _Bad
        if publishing and len(value) < field.min:
            raise _Bad
        for item in value:
            if isinstance(field.item, dict):
                _check_fields(field.item, item, publishing, allowed=set())
            elif item in EMPTY:
                if publishing:
                    raise _Bad
            else:
                _check(field.item, item, publishing)
    else:  # columns: una llista buida ja és un camp buit (EMPTY)
        if not isinstance(value, list) or len(value) > field.max:
            raise _Bad
        for column in value:
            _validate(column, publishing, nested=True)


def _check_fields(schema: dict, data, publishing: bool, allowed: set) -> None:
    if not isinstance(data, dict) or set(data) - set(schema) - allowed:
        raise _Bad
    for name, field in schema.items():
        value = data.get(name)
        if value in EMPTY:
            if publishing and field.required:
                raise _Bad
            continue
        _check(field, value, publishing)


def _check_block(block, publishing: bool, nested: bool) -> None:
    kind = block.get("kind") if isinstance(block, dict) else None
    if kind not in CATALOG or (nested and kind == "section"):
        raise _Bad
    if not isinstance(block.get("hidden", False), bool):
        raise _Bad
    _check_fields(CATALOG[kind], block, publishing, allowed=COMMON)
    if kind == "video" and publishing:
        needed = "youtube_id" if block.get("source") == "youtube" else "video"
        if block.get(needed) in EMPTY:
            raise _Bad


def _validate(blocks, publishing: bool, nested: bool = False) -> None:
    if not isinstance(blocks, list):
        raise ValidationError(_("Els blocs han de ser una llista."))
    for number, block in enumerate(blocks, start=1):
        try:
            _check_block(block, publishing, nested)
        except _Bad:
            raise ValidationError(
                _("El bloc %(n)s no és com el seu tipus demana (camp, variant o límit).")
                % {"n": number}
            ) from None


def validate(blocks, *, publishing: bool) -> None:
    """RN-M07-15 i CA-M07-23: `ValidationError` si cal rebutjar-los; qui desa no desa res."""
    _validate(blocks, publishing)


def walk(blocks, *, public_only: bool = False):
    """Tots els blocs, també els de dins de les seccions. `public_only`: sense els amagats."""
    for block in blocks:
        if public_only and block.get("hidden"):
            continue
        yield block
        if block.get("kind") == "section":
            for column in block.get("columns") or []:
                yield from walk(column, public_only=public_only)


# Llista inicial de M07-6 → catàleg de la 106 (l'addenda: «la T-M07-04 en fa la migració»).
def _upgrade(block):
    if not isinstance(block, dict):
        return block
    kind = block.get("kind")
    if kind == "text" and "text" in block:
        new = {k: v for k, v in block.items() if k != "text"}
        return {**new, "body": block["text"]}
    if kind == "activities":
        new = {"kind": "upcoming_activities", "title": _("Properes activitats"),
               "count": business_settings.get("website.home_activities_count")}  # fmt: skip
        return {**new, **({"filters": block["filters"]} if block.get("filters") else {})}
    if kind == "news":
        count = business_settings.get("website.news_on_home")
        return {"kind": "recent_news", "title": _("Notícies"), "count": count}
    if kind == "faq":
        return {"kind": "faq_topic", "topic": block.get("topic")}
    if kind == "join_button":
        return {"kind": "join_cta", "title": _("Fes-te soci"), "body": _("Uneix-te al C.R.I.S.")}
    return block


def upgrade_all(blocks) -> list:
    return [_upgrade(block) for block in blocks]


# RN-M07-10: negreta, cursiva, enllaç, llistes i títols 2 i 3; HTML desactivat.
_md = MarkdownIt("zero", {"html": False}).enable(
    ["emphasis", "link", "list", "heading", "escape", "newline"]
)


def _allowed_link(url: str) -> bool:
    """Un enllaç amb un altre esquema no es fa: es queda com a text."""
    if url.lower().startswith(("https:", "mailto:", "tel:")):
        return True
    return url.startswith("/") and not url.startswith("//")


def _clamp_headings(state) -> None:
    """L'`h1` és el títol de la pàgina: `#` es pinta com a `h2` i `####` o més com a `h3`."""
    for token in state.tokens:
        if token.type in ("heading_open", "heading_close"):
            token.tag = "h2" if token.tag == "h1" else min(token.tag, "h3")


_md.validateLink = _allowed_link
_md.core.ruler.push("clamp_headings", _clamp_headings)


def render_markdown(text: str) -> str:
    """HTML segur: markdown-it n'escapa tot el text i només en fa les etiquetes permeses."""
    return mark_safe(_md.render(text or ""))  # noqa: S308
