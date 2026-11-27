"""Revisor de qualitat abans de publicar (T-M07-25, decisió 106). Només avisos, mai bloquejos: el
que impedeix publicar ho decideix `blocks.validate` (RN-M07-15). Mira el text alternatiu de les
fotos, l'ordre dels títols, els enllaços interns, les seccions buides, els blocs a mig fer, les
llargades per compartir (RN-M07-13) i que hi hagi un sol botó principal a la pàgina (D19)."""

import re
import uuid

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from . import blocks as catalog
from . import media, pages
from .models import MediaAsset, Page
from .routes import route_taken

MD_LINK = re.compile(r"\]\((/[^)\s]*)\)")
PRIMARY = {"join_cta"}  # la crida de la plantilla Captació es pinta com a botó principal


def _internal_links(blocks) -> list[str]:
    links = []
    for block in blocks:
        for value in [block.get("target")] + [i.get("target") for i in block.get("items") or []
                                              if isinstance(i, dict)]:  # fmt: skip
            if isinstance(value, str) and value.startswith("/"):
                links.append(value)
        for name, field in catalog.CATALOG[block["kind"]].items():
            if field.type == "md":
                links += MD_LINK.findall(block.get(name) or "")
    return links


def _broken(path: str) -> bool:
    """Una pàgina interna que no és cap pàgina publicada ni cap pantalla de la plataforma."""
    first = path.strip("/").split("/")[0]
    if not first or route_taken(first):
        return False
    return not Page.objects.filter(slug=first, status=Page.Status.PUBLISHED).exists()


def review(page, blocks) -> list[str]:
    blocks = catalog.upgrade_all(blocks)
    visible = list(catalog.walk(blocks, public_only=True))
    warnings = []
    try:
        catalog.validate(blocks, publishing=True)
    except ValidationError as error:
        warnings += [_("%(problem)s Així no es podrà publicar.") % {"problem": m}
                     for m in error.messages]  # fmt: skip
    keys = {k for k in media.block_media_keys(blocks, public_only=True)}
    assets = MediaAsset.objects.filter(key__in=[uuid.UUID(k) for k in keys])
    if len(assets) < len(keys) or any(not a.alt_text.strip() for a in assets):
        warnings.append(_("Alguna foto no té text alternatiu o ja no és a la biblioteca."))
    levels = [b.get("level") for b in visible if b["kind"] == "heading"]
    if levels and levels[0] == 3:
        warnings.append(_("Hi ha un títol de nivell 3 abans de cap títol de nivell 2."))
    for path in sorted({p for p in _internal_links(visible) if _broken(p)}):
        warnings.append(_("L'enllaç «%(path)s» no porta a cap pàgina publicada.") % {"path": path})
    for block in visible:
        if block["kind"] == "section" and not any(
            not b.get("hidden") for column in block.get("columns") or [] for b in column
        ):
            warnings.append(_("Hi ha una secció buida."))
    primary = [b for b in visible if b["kind"] in PRIMARY or b.get("style") == "primary"]
    if len(primary) > 1:
        warnings.append(_("Hi ha més d'un botó principal a la pàgina; deixa'n només un."))
    return warnings + pages.share_warnings(page)
