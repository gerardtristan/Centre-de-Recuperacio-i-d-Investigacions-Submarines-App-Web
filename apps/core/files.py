"""Fitxers privats, versió mínima (spec 00, annex B; decisions 005, 010 i 035; V-08).

- El contingut és a l'emmagatzematge «private» (`STORAGES`): Scaleway Object Storage a París a
  producció, amb l'API S3 estàndard; fora de producció, `LocalSignedStorage`, que l'imita en
  una carpeta local. Cap compte de Scaleway fora de producció.
- Només s'hi arriba amb una URL signada de curta durada (`PRIVATE_FILES_SIGNED_URL_TTL`,
  5 minuts), que es genera després de comprovar el compte i l'objecte (`can_access`). Sense
  permís, «no trobat».
- Els tipus d'`ENCRYPTED_KINDS` (documents de justificació de la 051, factures emeses i fotos de
  titulacions de la 104; T-M09-25a) es xifren a l'aplicació abans de desar-los, amb la clau
  pròpia `FILE_ENCRYPTION_KEYS`. No tenen mai URL signada: només surten desxifrats per la vista
  `private_file`, amb `open_decrypted`, que comprova `can_access` i deixa cada obertura al
  registre d'activitat. Els documents de justificació no els torna a obrir qui els ha pujat:
  només els comptes d'administrador amb el permís (RN-M09-23).
- Clau i identificador aleatoris: cap nom previsible, cap dada personal a la ruta.
- Els fitxers pujats es comproven pel contingut i per la mida (`validate_upload`; checklist C10).
- L'exportació RGPD caduca als `GDPR_EXPORT_RETENTION_DAYS` dies i la tasca diària l'esborra.
- En un esborrat RGPD, els fitxers de la persona sense obligació legal s'esborren (RN-B8):
  `expire_owner_files`: l'exportació RGPD i les fotos de titulacions. Un tipus amb obligació
  legal (factures, justificants) no ha d'entrar a `ERASABLE_KINDS`: es bloqueja amb el seu mòdul.

Fora d'abast ara: els fitxers de cada mòdul (carnet en PDF a la T-M01-19) i les còpies (RN-B6).
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
from django.db import transaction
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext

from . import audit, crypto
from .models import PrivateFile
from .permissions import has_perm

# V-08: tipus permesos als fitxers pujats; el CSV, només a les importacions.
UPLOAD_TYPES = frozenset({"application/pdf", "image/jpeg", "image/png", "image/webp", "image/heic"})
IMPORT_TYPES = frozenset({"text/csv"})
# L'extracte bancari també pot ser un fitxer de text Norma 43 (T-M00-09).
BANK_STATEMENT_TYPES = frozenset({"text/csv", "text/plain"})
# El fitxer de retornats del banc és XML (pain.002; T-M05b-12b).
BANK_RETURNS_TYPES = frozenset({"application/xml"})

_EXTENSIONS = {
    "application/pdf": {".pdf"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "image/heic": {".heic", ".heif"},
    "text/csv": {".csv"},
    "text/plain": {".n43", ".txt"},
    "application/xml": {".xml"},
}
_HEIC_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"mif1", b"msf1"}

# Permís que deixa obrir un fitxer d'una altra persona, segons el tipus (RN-B4).
_KIND_PERMISSION = {
    PrivateFile.Kind.GDPR_EXPORT: "core.gdpr.handle",
    PrivateFile.Kind.PAYMENT_PROOF: "core.charges.record_manual",  # M14 (P-12b; P-405)
    # 051 (RN-M09-23): només el tresorer i la junta, permisos protegits.
    PrivateFile.Kind.EXPENSE_INVOICE: "expenses.documents.open",  # C5
    PrivateFile.Kind.EXPENSE_BANK_PROOF: "expenses.documents.open",
    PrivateFile.Kind.EXPENSE_MASKED_COPY: "expenses.documents.open",
    PrivateFile.Kind.GRANT_PACKAGE: "grants.documents.open",  # AJ12
    PrivateFile.Kind.ISSUED_INVOICE: "expenses.invoices.issue",  # MG9; el client, amb el personal
    PrivateFile.Kind.CERTIFICATION_PHOTO: "activities.card_photos.view",  # AC24 (RN-M02-48)
}

# Xifrats a l'aplicació abans de desar-los (051 i 104): mai URL signada.
ENCRYPTED_KINDS = frozenset(
    {
        PrivateFile.Kind.EXPENSE_INVOICE,
        PrivateFile.Kind.EXPENSE_BANK_PROOF,
        PrivateFile.Kind.EXPENSE_MASKED_COPY,
        PrivateFile.Kind.ISSUED_INVOICE,
        PrivateFile.Kind.GRANT_PACKAGE,
        PrivateFile.Kind.CERTIFICATION_PHOTO,
    }
)
# El titular (qui l'ha pujat) no el torna a obrir amb el compte personal (RN-M09-23).
_ADMIN_ONLY_KINDS = frozenset(
    {
        PrivateFile.Kind.EXPENSE_INVOICE,
        PrivateFile.Kind.EXPENSE_BANK_PROOF,
        PrivateFile.Kind.EXPENSE_MASKED_COPY,
        PrivateFile.Kind.GRANT_PACKAGE,
    }
)

_LOCAL_SALT = "apps.core.files.local"


def _local_signer() -> signing.Signer:
    # «~» i no el «:» per defecte: a la ruta, el servidor de proves en viu de Windows llegeix
    # «X:» com una unitat de disc (T-M01-22). La caducitat va dins del contingut signat.
    return signing.Signer(salt=_LOCAL_SALT, sep="~")


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
    extension = Path(uploaded.name or "").suffix.lower()
    if detected is None and _looks_like_text(head):
        if head.removeprefix(b"\xef\xbb\xbf").lstrip().startswith(b"<"):
            detected = "application/xml"
        else:
            detected = "text/plain" if extension in _EXTENSIONS["text/plain"] else "text/csv"

    if detected not in allowed or extension not in _EXTENSIONS[detected]:
        raise ValidationError(gettext("Aquest tipus de fitxer no és permès."), code="type")
    return detected


def store(
    content: bytes, *, owner, kind: str, content_type: str, download_name: str
) -> PrivateFile:
    """Desa un fitxer (generat per la plataforma o ja validat amb `validate_upload`) i el
    registra. Els tipus d'`ENCRYPTED_KINDS` es xifren abans d'arribar a l'emmagatzematge."""
    key = uuid.uuid4().hex
    expires_at = None
    if kind == PrivateFile.Kind.GDPR_EXPORT:
        expires_at = timezone.now() + datetime.timedelta(days=settings.GDPR_EXPORT_RETENTION_DAYS)
    storage = storages["private"]
    stored = crypto.encrypt_bytes(content) if kind in ENCRYPTED_KINDS else content
    saved = storage.save(key, ContentFile(stored))
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
        return account.person_id == file.owner_id and file.kind not in _ADMIN_ONLY_KINDS
    return has_perm(account, _KIND_PERMISSION[file.kind], file.owner)


