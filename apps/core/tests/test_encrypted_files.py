"""Fitxers privats xifrats a l'aplicació (T-M09-25a; 051, RN-M09-23; 104, RN-M02-48). Clau pròpia
`FILE_ENCRYPTION_KEYS`, cap URL signada, contingut només per la vista amb permís i registre.
Només dades inventades."""

import pytest
from cryptography.fernet import Fernet, InvalidToken
from django.core.files.storage import storages
from django.http import Http404
from django.test import override_settings
from django.urls import reverse

from apps.core import crypto, files
from apps.core.audit import Action
from apps.core.models import AuditEntry, PrivateFile, Role
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db

Kind = PrivateFile.Kind
PDF = b"%PDF-1.7\n%factura inventada\n"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def _store(owner, kind=Kind.EXPENSE_INVOICE, content=PDF, content_type="application/pdf"):
    return files.store(
        content, owner=owner, kind=kind, content_type=content_type, download_name="document.pdf"
    )


@pytest.fixture
def fresh_file_keys():
    crypto._file_fernet.cache_clear()
    yield
    crypto._file_fernet.cache_clear()


# --- Clau dels fitxers --------------------------------------------------------------------------


def test_bytes_round_trip_and_ciphertext_changes():
    first, second = crypto.encrypt_bytes(PDF), crypto.encrypt_bytes(PDF)
    assert first != second and PDF not in first
    assert crypto.decrypt_bytes(first) == PDF


def test_file_key_is_not_the_field_key(settings):
    """La clau dels fitxers és pròpia: un camp xifrat no es desxifra amb la dels fitxers."""
    assert settings.FILE_ENCRYPTION_KEYS != settings.FIELD_ENCRYPTION_KEYS
    with pytest.raises(InvalidToken):
        crypto.decrypt_bytes(crypto.encrypt("secret-de-camp").encode())


def test_file_key_rotation_keeps_old_files_readable(settings, fresh_file_keys):
    old_token = crypto.encrypt_bytes(PDF)
    new_key = Fernet.generate_key().decode()
    with override_settings(FILE_ENCRYPTION_KEYS=[new_key, *settings.FILE_ENCRYPTION_KEYS]):
        crypto._file_fernet.cache_clear()
        assert crypto.decrypt_bytes(old_token) == PDF
        new_token = crypto.encrypt_bytes(PDF)
    with override_settings(FILE_ENCRYPTION_KEYS=[new_key]):
        crypto._file_fernet.cache_clear()
        assert crypto.decrypt_bytes(new_token) == PDF  # la primera xifra


def test_without_a_file_key_nothing_is_stored(personal_account, fresh_file_keys):
    with override_settings(FILE_ENCRYPTION_KEYS=[]):
        with pytest.raises(RuntimeError, match="FILE_ENCRYPTION_KEYS"):
            _store(personal_account.person)
    assert not PrivateFile.objects.exists()


# --- Desar xifrat -------------------------------------------------------------------------------


@pytest.mark.parametrize("kind", sorted(files.ENCRYPTED_KINDS))
def test_encrypted_kinds_never_reach_storage_in_clear(personal_account, kind):
    file = _store(personal_account.person, kind=kind)
    with storages["private"].open(file.storage_key, "rb") as handle:
        stored = handle.read()
    assert b"%PDF" not in stored and b"factura inventada" not in stored
    assert crypto.decrypt_bytes(stored) == PDF
    assert file.size_bytes == len(PDF)


def test_other_kinds_are_stored_as_before(personal_account):
    file = _store(personal_account.person, kind=Kind.GDPR_EXPORT, content=b"{}")
    with storages["private"].open(file.storage_key, "rb") as handle:
        assert handle.read() == b"{}"


def test_encrypted_files_never_get_a_signed_url(personal_account, make_admin):
    file = _store(personal_account.person)
    with pytest.raises(ValueError, match="URL signada"):
        files.signed_url(make_admin(Role.Code.TREASURER), file)
    assert not AuditEntry.objects.filter(action=Action.FILE_URL_ISSUED).exists()


# --- Qui l'obre (RN-M09-23; RN-M02-48) ----------------------------------------------------------


