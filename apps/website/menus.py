"""Menús, capçalera i peu de la web pública (T-M07-21; addenda 106, decisió 034).

- `save_item(item, actor, **fields)` i `remove_item(item, actor)`: els enllaços del menú.
- `save_chrome(actor, header_text, footer_text, note)`: versió nova de la capçalera i el peu.
- `public_menu(code)` i `current_chrome()`: el que veu el visitant (etiqueta `{% menu_public %}`).

Tots els que desen demanen WP9 (`website.chrome`, «Sí») al servidor i deixen el registre.
"""

from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext as _

from apps.core import audit, business_settings
from apps.core.permissions import has_perm

from . import contact, newsletter
from .models import MenuItem, Page, SiteChrome

PERMISSION = "website.chrome"  # WP9
MAIN = "principal"
# Decisió 034: la pastilla no s'allarga; a partir del setè, els enllaços van a «Més».
VISIBLE_LINKS = 6
ITEM_FIELDS = {"menu", "parent", "label", "page", "url", "order"}
ACTION_ITEM_SAVED = "website.menu_item_saved"
ACTION_ITEM_REMOVED = "website.menu_item_removed"
ACTION_CHROME_SAVED = "website.chrome_saved"
SWITCHES = {"website:contact": contact.ENABLED, "website:newsletter": newsletter.ENABLED}


def require(actor):
    if not has_perm(actor, PERMISSION, write=True):
        raise Http404


def _pk(value):
    return value.pk if hasattr(value, "pk") else value


@transaction.atomic
def save_item(item: MenuItem | None, *, actor, **fields) -> MenuItem:
    """Crea (`item=None`) o canvia un enllaç. Una adreça que no és `https:` ni una ruta que
    existeix, o un submenú dins d'un submenú: `ValidationError` i no es desa res."""
    require(actor)
    if set(fields) - ITEM_FIELDS:
        raise ValueError(f"Camps no editables: {sorted(set(fields) - ITEM_FIELDS)}")
    if item is None:
        item, old = MenuItem(), {}
    else:
        item = MenuItem.objects.select_for_update().get(pk=item.pk)
        old = {name: getattr(item, name) for name in fields}
    for name, value in fields.items():
        setattr(item, name, value)
    item.full_clean()
    item.save()
    changes = {name: (_pk(old.get(name)), _pk(value)) for name, value in fields.items()}
    audit.record_changes(ACTION_ITEM_SAVED, actor=actor, target=item, changes=changes)
    return item


@transaction.atomic
def remove_item(item: MenuItem, *, actor) -> None:
    """Treu un enllaç del menú; un enllaç amb submenú, primer se'n treuen els de dins."""
    require(actor)
    item = MenuItem.objects.select_for_update().get(pk=item.pk)
    if item.children.exists():
        raise ValidationError(_("Aquest enllaç té un submenú: treu primer els enllaços de dins."))
    audit.record(ACTION_ITEM_REMOVED, actor=actor, target=item, field="label", old=item.label)
    item.delete()


def current_chrome() -> SiteChrome | None:
    return SiteChrome.objects.order_by("-number").first()


@transaction.atomic
def save_chrome(*, actor, header_text: str, footer_text: str = "", note: str = "") -> SiteChrome:
    """Una versió nova; cap versió no canvia. Text pla: s'escapa en mostrar-lo (RN-M07-10)."""
    require(actor)
    previous = SiteChrome.objects.aggregate(n=Max("number"))["n"] or 0
    chrome = SiteChrome(
        number=previous + 1,
        header_text=header_text.strip(),
        footer_text=footer_text.strip(),
        saved_by=actor,
        note=note.strip(),
    )
    chrome.full_clean()
    chrome.save()
    audit.record(
        ACTION_CHROME_SAVED,
        actor=actor,
        target=chrome,
        field="number",
        old=previous or None,
        new=chrome.number,
        reason=chrome.note,
    )
    return chrome


def public_menu(code: str = MAIN) -> dict:
    """`links` (fins a 6) i `more` («Més»). Cada enllaç porta `subitems`. No hi surt cap pàgina
    sense publicar ni cap grup buit."""
    items = MenuItem.objects.filter(menu__code=code).select_related("page")
    # Una pantalla apagada respon «no trobat»: el menú no hi enllaça.
    off = {reverse(name) for name, key in SWITCHES.items() if not business_settings.get(key)}

    def shown(item):
        if item.page_id:
            return item.page.status == Page.Status.PUBLISHED
        return item.url not in off

    children = defaultdict(list)
    for item in items:
        if item.parent_id and shown(item):
            children[item.parent_id].append(item)
    top = []
    for item in items:
        if item.parent_id is None and shown(item):
            item.subitems = children[item.pk]
            if item.href or item.subitems:
                top.append(item)
    return {"links": top[:VISIBLE_LINKS], "more": top[VISIBLE_LINKS:]}
