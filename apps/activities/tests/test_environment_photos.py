"""Fotos d'una sortida de medi ambient (T-M02-20; CA-M02-22; RN-M02-23; M02-12; P-41 oberta:
interruptor apagat). Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404

from apps.activities import environment, environment_photos
from apps.activities.models import EnvironmentalPhoto
from apps.core import files
from apps.core.models import AuditEntry, PrivateFile, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .test_card_photos import GPS, JPEG
from .test_environment import env_outing, manager  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db


@pytest.fixture
def switch_on():
    Setting.objects.filter(key=environment_photos.SWITCH).update(initial_value=True)


@pytest.fixture
def outing(manager):  # noqa: F811
    activity = env_outing(manager)
    environment.record_results(activity, by=manager, waste_grams=1000)
    return activity


def jpeg():
    return SimpleUploadedFile("foto.jpg", JPEG)


def upload(outing, by, **extra):
    data = {"author": "Autora Inventada", "usage_permission": True, **extra}
    return environment_photos.upload(outing, jpeg(), by=by, **data)


def test_switched_off_by_default_nothing_is_uploaded_or_opened(outing, manager):  # noqa: F811
    assert Setting.objects.get(key=environment_photos.SWITCH).initial_value is False
    with pytest.raises(ValidationError):
        upload(outing, manager)
    assert not EnvironmentalPhoto.objects.exists()


def test_a_photo_is_stored_encrypted_without_metadata_and_recorded(outing, manager, switch_on):  # noqa: F811
    photo = upload(outing, manager)
    assert photo.file.kind == PrivateFile.Kind.ENVIRONMENT_PHOTO
    assert photo.file.kind in files.ENCRYPTED_KINDS
    content = files.open_decrypted(manager, photo.file)
    assert GPS not in content and b"comentari" not in content
    with pytest.raises(ValueError):  # mai cap adreça signada
        files.signed_url(manager, photo.file)
    assert AuditEntry.objects.filter(action=environment_photos.UPLOADED).exists()
    assert list(environment_photos.photos_for(outing)) == [photo]


@pytest.mark.parametrize("missing", [{"author": " "}, {"usage_permission": False}])
def test_the_author_and_the_usage_permission_are_required(outing, manager, switch_on, missing):  # noqa: F811
    with pytest.raises(ValidationError):
        upload(outing, manager, **missing)
    assert not EnvironmentalPhoto.objects.exists()


def test_ca_m02_22_people_without_consent_are_never_publishable(outing, manager, switch_on):  # noqa: F811
    photo = upload(outing, manager, shows_people=True, people_consent=False)
    with pytest.raises(ValidationError):
        environment_photos.mark_publishable(photo, by=manager)
    photo.refresh_from_db()
    assert photo.publishable is False
    ok = upload(outing, manager, shows_people=True, people_consent=True)
    assert environment_photos.mark_publishable(ok, by=manager).publishable is True


def test_only_ac14_uploads_and_the_board_only_looks(outing, manager, switch_on, make_admin):  # noqa: F811
    board = make_admin("board")
    with pytest.raises(Http404):
        upload(outing, board)
    photo = upload(outing, manager)
    assert files.can_access(board, photo.file)  # AC14 «Cons.»
    with pytest.raises(Http404):
        environment_photos.retire(photo, by=board, reason="x")
    assert not files.can_access(make_admin("treasurer"), photo.file)
    assert not files.can_access(manager.person.accounts.filter(kind="personal").first(), photo.file)


def test_retiring_keeps_the_row_and_the_file_but_nobody_opens_it(outing, manager, switch_on):  # noqa: F811
    photo = upload(outing, manager)
    with pytest.raises(ValidationError):
        environment_photos.retire(photo, by=manager, reason=" ")
    environment_photos.retire(photo, by=manager, reason="Foto equivocada")
    photo.refresh_from_db()
    assert photo.status == "retired" and photo.file.deleted_at is None
    assert not files.can_access(manager, photo.file)
    assert not environment_photos.photos_for(outing).exists()
    entry = AuditEntry.objects.get(action=environment_photos.RETIRED)
    assert (entry.old_value, entry.new_value, entry.reason) == (
        "active",
        "retired",
        "Foto equivocada",
    )


def test_switching_off_again_closes_the_photos(outing, manager, switch_on):  # noqa: F811
    photo = upload(outing, manager)
    Setting.objects.filter(key=environment_photos.SWITCH).update(initial_value=False)
    assert not files.can_access(manager, photo.file)