@pytest.mark.parametrize(
    "kind", [Kind.EXPENSE_INVOICE, Kind.EXPENSE_BANK_PROOF, Kind.GRANT_PACKAGE]
)
def test_justification_documents_only_for_treasurer_and_board(personal_account, make_admin, kind):
    file = _store(personal_account.person, kind=kind)
    assert files.can_access(make_admin(Role.Code.TREASURER), file)
    assert files.can_access(make_admin(Role.Code.BOARD), file)
    for code in (Role.Code.ADMINISTRATOR, Role.Code.SECRETARY):
        assert not files.can_access(make_admin(code), file)
    # Qui l'ha pujat no el torna a obrir (RN-M09-23).
    assert not files.can_access(personal_account, file)


def test_issued_invoice_and_card_photo_open_for_the_owner(personal_account, make_admin):
    invoice = _store(personal_account.person, kind=Kind.ISSUED_INVOICE)
    photo = _store(personal_account.person, kind=Kind.CERTIFICATION_PHOTO)
    assert files.can_access(personal_account, invoice)
    assert files.can_access(personal_account, photo)
    assert files.can_access(make_admin(Role.Code.TREASURER), invoice)  # MG9
    assert files.can_access(make_admin(Role.Code.SECRETARY), photo)  # AC24
    assert not files.can_access(make_admin(Role.Code.SECRETARY), invoice)


def test_card_photos_are_erased_with_the_person(personal_account):
    photo = _store(personal_account.person, kind=Kind.CERTIFICATION_PHOTO)
    invoice = _store(personal_account.person, kind=Kind.EXPENSE_INVOICE)
    assert files.expire_owner_files(personal_account.person) == 1
    assert not files.can_access(personal_account, PrivateFile.objects.get(pk=photo.pk))
    assert PrivateFile.objects.get(pk=invoice.pk).expires_at is None  # document econòmic


# --- Obrir-lo desxifrat -------------------------------------------------------------------------


def test_open_decrypted_audits_every_opening(personal_account, make_admin):
    treasurer = make_admin(Role.Code.TREASURER)
    file = _store(personal_account.person)
    assert files.open_decrypted(treasurer, file) == PDF
    assert files.open_decrypted(treasurer, file) == PDF
    entries = AuditEntry.objects.filter(action=Action.FILE_OPENED)
    assert entries.count() == 2
    entry = entries.first()
    assert entry.actor_account == treasurer
    assert (entry.target_type, entry.target_id) == ("core.privatefile", str(file.pk))
    assert entry.details == {"kind": Kind.EXPENSE_INVOICE}


def test_open_decrypted_without_access_is_not_found_and_not_audited(personal_account, make_admin):
    file = _store(personal_account.person)
    with pytest.raises(Http404):
        files.open_decrypted(make_admin(Role.Code.ADMINISTRATOR), file)
    assert not AuditEntry.objects.filter(action=Action.FILE_OPENED).exists()


def test_open_decrypted_is_only_for_encrypted_kinds(personal_account):
    file = _store(personal_account.person, kind=Kind.GDPR_EXPORT, content=b"{}")
    with pytest.raises(ValueError):
        files.open_decrypted(personal_account, file)


# --- Vista ---------------------------------------------------------------------------------------


def test_view_serves_the_document_decrypted_to_the_treasurer(personal_account, make_admin):
    file = _store(personal_account.person)
    response = admin_client(make_admin(Role.Code.TREASURER)).get(
        reverse("administration:private_file", args=[file.pk])
    )
    assert response.status_code == 200
    assert response.content == PDF
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == 'attachment; filename="document.pdf"'
    assert response["Cache-Control"] == "no-store"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert AuditEntry.objects.filter(action=Action.FILE_OPENED).count() == 1


def test_view_shows_images_inline(personal_account, login_as):
    photo = _store(
        personal_account.person,
        kind=Kind.CERTIFICATION_PHOTO,
        content=PNG,
        content_type="image/png",
    )
    response = login_as(personal_account, "personal").get(
        reverse("core:private_file", args=[photo.pk])
    )
    assert response.status_code == 200 and response.content == PNG
    assert response["Content-Disposition"].startswith("inline")


def test_view_is_not_found_for_the_uploader_and_other_roles(personal_account, make_admin, login_as):
    file = _store(personal_account.person)
    assert (
        login_as(personal_account, "personal")
        .get(reverse("core:private_file", args=[file.pk]))
        .status_code
        == 404
    )
    url = reverse("administration:private_file", args=[file.pk])
    for code in (Role.Code.ADMINISTRATOR, Role.Code.SECRETARY):
        assert admin_client(make_admin(code)).get(url).status_code == 404
    assert not AuditEntry.objects.filter(action=Action.FILE_OPENED).exists()
