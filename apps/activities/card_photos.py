"""Fotos dels carnets de titulació d'altres agències (T-M02-42; addenda de la 104; RN-M02-47 i
56; CA-M02-49, 50 i 52; 051).

- **Qui:** el titular, amb el seu compte personal, o qui té AC25 en nom seu. Només per a una
  titulació d'una agència diferent de la de destinació (VC-55). Amb VC-56 apagat, es rebutja tot.
- **Què:** una imatge (JPEG o PNG) o un PDF per cara, comprovat amb `core.validate_upload` (mida
  màxima tècnica, al codi). Les metadades de les imatges (EXIF, XMP, IPTC, comentaris i els
  fragments de text del PNG) es treuen aquí, sense cap biblioteca nova (sí del 24/11). La imatge
  no es redueix: sense una biblioteca d'imatge no es pot (D2, P-551).
- **Com es desa:** xifrada a l'aplicació (`core.files`, tipus `certification_photo`), amb el
  titular com a propietari: només l'obren ell i qui té AC24, per la vista amb registre.

Veure-les (la vista de fitxers privats, només amb VC-56 encès: `photos_enabled`, registrada
al nucli) i esborrar-les (`delete`): T-M02-43. Conservació (VC-57, `purge_expired`, cada
dia per la cua): T-M02-47.
"""

import calendar
import struct

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, business_settings, files
from apps.core.models import PrivateFile

from . import catalogue
from .filings import PHOTOS_KEY, _own_or_ac25
from .models import CertificationCardPhoto, CertificationFiling

UPLOADED = "activities.card_photo.uploaded"
DELETED = "activities.card_photo.deleted"
EXPIRED = "activities.card_photo.expired"
RETENTION_KEY = "activities.card_photo_retention_months"  # VC-57
PHOTO_TYPES = frozenset({"image/jpeg", "image/png", "application/pdf"})
_EXTENSION = {"image/jpeg": "jpg", "image/png": "png", "application/pdf": "pdf"}

# JPEG: APP1 (EXIF i XMP), APP13 (IPTC) i COM (comentaris). PNG: fragments de text, EXIF i data.
_JPEG_DROP = {0xE1, 0xED, 0xFE}
_PNG_DROP = {b"eXIf", b"tEXt", b"zTXt", b"iTXt", b"tIME"}


def _broken():
    return ValidationError(_("No s'ha pogut llegir la imatge."), code="broken")


def strip_jpeg(data: bytes) -> bytes:
    """El JPEG sense els segments de metadades; la imatge (des de SOS) es copia tal qual."""
    out, i = bytearray(data[:2]), 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            raise _broken()
        marker = data[i + 1]
        if marker == 0xFF:  # farciment
            i += 1
            continue
        if marker == 0xDA:  # SOS: d'aquí al final són dades de la imatge
            return bytes(out + data[i:])
        length = int.from_bytes(data[i + 2 : i + 4], "big")
        if length < 2 or i + 2 + length > len(data):
            raise _broken()
        if marker not in _JPEG_DROP:
            out += data[i : i + 2 + length]
        i += 2 + length
    raise _broken()


def strip_png(data: bytes) -> bytes:
    """El PNG sense els fragments de text, EXIF ni data (cada fragment porta la seva mida)."""
    out, i = bytearray(data[:8]), 8
    while i + 12 <= len(data):
        (length,) = struct.unpack(">I", data[i : i + 4])
        kind, end = data[i + 4 : i + 8], i + 12 + length
        if end > len(data):
            raise _broken()
        if kind not in _PNG_DROP:
            out += data[i:end]
        if kind == b"IEND":
            return bytes(out)
        i = end
    raise _broken()


_STRIP = {"image/jpeg": strip_jpeg, "image/png": strip_png}


