"""Fitxers privats, versió mínima (spec 00, annex B; decisions 005, 010 i 035; V-08).

- El contingut és a l'emmagatzematge «private» (`STORAGES`): Scaleway Object Storage a París a
  producció, amb l'API S3 estàndard; fora de producció, `LocalSignedStorage`, que l'imita en
  una carpeta local. Cap compte de Scaleway fora de producció.
- Només s'hi arriba amb una URL signada de curta durada (`PRIVATE_FILES_SIGNED_URL_TTL`,
  5 minuts), que es genera després de comprovar el compte i l'objecte (`can_access`). Sense
  permís, «no trobat».
- Clau i identificador aleatoris: cap nom previsible, cap dada personal a la ruta.
- Els fitxers pujats es comproven pel contingut i per la mida (`validate_upload`; checklist C10).
- L'exportació RGPD caduca als `GDPR_EXPORT_RETENTION_DAYS` dies i la tasca diària l'esborra.

Fora d'abast ara: els fitxers de cada mòdul (carnet en PDF a la T-M01-19, exportació RGPD a la
T-M01-22), el bloqueig en un esborrat RGPD (RN-B8) i les còpies (RN-B6).
"""

import datetime
import time
import uuid
from pathlib import Path

from django.conf import settings
from django.core import signing
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, storages
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext

from . import audit
from .models import PrivateFile
from .permissions import has_perm

# V-08: tipus permesos als fitxers pujats; el CSV, només a les importacions.
UPLOAD_TYPES = frozenset({"application/pdf", "image/jpeg", "image/png", "image/webp", "image/heic"})
IMPORT_TYPES = frozenset({"text/csv"})

_EXTENSIONS = {
    "application/pdf": {".pdf"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "image/heic": {".heic", ".heif"},
    "text/csv": {".csv"},
}
_HEIC_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"mif1", b"msf1"}

# Permís que deixa obrir un fitxer d'una altra persona, segons el tipus (RN-B4).
_KIND_PERMISSION = {PrivateFile.Kind.GDPR_EXPORT: "core.gdpr.handle"}

_LOCAL_SALT = "apps.core.files.local"


class LinkRejected(Exception):
    """Enllaç local caducat, manipulat o d'un fitxer que ja no hi és."""


def _detect(head: bytes) -> str | None:
    """Tipus real pels primers bytes, no per l'extensió (RN-B3)."""
    if head.startswith(b"%PDF-"):
        return "application/pdf"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head[4:8] == b"ftyp" and head[8:12] in _HEIC_BRANDS:
        return "image/heic"
    return None


