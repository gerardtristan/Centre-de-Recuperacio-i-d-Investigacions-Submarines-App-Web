"""Fotos i fitxers de la web (T-M07-07; P-M07-C, RN-M07-05 i 14; CA-M07-05; P-489).

- `upload`, `update_details` i `retire`: WP3 (`website.media`, «Sí») al servidor (catàleg i
  matriu inicial, T-M07-02).
- `check_publishable(keys)`: la crida `pages.publish_page`; cap foto en un bloc publicat sense
  autor, permís d'ús, text alternatiu i, si s'hi veuen persones, el consentiment.
- `public_asset(key)` i `open_content(asset)`: per a la vista pública declarada (P-489). Una foto
  retirada, o que no surt a la versió vigent de cap pàgina publicada ni a cap notícia publicada,
  és «no trobat» a la petició següent, sense cap memòria cau.

**Pujades (RN-M07-19, addenda M07 de la 106, amb la P-633 A de la 108; CA-M07-28; T-M07-07b):**
només JPEG i PNG (cap WebP ni SVG) i PDF, fins a `website.upload_max_mb`. El tipus surt del
contingut i l'extensió hi ha de correspondre (`core.files.validate_upload`); Pillow ha de poder
obrir la imatge com a aquest format i la torna a codificar, cosa que en treu l'EXIF, el GPS, els
comentaris i qualsevol altra metadada (la rotació de l'EXIF s'aplica abans). Es desen també les
mides en WebP (les fa el servidor, P-633 A) de `RENDITION_WIDTHS` més petites que l'original. El
punt focal (`focal_x`, `focal_y`, en %) s'edita amb `update_details`. Els PDF no es tornen a
codificar: la vista pública els serveix com a descàrrega.
"""

import io
import uuid
import warnings

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from PIL import Image, ImageOps

from apps.core import audit, business_settings, files
from apps.core.models import Setting
from apps.core.permissions import has_perm

from .models import MediaAsset, NewsItem, Page, PageVersion, Tutorial

PERMISSION = "website.media"  # WP3
ACTION_CHANGED = "website.media_changed"
ACTION_RETIRED = "website.media_retired"
# RN-M07-19 amb la P-633 A (108): només JPEG i PNG (cap WebP, HEIC ni SVG) i els PDF. Les mides
# automàtiques, en canvi, les fa el servidor en WebP.
PDF = "application/pdf"
WEB_IMAGE_TYPES = frozenset({"image/jpeg", "image/png"})
UPLOAD_TYPES = WEB_IMAGE_TYPES | {PDF}
_PIL_FORMAT = {"image/jpeg": "JPEG", "image/png": "PNG"}
MAX_MB_KEY = "website.upload_max_mb"
MAX_MB_FALLBACK = 10  # shortcut: fins que el carril E creï la clau (`website/0011`); llavors fora
RENDITION_WIDTHS = (480, 960, 1600)  # format de les mides automàtiques, no un valor de negoci
DETAIL_FIELDS = (
    "alt_text", "author", "licence_note", "shows_people", "people_consent", "credit",
    "focal_x", "focal_y",
)  # fmt: skip
NOT_AN_IMAGE = gettext_lazy("El fitxer no és una imatge vàlida.")
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
    _check_size(uploaded)
    content_type = files.validate_upload(uploaded, allowed=UPLOAD_TYPES)
    uploaded.seek(0)
    data, renditions = uploaded.read(), {}
    if content_type != PDF:
        data, renditions = _reencode(data, content_type)
    clean = ContentFile(data)
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
    saved = []
    try:
        asset.storage_key = storage.save(uuid.uuid4().hex, clean)
        saved.append(asset.storage_key)
        for width, content in renditions.items():
            saved.append(storage.save(uuid.uuid4().hex, ContentFile(content)))
            asset.renditions[str(width)] = saved[-1]
        asset.save()
    except Exception:
        for key in saved:
            storage.delete(key)
        raise
    return asset


def _check_size(uploaded) -> None:
    try:
        max_mb = business_settings.get(MAX_MB_KEY)
    except Setting.DoesNotExist:
        max_mb = MAX_MB_FALLBACK
    if uploaded.size > max_mb * 1024 * 1024:
        raise ValidationError(
            _("El fitxer supera la mida màxima de %(mb)s MB.") % {"mb": max_mb}, code="too_large"
        )


def _reencode(data: bytes, content_type: str) -> tuple[bytes, dict[int, bytes]]:
    """La imatge codificada de nou, sense cap metadada, i les mides en WebP. Una imatge que Pillow
    no obre com al format detectat, o massa gran (bomba de descompressió), es rebutja."""
    fmt = _PIL_FORMAT[content_type]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data), formats=[fmt]) as source:
                source.load()
                icc = source.info.get("icc_profile")
                image = ImageOps.exif_transpose(source)
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError,
            Image.DecompressionBombWarning):  # fmt: skip
        raise ValidationError(NOT_AN_IMAGE, code="type") from None
    # Pillow torna a escriure algunes metadades de `info` (el comentari del JPEG, l'XMP): fora totes
    # menys la transparència.
    image.info = {k: v for k, v in image.info.items() if k == "transparency"}
    out = io.BytesIO()
    options = {"icc_profile": icc} if icc else {}  # el perfil de color no és cap dada personal
    if fmt == "JPEG":
        options["quality"] = 90
    image.save(out, fmt, **options)
    if image.mode not in ("RGB", "RGBA"):
        alpha = "transparency" in image.info or "A" in image.mode
        image = image.convert("RGBA" if alpha else "RGB")
    renditions = {}
    for width in RENDITION_WIDTHS:
        if width >= image.width:
            break
        copy = image.copy()
        copy.thumbnail((width, image.height), Image.Resampling.LANCZOS)
        rendition = io.BytesIO()
        copy.save(rendition, "WEBP", quality=80)
        renditions[width] = rendition.getvalue()
    return out.getvalue(), renditions


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
        elif block.get("kind") == "file":  # PDF de la biblioteca (catàleg de la 106)
            if not isinstance(block.get("file"), str):
                raise ValidationError(_("Un bloc de fitxer porta un sol PDF."))
            keys.append(block["file"])
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


def _is_published(asset: MediaAsset) -> bool:
    """Surt en una notícia publicada o a la versió vigent d'una pàgina publicada. Només es miren
    les versions que contenen aquesta clau (contenció de JSON de PostgreSQL), no totes."""
    if NewsItem.objects.filter(status=NewsItem.Status.PUBLISHED, image=asset).exists():
        return True
    if Tutorial.objects.filter(published=True, image=asset).exists():  # T-M07-10
        return True
    key = str(asset.key)
    candidates = PageVersion.objects.filter(page__status=Page.Status.PUBLISHED).filter(
        Q(blocks__contains=[{"kind": "image", "media": key}])
        | Q(blocks__contains=[{"kind": "gallery", "media": [key]}])
        | Q(blocks__contains=[{"kind": "file", "file": key}])
    )
    for version in candidates.select_related("page"):
        latest = version.page.versions.order_by("-number").values_list("number", flat=True)[0]
        if version.number == latest:
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


def open_content(asset: MediaAsset, width: str = ""):
    """El contingut; amb `width`, la mida en WebP si n'hi ha (si no, l'original)."""
    key = asset.renditions.get(width) or asset.storage_key
    return storages["private"].open(key, "rb")
