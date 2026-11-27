"""Pàgines, versions i blocs (T-M07-04; P-M07-A, RN-M07-03, 13 i 14; CA-M07-03, 19 i 22).

- `save_page(page, actor, **fields)`: desa les dades de la pàgina (plantilla, accent i adreça
  de llistes tancades o lliures, CA-M07-19) i torna els avisos de compartir (RN-M07-13).
- `publish_page(page, blocks, actor, note)`: versió nova; el públic veu aquesta (RN-M07-03).
- `revert_to(version, actor)`: publica una còpia d'una versió anterior.

Tots demanen WP1 (`website.pages`, «Sí») al servidor (catàleg i matriu inicial, T-M07-02).
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.permissions import has_perm

from . import media
from .models import Page, PageVersion

PERMISSION = "website.pages"  # WP1
ACTION_PUBLISHED = "website.page_published"

SHARE_TITLE_MAX = 60
SHARE_DESCRIPTION_MAX = 150

# Tipus de bloc (M07-6, llista tancada) → camps de text que porta.
BLOCK_KINDS = {
    "text": ("title", "text"),
    "image": ("media",),
    "gallery": ("media",),
    "activities": ("filters",),
    "news": (),
    "faq": ("topic",),
    "join_button": (),
    "contact_form": (),
    "newsletter": (),
}
EDITABLE_FIELDS = {
    "slug", "title", "template", "accent", "menu_order", "in_menu", "share_title",
    "share_description",
}  # fmt: skip


def require(actor):
    if not has_perm(actor, PERMISSION, write=True):
        raise Http404


def share_warnings(page: Page) -> list[str]:
    """RN-M07-13: un avís, no un error."""
    warnings = []
    if len(page.share_title) > SHARE_TITLE_MAX:
        warnings.append(
            _("El títol per compartir passa de %(max)s caràcters: es pot veure tallat.")
            % {"max": SHARE_TITLE_MAX}
        )
    if len(page.share_description) > SHARE_DESCRIPTION_MAX:
        warnings.append(
            _("La descripció per compartir passa de %(max)s caràcters: es pot veure tallada.")
            % {"max": SHARE_DESCRIPTION_MAX}
        )
    return warnings


def save_page(page: Page | None, *, actor, **fields) -> tuple[Page, list[str]]:
    """Crea (`page=None`) o canvia una pàgina. Plantilla, accent o adreça fora de la llista o
    d'una ruta existent: `ValidationError` i no es desa res (CA-M07-19)."""
    require(actor)
    unknown = set(fields) - EDITABLE_FIELDS
    if unknown:
        raise ValueError(f"Camps no editables: {sorted(unknown)}")
    page = page or Page()
    for name, value in fields.items():
        setattr(page, name, value)
    page.full_clean()
    page.save()
    return page, share_warnings(page)


def validate_blocks(blocks) -> None:
    if not isinstance(blocks, list):
        raise ValidationError(_("Els blocs han de ser una llista."))
    for block in blocks:
        if not isinstance(block, dict) or block.get("kind") not in BLOCK_KINDS:
            raise ValidationError(_("Hi ha un bloc d'un tipus que no existeix."))
        extra = set(block) - {"kind", *BLOCK_KINDS[block["kind"]]}
        if extra:
            raise ValidationError(_("Un bloc porta camps que no són del seu tipus."))
        # RN-M07-10: text sense format propi; s'escapa en mostrar-lo.
        if any(not isinstance(block.get(f, ""), str) for f in ("title", "text")):
            raise ValidationError(_("El text d'un bloc ha de ser text."))
    media.check_publishable(media.block_media_keys(blocks))  # RN-M07-05
    media.check_publishable(media.block_file_keys(blocks), kind="file")


def current_version(page: Page) -> PageVersion | None:
    return page.versions.order_by("-number").first()


@transaction.atomic
def publish_page(page: Page, blocks, actor, note: str = "") -> PageVersion:
    """RN-M07-03: crea la versió següent i deixa la pàgina publicada. Cap versió no canvia."""
    require(actor)
    validate_blocks(blocks)
    page = Page.objects.select_for_update().get(pk=page.pk)
    previous = page.versions.aggregate(n=Max("number"))["n"] or 0
    version = PageVersion.objects.create(
        page=page, number=previous + 1, blocks=blocks, published_by=actor, note=note.strip()
    )
    if page.status != Page.Status.PUBLISHED:
        page.status = Page.Status.PUBLISHED
        page.save(update_fields=["status"])
    audit.record(
        ACTION_PUBLISHED,
        actor=actor,
        target=page,
        field="version",
        old=previous or None,
        new=version.number,
        reason=version.note,
    )
    return version


def revert_to(version: PageVersion, actor) -> PageVersion:
    """«Tornar a aquesta versió»: publica una còpia dels seus blocs (RN-M07-03)."""
    note = _("Torna a la versió %(n)s") % {"n": version.number}
    return publish_page(version.page, list(version.blocks), actor, note)
