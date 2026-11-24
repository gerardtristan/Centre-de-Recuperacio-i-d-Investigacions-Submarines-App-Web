"""Fotos dels carnets de titulació (T-M02-42; addenda de la 104; RN-M02-47; CA-M02-49, 50 i 52).
Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404

from apps.activities import card_photos, filings
from apps.activities.models import CertificationCardPhoto, DiverCertification
from apps.core import crypto, files
from apps.core.models import AuditEntry, PrivateFile, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_member
from .test_filings import levels, padi_cert, secretary, setting  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
GPS = b"GPS 41.3851N 2.1734E (inventat)"


def segment(marker: int, payload: bytes) -> bytes:
    return bytes([0xFF, marker]) + (len(payload) + 2).to_bytes(2, "big") + payload


JFIF = segment(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
SCAN = segment(0xDA, b"\x01\x01\x00\x00\x3f\x00") + b"\x12\x34\x56" + b"\xff\xd9"
JPEG = (
    b"\xff\xd8" + JFIF + segment(0xE1, b"Exif\x00\x00" + GPS) + segment(0xFE, b"comentari")
    + segment(0xDB, b"\x00" * 65) + SCAN
)  # fmt: skip


def chunk(kind: bytes, payload: bytes) -> bytes:
    return len(payload).to_bytes(4, "big") + kind + payload + b"\x00\x00\x00\x00"


PNG = (
    b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", b"\x00" * 13) + chunk(b"tEXt", b"Comment\x00" + GPS)
    + chunk(b"IDAT", b"\x78\x9c") + chunk(b"IEND", b"")
)  # fmt: skip


@pytest.fixture
def photos_on(make_admin):  # noqa: F811
    setting("activities.card_photos_enabled", True, make_admin(Role.Code.ADMINISTRATOR))


@pytest.fixture
def holder():
    return a_member("Laia")


@pytest.fixture
def cert(holder, levels):  # noqa: F811
    return padi_cert(holder.person, levels[0])


def upload(cert, by, name="carnet.jpg", content=JPEG, side="front"):  # noqa: F811
    return card_photos.upload(cert, side, SimpleUploadedFile(name, content), by=by)


def stored(photo):
    with storages["private"].open(photo.file.storage_key, "rb") as handle:
        return handle.read()


def test_ca_m02_49_the_photo_is_stored_encrypted_without_exif_and_audited(photos_on, cert, holder):
    photo = upload(cert, holder)

    raw = stored(photo)
    assert not raw.startswith(b"\xff\xd8") and GPS not in raw  # sense la clau no és una imatge
    content = crypto.decrypt_bytes(raw)
    assert GPS not in content and b"comentari" not in content and b"Exif" not in content
    assert content == b"\xff\xd8" + JFIF + segment(0xDB, b"\x00" * 65) + SCAN
    assert (photo.file.kind, photo.file.owner, photo.content_type) == (
        PrivateFile.Kind.CERTIFICATION_PHOTO,
        holder.person,
        "image/jpeg",
    )
    entry = AuditEntry.objects.get(action=card_photos.UPLOADED)
    assert (entry.actor_account, entry.details) == (
        holder,
        {"certification": cert.pk, "side": "front"},
    )
    # El titular l'obre amb el seu compte personal (AC24: T-M02-43 i core.files).
    assert files.open_decrypted(holder, photo.file) == content


def test_png_text_chunks_are_removed(photos_on, cert, holder):
    photo = upload(cert, holder, "carnet.png", PNG, side="back")
    content = crypto.decrypt_bytes(stored(photo))
    assert GPS not in content and b"tEXt" not in content
    assert content.startswith(b"\x89PNG") and content.endswith(chunk(b"IEND", b""))


def test_a_pdf_is_stored_as_it_is(photos_on, cert, holder):
    pdf = b"%PDF-1.7\n%carnet inventat\n"
    photo = upload(cert, holder, "carnet.pdf", pdf)
    assert crypto.decrypt_bytes(stored(photo)) == pdf


@pytest.mark.parametrize(
    ("name", "content"),
    [("carnet.jpg", b"MZ\x90\x00programa"), ("carnet.jpg", b"\xff\xd8\xff\xe0\x00")],
    ids=["executable", "jpeg-trencat"],
)
def test_ca_m02_50_a_file_that_is_not_a_photo_saves_nothing(photos_on, cert, holder, name, content):
    with pytest.raises(ValidationError):
        upload(cert, holder, name, content)
    assert not CertificationCardPhoto.objects.exists() and not PrivateFile.objects.exists()


def test_ca_m02_52_with_photos_off_the_service_refuses(cert, holder):
    with pytest.raises(ValidationError, match="no es poden pujar"):
        upload(cert, holder)
    assert not PrivateFile.objects.exists()


def test_only_the_holder_or_ac25(photos_on, cert, secretary, make_admin):  # noqa: F811
    for stranger in (a_member("Pau"), make_admin(Role.Code.COURSES_MANAGER), make_admin("board")):
        with pytest.raises(Http404):
            upload(cert, stranger)
    assert upload(cert, secretary).uploaded_by == secretary


def test_only_another_agency_and_one_photo_per_side(photos_on, cert, holder, levels):  # noqa: F811
    own = DiverCertification.objects.create(
        person=holder.person, level=levels[1], agency=levels[1].agency, source="declared"
    )
    with pytest.raises(ValidationError, match="altra agència"):
        upload(own, holder)
    upload(cert, holder)
    with pytest.raises(ValidationError, match="ja té una foto"):
        upload(cert, holder)
    assert PrivateFile.objects.count() == 1


def test_with_photos_on_the_front_photo_lets_the_holder_request_the_homologation(
    photos_on, cert, holder
):
    upload(cert, holder, side="back")
    with pytest.raises(ValidationError, match="anvers"):
        filings.request_homologation(cert, by=holder)
    upload(cert, holder)
    assert filings.request_homologation(cert, by=holder).status == "requested"
