"""Fotos i fitxers de la web (T-M07-07; P-M07-C, RN-M07-05 i 14; CA-M07-05; P-489).

- `upload`, `update_details` i `retire`: WP3 (`website.media`, «Sí») al servidor (catàleg i
  matriu inicial, T-M07-02).
- `check_publishable(keys)`: la crida `pages.publish_page`; cap foto en un bloc publicat sense
  autor, permís d'ús, text alternatiu i, si s'hi veuen persones, el consentiment.
- `public_asset(key)` i `open_content(asset)`: per a la vista pública declarada (P-489). Una foto
  retirada o que no surt a cap versió vigent d'una pàgina publicada és «no trobat» a la petició
  següent, sense cap memòria cau.
"""

import uuid

from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.core import audit, files
from apps.core.permissions import has_perm

from .models import MediaAsset, Page, PageVersion

PERMISSION = "website.media"  # WP3
ACTION_CHANGED = "website.media_changed"
ACTION_RETIRED = "website.media_retired"
# Només formats que mostra qualsevol navegador (el HEIC de la 00, no).
WEB_IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
DETAIL_FIELDS = ("alt_text", "author", "licence_note", "shows_people", "people_consent", "credit")
NOT_PUBLISHABLE = gettext_lazy(
    "Una foto no té autor, permís d'ús o text alternatiu, s'hi veuen persones sense el seu "
    "consentiment, o és retirada."
)


def require(actor):
    if not has_perm(actor, PERMISSION, write=True):
        raise Http404


def upload(uploaded, *, actor, alt_text, shows_people, **details) -> MediaAsset:
    """Desa la foto. El text alternatiu és obligatori; l'autor, el permís i el consentiment es
    poden completar després, però sense ells no es pot publicar."""
    require(actor)
    unknown = set(details) - set(DETAIL_FIELDS)
    if unknown:
        raise ValueError(f"Camps desconeguts: {sorted(unknown)}")
    content_type = files.validate_upload(uploaded, allowed=WEB_IMAGE_TYPES)
    asset = MediaAsset(
        content_type=content_type,
        size_bytes=uploaded.size,
        alt_text=alt_text.strip(),
        shows_people=shows_people,
        uploaded_by=actor,
        **details,
    )
    asset.full_clean(exclude=["storage_key", "uploaded_by"])
    storage = storages["private"]
    asset.storage_key = storage.save(uuid.uuid4().hex, uploaded)
    try:
        asset.save()
    except Exception:
        storage.delete(asset.storage_key)
        raise
    return asset


@transaction.atomic
def update_details(asset: MediaAsset, *, actor, **fields) -> MediaAsset:
    """Autor, permís, persones i consentiment, amb el valor anterior al registre (RN-M07-14)."""
    require(actor)
    if set(fields) - set(DETAIL_FIELDS):
        raise ValueError(f"Camps no editables: {sorted(set(fields) - set(DETAIL_FIELDS))}")
    asset = MediaAsset.objects.select_for_update().get(pk=asset.pk)
    if asset.status == MediaAsset.Status.RETIRED:
        raise ValidationError(_("Una foto retirada no es pot canviar."))
    before = {name: getattr(asset, name) for name in fields}
    for name, value in fields.items():
        setattr(asset, name, value)
    asset.full_clean()
    asset.save(update_fields=list(fields))
    changes = {name: (before[name], getattr(asset, name)) for name in fields}
    audit.record_changes(ACTION_CHANGED, actor=actor, target=asset, changes=changes)
    return asset


@transaction.atomic
def retire(asset: MediaAsset, *, actor, reason: str) -> MediaAsset:
    """La treu de totes les pàgines a la petició següent (RN-M07-05). Amb motiu i registre."""
    require(actor)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal el motiu de la retirada."))
    asset = MediaAsset.objects.select_for_update().get(pk=asset.pk)
    if asset.status == MediaAsset.Status.RETIRED:
        return asset
    asset.status, asset.retired_reason = MediaAsset.Status.RETIRED, reason
    asset.save(update_fields=["status", "retired_reason"])
    audit.record(
        ACTION_RETIRED, actor=actor, target=asset, field="status",
        old=MediaAsset.Status.ACTIVE, new=asset.status, reason=reason,
    )  # fmt: skip
    return asset


def block_media_keys(blocks) -> list[str]:
    """Claus de les fotos dels blocs d'imatge (una) i de galeria (una llista)."""
    keys = []
    for block in blocks:
        if not isinstance(block, dict):
            continue  # el rebutja `pages.validate_blocks`
        value = block.get("media")
        if block.get("kind") == "image":
            if not isinstance(value, str):
                raise ValidationError(_("Un bloc d'imatge porta una sola foto."))
            keys.append(value)
        elif block.get("kind") == "gallery":
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                raise ValidationError(_("Una galeria porta una llista de fotos."))
            keys.extend(value)
    return keys


def _as_uuids(keys) -> set[uuid.UUID]:
    try:
        return {uuid.UUID(key) for key in keys}
    except ValueError:
        raise ValidationError(NOT_PUBLISHABLE) from None


def check_publishable(keys) -> None:
    wanted = _as_uuids(keys)
    ok = {a.key for a in MediaAsset.objects.filter(key__in=wanted) if a.publishable}
    if wanted - ok:
        raise ValidationError(NOT_PUBLISHABLE)


def _published_keys() -> set[uuid.UUID]:
    """Fotos de la versió vigent de cada pàgina publicada (DISTINCT ON de PostgreSQL)."""
    current = (
        PageVersion.objects.filter(page__status=Page.Status.PUBLISHED)
        .order_by("page_id", "-number")
        .distinct("page_id")
        .values_list("blocks", flat=True)
    )
    return _as_uuids(key for blocks in current for key in block_media_keys(blocks))


def public_asset(key: str) -> MediaAsset:
    """CA-M07-05: només una foto publicable que surt en una pàgina publicada; si no, «no trobat»
    (el mateix si no existeix)."""
    try:
        wanted = uuid.UUID(str(key))
    except ValueError:
        raise Http404 from None
    asset = MediaAsset.objects.filter(key=wanted).first()
    if asset is None or not asset.publishable or wanted not in _published_keys():
        raise Http404
    return asset


def open_content(asset: MediaAsset):
    return storages["private"].open(asset.storage_key, "rb")
