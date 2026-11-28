"""Fotos i fitxers de la web (T-M07-07; P-M07-C, RN-M07-05 i 14; CA-M07-05; P-489).

- `upload`, `update_details` i `retire`: WP3 (`website.media`, «Sí») al servidor (catàleg i
  matriu inicial, T-M07-02).
- `check_publishable(keys)`: la crida `pages.publish_page`; cap foto en un bloc publicat sense
  autor, permís d'ús, text alternatiu i, si s'hi veuen persones, el consentiment.
- `public_asset(key)` i `open_content(asset)`: per a la vista pública declarada (P-489). Una foto
  retirada, o que no surt a la versió vigent de cap pàgina publicada ni a cap notícia publicada,
  és «no trobat» a la petició següent, sense cap memòria cau.
"""

import uuid

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.activities.card_photos import strip_jpeg, strip_png
from apps.core import audit, business_settings, files
from apps.core.permissions import has_perm

from . import blocks as catalog
from .models import MediaAsset, NewsItem, Page, PageVersion, SharedBlockVersion, Tutorial

PERMISSION = "website.media"  # WP3
ACTION_CHANGED = "website.media_changed"
ACTION_RETIRED = "website.media_retired"
# Només formats que mostra qualsevol navegador i dels quals es poden treure les metadades sense cap
# biblioteca nova (el HEIC de la 00, no; el WebP, tampoc: P-633).
WEB_IMAGE_TYPES = frozenset({"image/jpeg", "image/png"})
_STRIP = {"image/jpeg": strip_jpeg, "image/png": strip_png}
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
    return _store(uploaded, actor=actor, alt_text=alt_text, shows_people=shows_people, **details)


def store_image(content: bytes, *, actor, alt_text, shows_people, **details) -> MediaAsset:
    """Una imatge que obté el servidor (la miniatura d'un vídeo, T-M07-23), amb la mateixa
    validació i neteja que una pujada. Demana WP3, com una pujada."""
    require(actor)
    name = "imatge.png" if content.startswith(b"\x89PNG") else "imatge.jpg"
    uploaded = SimpleUploadedFile(name, content)
    return _store(uploaded, actor=actor, alt_text=alt_text, shows_people=shows_people, **details)


VIDEO_UPLOADS = "website.video_upload_enabled"
MP4_BRANDS = {b"isom", b"iso2", b"mp41", b"mp42", b"avc1", b"M4V "}


def upload_video(uploaded, *, actor, alt_text, shows_people, **details) -> MediaAsset:
    """RN-M07-26 i P-610: només MP4, comprovat pel contingut, i com a màxim
    `website.upload_max_mb`. Darrere de `website.video_upload_enabled`, apagat (P-687: les
    metadades d'un MP4, com el lloc, encara no se'n treuen)."""
    require(actor)
    if not business_settings.get(VIDEO_UPLOADS):
        raise ValidationError(_("La pujada de vídeos no està activada."))
    uploaded.seek(0)
    head = uploaded.read(12)
    if head[4:8] != b"ftyp" or head[8:12] not in MP4_BRANDS:
        raise ValidationError(_("Només es poden pujar vídeos MP4."))
    if uploaded.size > business_settings.get("website.upload_max_mb") * 1024 * 1024:
        raise ValidationError(_("El vídeo és massa gran."))
    uploaded.seek(0)
    content = ContentFile(uploaded.read())
    return _save(content, "video/mp4", actor=actor, alt_text=alt_text, shows_people=shows_people,
                 **details)  # fmt: skip


def _store(uploaded, *, actor, alt_text, shows_people, **details) -> MediaAsset:
    content_type = files.validate_upload(uploaded, allowed=WEB_IMAGE_TYPES)
    uploaded.seek(0)
    # Sense metadades (EXIF amb el GPS, número de sèrie, propietari, comentaris): el mateix mètode
    # que les fotos dels carnets (T-M02-42), sense cap biblioteca nova.
    clean = ContentFile(_STRIP[content_type](uploaded.read()))
    return _save(clean, content_type, actor=actor, alt_text=alt_text, shows_people=shows_people,
                 **details)  # fmt: skip


def _save(clean, content_type, *, actor, alt_text, shows_people, **details) -> MediaAsset:
    unknown = set(details) - set(DETAIL_FIELDS)
    if unknown:
        raise ValueError(f"Camps desconeguts: {sorted(unknown)}")
    asset = MediaAsset(
        content_type=content_type,
        size_bytes=clean.size,
        alt_text=alt_text.strip(),
        shows_people=shows_people,
        uploaded_by=actor,
        **details,
    )
    asset.full_clean(exclude=["storage_key", "uploaded_by"])
    storage = storages["private"]
    asset.storage_key = storage.save(uuid.uuid4().hex, clean)
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


def block_media_keys(blocks, *, public_only: bool = False) -> list[str]:
    """Claus de les fotos dels blocs (també dins de seccions i targetes), ja validats amb
    `blocks.validate`. `public_only`: sense els blocs amagats, que no surten a la web."""
    keys = []
    for block in catalog.walk(blocks, public_only=public_only):
        kind = block["kind"]
        if kind in ("image", "image_text") and block.get("media"):
            keys.append(block["media"])
        elif kind == "gallery":
            keys.extend(k for k in block.get("media") or [] if k)  # un forat de l'esborrany, no
        elif kind == "video":  # la miniatura i, si és un vídeo propi, el vídeo (RN-M07-26)
            keys += [k for k in (block.get("thumbnail"), block.get("video")) if k]
        elif kind == "project_cards":
            keys.extend(item["media"] for item in block.get("items") or [] if item.get("media"))
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


def _is_published(asset: MediaAsset) -> bool:
    """Surt en una notícia publicada o en un bloc visible de la versió vigent d'una pàgina
    publicada. Només es miren les versions que contenen el text de la clau, no totes."""
    if NewsItem.objects.filter(status=NewsItem.Status.PUBLISHED, image=asset).exists():
        return True
    if Tutorial.objects.filter(published=True, image=asset).exists():  # T-M07-10
        return True
    from .library import resolve  # una foto dins d'un bloc compartit (T-M07-20a)

    key = str(asset.key)
    mentions = Q(blocks__icontains=key)
    if SharedBlockVersion.objects.filter(block__icontains=key).exists():
        mentions |= Q(blocks__icontains='"shared"')
    candidates = PageVersion.objects.filter(mentions, page__status=Page.Status.PUBLISHED)
    for version in candidates.select_related("page"):
        latest = version.page.versions.order_by("-number").values_list("number", flat=True)[0]
        blocks = resolve(catalog.upgrade_all(version.blocks))
        if version.number == latest and key in block_media_keys(blocks, public_only=True):
            return True
    return False


def public_asset(key: str) -> MediaAsset:
    """CA-M07-05: només una foto publicable que surt en una pàgina publicada; si no, «no trobat»
    (el mateix si no existeix)."""
    try:
        wanted = uuid.UUID(str(key))
    except ValueError:
        raise Http404 from None
    asset = MediaAsset.objects.filter(key=wanted).first()
    if asset is None or not asset.publishable or not _is_published(asset):
        raise Http404
    return asset


def open_content(asset: MediaAsset):
    return storages["private"].open(asset.storage_key, "rb")