def _looks_like_text(head: bytes) -> bool:
    if b"\x00" in head:
        return False
    try:
        head.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def validate_upload(uploaded, *, allowed=UPLOAD_TYPES) -> str:
    """Comprova la mida i el tipus d'un fitxer pujat i en torna el tipus real.

    El tipus surt del contingut i l'extensió hi ha de correspondre (CA-B1, CA-B2).
    """
    if uploaded.size > settings.UPLOAD_MAX_BYTES:
        raise ValidationError(
            gettext("El fitxer supera la mida màxima de %(mb)s MB.")
            % {"mb": settings.UPLOAD_MAX_BYTES // (1024 * 1024)},
            code="too_large",
        )
    if uploaded.size == 0:
        raise ValidationError(gettext("El fitxer és buit."), code="empty")

    uploaded.seek(0)
    head = uploaded.read(64 * 1024)
    uploaded.seek(0)
    detected = _detect(head)
    if detected is None and "text/csv" in allowed and _looks_like_text(head):
        detected = "text/csv"

    extension = Path(uploaded.name or "").suffix.lower()
    if detected not in allowed or extension not in _EXTENSIONS[detected]:
        raise ValidationError(gettext("Aquest tipus de fitxer no és permès."), code="type")
    return detected


def store(
    content: bytes, *, owner, kind: str, content_type: str, download_name: str
) -> PrivateFile:
    """Desa un fitxer generat per la plataforma (p. ex. una exportació) i el registra."""
    key = uuid.uuid4().hex
    expires_at = None
    if kind == PrivateFile.Kind.GDPR_EXPORT:
        expires_at = timezone.now() + datetime.timedelta(days=settings.GDPR_EXPORT_RETENTION_DAYS)
    storage = storages["private"]
    saved = storage.save(key, ContentFile(content))
    try:
        return PrivateFile.objects.create(
            storage_key=saved,
            kind=kind,
            owner=owner,
            content_type=content_type,
            size_bytes=len(content),
            download_name=download_name,
            expires_at=expires_at,
        )
    except Exception:
        storage.delete(saved)
        raise


def can_access(account, file: PrivateFile) -> bool:
    """El compte pot obrir el fitxer? El titular, amb el seu compte personal; un compte
    d'administrador, només amb el permís del tipus de fitxer (rol i objecte)."""
    from apps.accounts.models import Account

    if file.deleted_at is not None or (file.expires_at and file.expires_at <= timezone.now()):
        return False
    if not isinstance(account, Account) or not account.is_active:
        return False
    if account.kind == Account.Kind.PERSONAL:
        return account.person_id == file.owner_id
    return has_perm(account, _KIND_PERMISSION[file.kind], file.owner)


def signed_url(account, file: PrivateFile, *, request=None) -> str:
    """URL signada de curta durada, només si el compte hi té accés; si no, «no trobat».

    El registre d'activitat guarda qui l'ha demanada i de quin fitxer; mai la URL (RN-52).
    """
    if not can_access(account, file):
        raise Http404
    audit.record(
        audit.Action.FILE_URL_ISSUED,
        actor=account,
        target=file,
        details={"kind": file.kind},
        request=request,
    )
    return storages["private"].url(
        file.storage_key,
        parameters={
            "ResponseContentDisposition": f'attachment; filename="{file.download_name}"',
            "ResponseContentType": file.content_type,
        },
        expire=settings.PRIVATE_FILES_SIGNED_URL_TTL,
    )


def purge_expired() -> int:
    """Esborra els fitxers caducats (V-08: exportació RGPD als 7 dies). Torna quants."""
    now = timezone.now()
    storage = storages["private"]
    expired = PrivateFile.objects.filter(expires_at__lte=now, deleted_at__isnull=True)
    count = 0
    for file in expired:
        storage.delete(file.storage_key)
        file.deleted_at = now
        file.save(update_fields=["deleted_at"])
        audit.record(
            audit.Action.FILE_DELETED,
            actor=audit.system("files.purge_expired"),
            target=file,
            details={"kind": file.kind},
        )
        count += 1
    return count


class LocalSignedStorage(FileSystemStorage):
    """Emmagatzematge local que imita Scaleway fora de producció (decisió 010).

    Les URL que dona porten la clau i la caducitat signades amb la clau de Django: com les de
    S3, són la credencial i, passat el termini, es rebutgen. No s'admet a producció.
    """

    def __init__(self, **kwargs):
        if not settings.PRIVATE_FILES_LOCAL_ALLOWED:
            raise ImproperlyConfigured(
                "L'emmagatzematge local de fitxers privats no s'admet en aquest entorn."
            )
        super().__init__(**kwargs)

    def url(self, name, parameters=None, expire=None, http_method=None):
        ttl = expire or settings.PRIVATE_FILES_SIGNED_URL_TTL
        token = signing.dumps({"k": name, "e": int(time.time()) + ttl}, salt=_LOCAL_SALT)
        return reverse("core:local_private_file", args=[token])


def open_local(token: str) -> tuple[PrivateFile, object]:
    """Obre el fitxer d'un enllaç local signat, o aixeca `LinkRejected`."""
    try:
        payload = signing.loads(token, salt=_LOCAL_SALT)
    except signing.BadSignature:
        raise LinkRejected from None
    if not isinstance(payload, dict) or payload.get("e", 0) < time.time():
        raise LinkRejected
    file = PrivateFile.objects.filter(storage_key=payload.get("k"), deleted_at__isnull=True).first()
    if file is None:
        raise LinkRejected
    return file, storages["private"].open(file.storage_key, "rb")
