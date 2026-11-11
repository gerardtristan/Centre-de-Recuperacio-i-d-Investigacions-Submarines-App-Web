"""Fitxers privats (spec 00, annex B; V-08; checklist C10; T-M01-10). Només dades inventades."""

import datetime
import importlib
import re
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from storages.backends.s3 import S3Storage

from apps.accounts.models import Account
from apps.core import files
from apps.core.audit import Action
from apps.core.models import AuditEntry, PrivateFile, Role
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

PDF = b"%PDF-1.7\n%inventat\n"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 16
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 8
HEIC = b"\x00\x00\x00\x18ftypheic" + b"\x00" * 8
GIF = b"GIF89a" + b"\x00" * 16


def _upload(name, content):
    return SimpleUploadedFile(name, content)


def _export(owner, content=b'{"nom": "Anna"}'):
    return files.store(
        content,
        owner=owner,
        kind=PrivateFile.Kind.GDPR_EXPORT,
        content_type="application/json",
        download_name="exportacio.json",
    )


@pytest.fixture
def other_member(make_person):
    account = Account.objects.create_personal(
        make_person("Marc", "Soler"), "marc@example.org", PASSWORD
    )
    account.status = Account.Status.ACTIVE
    account.save()
    return account


# --- Tipus i mida (C10, CA-B1, CA-B2) -------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "content", "expected"),
    [
        ("factura.pdf", PDF, "application/pdf"),
        ("foto.jpg", JPEG, "image/jpeg"),
        ("foto.JPEG", JPEG, "image/jpeg"),
        ("foto.png", PNG, "image/png"),
        ("foto.webp", WEBP, "image/webp"),
        ("foto.heic", HEIC, "image/heic"),
    ],
)
def test_allowed_types_are_recognised_by_content(name, content, expected):
    assert files.validate_upload(_upload(name, content)) == expected


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("animacio.gif", GIF),  # tipus no permès
        ("factura.pdf", PNG),  # extensió permesa, contingut d'un altre tipus (CA-B2)
        ("foto.png", PDF),
        ("programa.pdf", b"MZ\x90\x00executable"),
        ("factura", PDF),  # sense extensió
        ("socis.csv", b"num;nom\n1;Anna\n"),  # el CSV només a les importacions
    ],
)
def test_disallowed_or_disguised_files_are_rejected(name, content):
    with pytest.raises(ValidationError) as error:
        files.validate_upload(_upload(name, content))
    assert error.value.code == "type"
    assert error.value.messages == ["Aquest tipus de fitxer no és permès."]


def test_csv_is_accepted_only_for_imports():
    upload = _upload("socis.csv", "número;nom\n1;Anna\n".encode())
    assert files.validate_upload(upload, allowed=files.IMPORT_TYPES) == "text/csv"
    with pytest.raises(ValidationError):
        files.validate_upload(_upload("socis.csv", b"\x00\x01binari"), allowed=files.IMPORT_TYPES)


def test_default_size_limit_is_ten_megabytes(settings):
    assert settings.UPLOAD_MAX_BYTES == 10 * 1024 * 1024
    too_big = _upload("factura.pdf", PDF + b"0" * (10 * 1024 * 1024))
    with pytest.raises(ValidationError) as error:
        files.validate_upload(too_big)
    assert error.value.code == "too_large"
    assert error.value.messages == ["El fitxer supera la mida màxima de 10 MB."]


@override_settings(UPLOAD_MAX_BYTES=2 * 1024 * 1024)
def test_size_limit_is_configurable():
    files.validate_upload(_upload("factura.pdf", PDF + b"0" * (1024 * 1024)))
    with pytest.raises(ValidationError, match="2 MB"):
        files.validate_upload(_upload("factura.pdf", PDF + b"0" * (2 * 1024 * 1024)))


def test_empty_file_is_rejected():
    with pytest.raises(ValidationError) as error:
        files.validate_upload(_upload("factura.pdf", b""))
    assert error.value.code == "empty"


# --- Desar ----------------------------------------------------------------------------------


def test_stored_file_has_an_unpredictable_name(personal_account):
    first = _export(personal_account.person)
    second = _export(personal_account.person)

    assert first.storage_key != second.storage_key
    # Només 32 xifres hexadecimals aleatòries: cap nom, cap tipus, cap dada personal.
    assert re.fullmatch(r"[0-9a-f]{32}", first.storage_key)
    with storages["private"].open(first.storage_key) as handle:
        assert handle.read() == b'{"nom": "Anna"}'
    assert first.size_bytes == len(b'{"nom": "Anna"}')