@transaction.atomic
def upload(certification, side: str, uploaded, *, by, request=None) -> CertificationCardPhoto:
    """RN-M02-47: desa la foto d'una cara del carnet, xifrada i sense metadades."""
    _own_or_ac25(certification, by)
    if not business_settings.get(PHOTOS_KEY):
        raise ValidationError(_("Ara mateix no es poden pujar fotos de carnets."))
    target = catalogue.target_agency()
    if target is None or certification.agency_id in (None, target.pk):
        raise ValidationError(_("Només es pot pujar la foto d'una titulació d'una altra agència."))
    if side not in CertificationCardPhoto.Side.values:
        raise ValueError(side)
    if CertificationCardPhoto.objects.filter(certification=certification, side=side).exists():
        raise ValidationError(_("Aquesta cara ja té una foto: esborra-la abans."))
    content_type = files.validate_upload(uploaded, allowed=PHOTO_TYPES)
    uploaded.seek(0)
    content = uploaded.read()
    content = _STRIP.get(content_type, bytes)(content)
    file = files.store(
        content,
        owner=certification.person,
        kind=PrivateFile.Kind.CERTIFICATION_PHOTO,
        content_type=content_type,
        download_name=f"titulacio-{certification.pk}-{side}.{_EXTENSION[content_type]}",
    )
    try:
        with transaction.atomic():
            photo = CertificationCardPhoto.objects.create(
                certification=certification, side=side, file=file,
                content_type=content_type, uploaded_by=by,
            )  # fmt: skip
    except IntegrityError as error:
        raise ValidationError(_("Aquesta cara ja té una foto: esborra-la abans.")) from error
    audit.record(
        UPLOADED, actor=by, target=photo,
        details={"certification": certification.pk, "side": side}, request=request,
    )  # fmt: skip
    return photo


def photos_enabled(file=None) -> bool:
    """RN-M02-56: amb VC-56 apagat, cap foto no s'obre, tampoc per l'adreça directa (el nucli la
    pregunta a `files.can_access`)."""
    return bool(business_settings.get(PHOTOS_KEY))


@transaction.atomic
def delete(photo: CertificationCardPhoto, *, by, request=None) -> None:
    """RN-M02-49: el titular o qui té AC25 l'esborra en qualsevol moment (també amb VC-56
    apagat): la fila i el fitxer, i queda al registre."""
    _own_or_ac25(photo.certification, by)
    file = photo.file
    audit.record(
        DELETED, actor=by, target=photo,
        details={"certification": photo.certification_id, "side": photo.side}, request=request,
    )  # fmt: skip
    photo.delete()
    files.delete_now(file, actor=by, request=request)


def _add_months(day, months: int):
    month = day.month - 1 + months
    year, month = day.year + month // 12, month % 12 + 1
    return day.replace(
        year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1])
    )


def delete_after(photo: CertificationCardPhoto, months: int):
    """RN-M02-54: la data des de la qual s'esborra, o `None` mentre hi ha una homologació oberta.
    Són VC-57 mesos des de l'última d'aquestes coses: la verificació de la titulació, el tancament
    (feta o rebutjada) d'una homologació o, si no n'hi ha cap de posterior, la pujada."""
    homologations = CertificationFiling.objects.filter(
        source_certification_id=photo.certification_id,
        kind=CertificationFiling.Kind.HOMOLOGATION,
    )
    if homologations.filter(status__in=CertificationFiling.OPEN).exists():
        return None
    events = [
        photo.uploaded_at,
        photo.certification.verified_at,
        *homologations.exclude(closed_at=None).values_list("closed_at", flat=True),
    ]
    anchor = max(event for event in events if event is not None)
    return _add_months(timezone.localtime(anchor).date(), months)


def purge_expired(today=None) -> int:
    """La tasca diària (T-M02-47, CA-M02-56): esborra les fotos vençudes, la fila i el fitxer, amb
    l'actor «sistema». La titulació conserva la verificació. Torna quantes n'ha esborrat."""
    today = today or timezone.localdate()
    months = business_settings.get(RETENTION_KEY)
    actor = audit.system("activities.purge_card_photos")
    count = 0
    for photo in CertificationCardPhoto.objects.select_related("certification", "file"):
        due = delete_after(photo, months)
        if due is None or due > today:
            continue
        with transaction.atomic():
            details = {"certification": photo.certification_id, "side": photo.side}
            audit.record(EXPIRED, actor=actor, target=photo, details=details)
            file = photo.file
            photo.delete()
            files.delete_now(file, actor=actor)
        count += 1
    return count