def signed_url(account, file: PrivateFile, *, request=None) -> str:
    """URL signada de curta durada, només si el compte hi té accés; si no, «no trobat».

    El registre d'activitat guarda qui l'ha demanada i de quin fitxer; mai la URL (RN-52).
    Els fitxers xifrats no en tenen mai: es llegeixen amb `open_decrypted`.
    """
    if file.kind in ENCRYPTED_KINDS:
        raise ValueError("Un fitxer xifrat no té URL signada: open_decrypted (T-M09-25a).")
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


def open_decrypted(account, file: PrivateFile, *, request=None) -> bytes:
    """Contingut desxifrat d'un fitxer d'`ENCRYPTED_KINDS`, només si el compte hi té accés (si
    no, «no trobat» i no es desxifra res). Cada obertura queda al registre d'activitat (051;
    RN-M02-48)."""
    if file.kind not in ENCRYPTED_KINDS:
        raise ValueError("Només per a fitxers xifrats; els altres, signed_url.")
    if not can_access(account, file):
        raise Http404
    audit.record(
        audit.Action.FILE_OPENED,
        actor=account,
        target=file,
        details={"kind": file.kind},
        request=request,
    )
    with storages["private"].open(file.storage_key, "rb") as handle:
        return crypto.decrypt_bytes(handle.read())


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


# Tipus de fitxer sense obligació legal de conservació (RN-B8). Les fotos de titulacions
# s'esborren al moment en un esborrat RGPD (RN-M02-54).
ERASABLE_KINDS = frozenset({PrivateFile.Kind.GDPR_EXPORT, PrivateFile.Kind.CERTIFICATION_PHOTO})


def expire_owner_files(owner, *, kinds=ERASABLE_KINDS) -> int:
    """Deixa caducats ara mateix els fitxers vius de la persona (RN-B8; i l'exportació anterior
    quan se'n demana una de nova): des d'aquest moment ningú no els pot obrir (`can_access`).
    El contingut s'esborra en confirmar-se la transacció; si aquell esborrat falla, el torna a
    provar la tasca diària (`purge_expired`). Així, si la transacció es desfà, no es perd cap
    fitxer. Torna quants n'ha caducat."""
    count = PrivateFile.objects.filter(owner=owner, kind__in=kinds, deleted_at__isnull=True).update(
        expires_at=timezone.now()
    )
    if count:
        transaction.on_commit(purge_expired, robust=True)
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
        token = _local_signer().sign_object({"k": name, "e": int(time.time()) + ttl})
        return reverse("core:local_private_file", args=[token])


def open_local(token: str) -> tuple[PrivateFile, object]:
    """Obre el fitxer d'un enllaç local signat, o aixeca `LinkRejected`."""
    try:
        payload = _local_signer().unsign_object(token)
    except signing.BadSignature:
        raise LinkRejected from None
    if not isinstance(payload, dict) or payload.get("e", 0) < time.time():
        raise LinkRejected
    file = PrivateFile.objects.filter(storage_key=payload.get("k"), deleted_at__isnull=True).first()
    if file is None:
        raise LinkRejected
    return file, storages["private"].open(file.storage_key, "rb")