def test_gdpr_export_expires_after_seven_days(personal_account):
    before = timezone.now()
    file = _export(personal_account.person)
    expected = before + datetime.timedelta(days=7)
    assert abs((file.expires_at - expected).total_seconds()) < 5


# --- Permís (rol i objecte, CA-B3, CA-B4) ---------------------------------------------------


def test_owner_gets_a_signed_url(personal_account):
    file = _export(personal_account.person)
    assert files.signed_url(personal_account, file).startswith("/fitxers/local/")


def test_another_member_cannot_get_the_file(personal_account, other_member):
    file = _export(personal_account.person)
    assert not files.can_access(other_member, file)
    with pytest.raises(Http404):
        files.signed_url(other_member, file)


def test_admin_without_the_permission_cannot_get_the_file(personal_account, make_admin):
    file = _export(personal_account.person)
    with pytest.raises(Http404):
        files.signed_url(make_admin(Role.Code.TREASURER), file)


def test_admin_with_the_gdpr_permission_gets_the_file(personal_account, make_admin):
    file = _export(personal_account.person)
    assert files.can_access(make_admin(Role.Code.ADMINISTRATOR), file)


def test_admin_account_of_the_owner_needs_the_permission_too(personal_account, make_admin):
    """El titular només hi entra amb el seu compte personal; l'altre compte, amb permís."""
    file = _export(personal_account.person)
    own_admin = make_admin(Role.Code.TREASURER, person=personal_account.person)
    assert not files.can_access(own_admin, file)


def test_inactive_account_cannot_get_the_file(personal_account):
    file = _export(personal_account.person)
    personal_account.status = Account.Status.DISABLED
    personal_account.save()
    assert not files.can_access(personal_account, file)


def test_expired_or_deleted_file_cannot_be_requested(personal_account):
    expired = _export(personal_account.person)
    expired.expires_at = timezone.now() - datetime.timedelta(seconds=1)
    expired.save()
    deleted = _export(personal_account.person)
    deleted.deleted_at = timezone.now()
    deleted.save()

    assert not files.can_access(personal_account, expired)
    assert not files.can_access(personal_account, deleted)


def test_anonymous_cannot_get_the_file(personal_account):
    from django.contrib.auth.models import AnonymousUser

    assert not files.can_access(AnonymousUser(), _export(personal_account.person))


def test_issuing_a_url_is_audited_without_the_url(personal_account):
    file = _export(personal_account.person)
    url = files.signed_url(personal_account, file)

    entry = AuditEntry.objects.get(action=Action.FILE_URL_ISSUED)
    assert entry.actor_account == personal_account
    assert (entry.target_type, entry.target_id) == ("core.privatefile", str(file.pk))
    token = url.rstrip("/").rsplit("/", 1)[-1]
    assert token not in str(entry.details) + str(entry.new_value) + str(entry.old_value)


# --- Vistes i URL signada local -------------------------------------------------------------


def test_owner_downloads_through_the_signed_url(login_as, personal_account):
    file = _export(personal_account.person)
    client = login_as(personal_account, "personal")

    response = client.get(reverse("core:private_file", args=[file.pk]))
    assert response.status_code == 302
    assert response["Cache-Control"] == "no-store"

    download = client.get(response["Location"])
    assert download.status_code == 200
    assert b"".join(download.streaming_content) == b'{"nom": "Anna"}'
    assert download["Content-Disposition"] == 'attachment; filename="exportacio.json"'
    assert download["Cache-Control"] == "no-store"


def test_other_member_gets_not_found(login_as, personal_account, other_member):
    file = _export(personal_account.person)
    client = login_as(other_member, "personal")
    assert client.get(reverse("core:private_file", args=[file.pk])).status_code == 404


def test_unknown_file_gets_not_found(login_as, personal_account):
    import uuid

    client = login_as(personal_account, "personal")
    assert client.get(reverse("core:private_file", args=[uuid.uuid4()])).status_code == 404


def test_file_view_requires_a_session(client, personal_account):
    file = _export(personal_account.person)
    response = client.get(reverse("core:private_file", args=[file.pk]))
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))


@pytest.mark.parametrize(
    ("offset", "status"),
    [(0, 200), (299, 200), (300, 200), (300.001, 403), (301, 403)],
)
def test_expired_signed_url_is_rejected(
    client, personal_account, monkeypatch, settings, offset, status
):
    """CA-B5: passats els 5 minuts, l'emmagatzematge rebutja l'enllaç.

    El rellotge del mòdul (el que fan servir l'emissió i la comprovació) es fixa abans d'emetre
    l'URL, en un instant enter, i totes les comprovacions en deriven. Abans es prenia l'instant base
    després del primer GET, amb el rellotge real: fallava de manera intermitent (CI #102).
    """
    issued = 1_000_000.0
    clock = [issued]
    monkeypatch.setattr(files, "time", SimpleNamespace(time=lambda: clock[0]))
    assert settings.PRIVATE_FILES_SIGNED_URL_TTL == 300
    url = files.signed_url(personal_account, _export(personal_account.person))
    clock[0] = issued + offset
    assert client.get(url).status_code == status


