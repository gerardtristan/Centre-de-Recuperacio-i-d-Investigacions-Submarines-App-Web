"""Pàgines, versions i blocs (T-M07-04; P-M07-A, RN-M07-03, 13 i 14; CA-M07-03, 19 i 22).

- `save_page(page, actor, **fields)`: desa les dades de la pàgina (plantilla, accent i adreça
  de llistes tancades o lliures, CA-M07-19) i torna els avisos de compartir (RN-M07-13).
- `save_draft(page, blocks, actor)`: l'únic esborrany de la pàgina (RN-M07-16).
- `publish_page(page, blocks, actor, note)`: versió nova; el públic veu aquesta (RN-M07-03).
- `revert_to(version, actor)`: publica una còpia d'una versió anterior (amb els tipus antics
  traduïts al catàleg de la 106, `blocks.upgrade_all`).
- `validate_blocks(blocks, publishing=...)`: l'esquema de cada tipus (`blocks.CATALOG`).

Tots demanen WP1 (`website.pages`, «Sí») al servidor (catàleg i matriu inicial, T-M07-02).
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.permissions import has_perm

from . import blocks as catalog
from . import media
from .models import Page, PageDraft, PageVersion

PERMISSION = "website.pages"  # WP1
ACTION_PUBLISHED = "website.page_published"

SHARE_TITLE_MAX = 60
SHARE_DESCRIPTION_MAX = 150

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


def validate_blocks(blocks, *, publishing: bool) -> None:
    """Esquema del catàleg (RN-M07-15, CA-M07-23) i, en publicar, les fotos (RN-M07-05)."""
    catalog.validate(blocks, publishing=publishing)
    if publishing:
        media.check_publishable(media.block_media_keys(blocks))


class DraftConflict(ValidationError):
    """Algú altre ha desat l'esborrany des que es va obrir (CA-M07-32): no es desa res."""

    def __init__(self):
        super().__init__(_("Una altra persona ha canviat l'esborrany mentrestant. Torna a carregar "
                           "la pàgina: no s'ha desat res."))  # fmt: skip


def draft_state(page: Page) -> tuple[list, int]:
    """Els blocs que s'editen i la seva revisió: l'esborrany o, si no n'hi ha, l'última versió
    (amb els tipus antics traduïts) amb la revisió 0."""
    draft = PageDraft.objects.filter(page=page).first()
    if draft is not None:
        return draft.blocks, draft.revision
    version = current_version(page)
    return (catalog.upgrade_all(version.blocks) if version else []), 0


@transaction.atomic
def save_draft(page: Page, blocks, actor) -> PageDraft:
    """RN-M07-16: l'únic esborrany de la pàgina, amb la validació de desar (CA-M07-23). Bloqueja
    la pàgina (dos desats alhora no es trepitgen) i puja la revisió; qui ha de comprovar que la
    pantalla estava al dia ho fa abans, amb la pàgina ja bloquejada (`editor.change`)."""
    require(actor)
    validate_blocks(blocks, publishing=False)
    Page.objects.select_for_update().get(pk=page.pk)
    current = draft_state(page)[1]
    draft, _created = PageDraft.objects.update_or_create(
        page=page, defaults={"blocks": blocks, "updated_by": actor, "revision": current + 1}
    )
    return draft


def current_version(page: Page) -> PageVersion | None:
    return page.versions.order_by("-number").first()


@transaction.atomic
def publish_page(page: Page, blocks, actor, note: str = "") -> PageVersion:
    """RN-M07-03: crea la versió següent i deixa la pàgina publicada. Cap versió no canvia."""
    require(actor)
    validate_blocks(blocks, publishing=True)
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


@transaction.atomic
def publish_draft(page: Page, actor, note: str = "", *, revision: int | None = None) -> PageVersion:
    """Publica el que s'edita. Amb `revision`, només si ningú no l'ha canviat des de llavors
    (`DraftConflict`). L'esborrany es queda: continua sent el que s'edita."""
    require(actor)
    Page.objects.select_for_update().get(pk=page.pk)
    blocks, current = draft_state(page)
    if revision is not None and revision != current:
        raise DraftConflict
    return publish_page(page, blocks, actor, note)


def revert_to(version: PageVersion, actor) -> PageVersion:
    """«Tornar a aquesta versió»: publica una còpia dels seus blocs (RN-M07-03)."""
    note = _("Torna a la versió %(n)s") % {"n": version.number}
    return publish_page(version.page, catalog.upgrade_all(version.blocks), actor, note)