def test_tampered_signed_url_is_rejected(client, personal_account):
    file = _export(personal_account.person)
    url = files.signed_url(personal_account, file)
    assert client.get(url[:-3] + "xx/").status_code == 403
    assert client.get(reverse("core:local_private_file", args=["inventat"])).status_code == 403


def test_local_signed_url_has_no_colon(personal_account):
    """T-M01-22 (trobat amb l'e2e de l'exportació RGPD): el separador «:» de `django.core.signing`
    a la ruta fa fallar el servidor de proves en viu a Windows, que llegeix «X:» com una unitat
    de disc (`url2pathname`) i respon 500 en lloc de servir el fitxer. L'enllaç local no en porta
    cap."""
    url = files.signed_url(personal_account, _export(personal_account.person))
    assert ":" not in url


def test_signed_url_of_a_purged_file_is_rejected(client, personal_account):
    file = _export(personal_account.person)
    url = files.signed_url(personal_account, file)
    file.deleted_at = timezone.now()
    file.save()
    assert client.get(url).status_code == 403


@override_settings(PRIVATE_FILES_LOCAL_ALLOWED=False)
def test_local_storage_is_refused_where_not_allowed(tmp_path):
    with pytest.raises(ImproperlyConfigured):
        files.LocalSignedStorage(location=tmp_path)


# --- Scaleway (API S3) ----------------------------------------------------------------------


def test_s3_signed_url_lasts_five_minutes():
    """La URL de Scaleway es firma al servidor, sense xarxa; caduca als 300 segons."""
    storage = S3Storage(
        bucket_name="cris-proves",
        endpoint_url="https://s3.fr-par.scw.cloud",
        region_name="fr-par",
        access_key="proves",
        secret_key=PASSWORD,
        querystring_auth=True,
        signature_version="s3v4",
    )
    url = storage.url("0123456789abcdef", expire=300)
    query = parse_qs(urlparse(url).query)

    assert urlparse(url).hostname.endswith("s3.fr-par.scw.cloud")
    assert query["X-Amz-Expires"] == ["300"]
    assert "X-Amz-Signature" in query


def test_production_uses_a_private_scaleway_bucket(monkeypatch):
    for name, value in {
        "DJANGO_SECRET_KEY": "nomes-per-a-proves",
        "EMAIL_HOST": "smtp.example.invalid",
        "EMAIL_HOST_USER": "proves",
        "EMAIL_HOST_PASSWORD": PASSWORD,
        "S3_BUCKET_FITXERS": "cris-produccio",
        "S3_ENDPOINT_URL": "https://s3.fr-par.scw.cloud",
        "S3_ACCESS_KEY_ID": "proves",
        "S3_SECRET_ACCESS_KEY": PASSWORD,
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delitem(sys.modules, "config.settings.prod", raising=False)
    prod = importlib.import_module("config.settings.prod")
    monkeypatch.delitem(sys.modules, "config.settings.prod")

    private = prod.STORAGES["private"]
    assert private["BACKEND"] == "storages.backends.s3.S3Storage"
    assert prod.PRIVATE_FILES_LOCAL_ALLOWED is False
    assert private["OPTIONS"]["bucket_name"] == "cris-produccio"
    assert private["OPTIONS"]["region_name"] == "fr-par"
    assert private["OPTIONS"]["default_acl"] == "private"
    assert private["OPTIONS"]["querystring_auth"] is True
    assert private["OPTIONS"]["querystring_expire"] == 300
    assert private["OPTIONS"]["file_overwrite"] is False


# --- Esborrat de les exportacions caducades (V-08) ------------------------------------------


def test_purge_deletes_expired_exports_only(personal_account):
    expired = _export(personal_account.person)
    expired.expires_at = timezone.now() - datetime.timedelta(seconds=1)
    expired.save()
    current = _export(personal_account.person)

    assert files.purge_expired() == 1

    expired.refresh_from_db()
    assert expired.deleted_at is not None
    assert not storages["private"].exists(expired.storage_key)
    assert storages["private"].exists(current.storage_key)
    entry = AuditEntry.objects.get(action=Action.FILE_DELETED)
    assert entry.actor_origin == "files.purge_expired"
    assert files.purge_expired() == 0
