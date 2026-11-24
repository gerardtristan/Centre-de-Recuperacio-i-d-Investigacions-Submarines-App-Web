# ruff: noqa: F811 (fixtures importades com a paràmetres)
"""Veure les fotos dels carnets, exportació RGPD i esborrat en anonimitzar (T-M02-43; RN-M02-48 i
54; CA-M02-51 i 57; P-552). Només dades inventades."""

import pytest
from django.core.files.storage import storages
from django.http import Http404
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.activities import card_photos, privacy
from apps.activities.models import CertificationCardPhoto
from apps.core import files
from apps.core.audit import Action
from apps.core.models import AuditEntry, PrivateFile, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_member
from .test_card_photos import JPEG, cert, holder, photos_on, upload  # noqa: F401 (fixtures)
from .test_filings import levels, padi_cert, secretary, setting  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db


@pytest.fixture
def photo(photos_on, cert, holder):
    return upload(cert, holder)


def opened():
    return AuditEntry.objects.filter(action=Action.FILE_OPENED).count()


def test_ca_m02_51_the_holder_and_ac24_see_it_and_each_opening_is_audited(
    login_as, photo, holder, secretary
):
    response = login_as(holder, AREA_PERSONAL).get(
        reverse("core:private_file", args=[photo.file_id])
    )
    assert response.status_code == 200 and response["Content-Disposition"].startswith("inline")
    staff = login_as(secretary, AREA_ADMIN)
    assert (
        staff.get(reverse("administration:private_file", args=[photo.file_id])).status_code == 200
    )
    assert opened() == 2
    # La pantalla de la foto hi enllaça.
    page = staff.get(reverse("administration:certification_photo", args=[photo.certification_id]))
    assert reverse("administration:private_file", args=[photo.file_id]) in page.content.decode()


def test_ca_m02_51_an_instructor_or_another_member_gets_not_found(login_as, photo, make_admin):
    other = login_as(a_member("Pau"), AREA_PERSONAL)
    assert other.get(reverse("core:private_file", args=[photo.file_id])).status_code == 404
    instructor = login_as(make_admin(Role.Code.INSTRUCTOR), AREA_ADMIN)
    url = reverse("administration:private_file", args=[photo.file_id])
    assert instructor.get(url).status_code == 404
    assert opened() == 0  # no es desxifra res


def test_ca_m02_57_the_export_has_the_photo_data_but_never_the_photo(photo, holder):
    data = privacy.export(holder.person)
    assert data["fotos_dels_carnets"] == [
        {"titulacio": "Open Water (inventat)", "cara": "Anvers", "pujada_el": photo.uploaded_at}
    ]
    assert str(photo.file_id) not in str(data) and "storage" not in str(data)


def test_ca_m02_57_anonymising_erases_the_photos_at_once(photo, holder, secretary):
    privacy.anonymise(holder.person, by=secretary)
    files.expire_owner_files(holder.person)  # el pas de la 00, a la mateixa transacció
    assert not CertificationCardPhoto.objects.exists()
    assert not files.can_access(holder, PrivateFile.objects.get(pk=photo.file_id))


def test_rn_m02_56_with_photos_off_not_even_the_direct_address_opens_it(
    login_as, photo, holder, secretary, make_admin
):
    setting("activities.card_photos_enabled", False, make_admin(Role.Code.ADMINISTRATOR))
    personal = login_as(holder, AREA_PERSONAL)
    assert personal.get(reverse("core:private_file", args=[photo.file_id])).status_code == 404
    staff = login_as(secretary, AREA_ADMIN)
    assert (
        staff.get(reverse("administration:private_file", args=[photo.file_id])).status_code == 404
    )
    assert opened() == 0  # no es desxifra res


def test_rn_m02_49_the_holder_deletes_it_from_the_page(
    login_as, photo, holder, django_capture_on_commit_callbacks
):
    client = login_as(holder, AREA_PERSONAL)
    url = reverse("activities:my_certification_photo", args=[photo.certification_id])
    assert client.post(url, {"esborra": "x"}).status_code == 404
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(url, {"esborra": photo.pk})
    assert response.status_code == 303
    assert not CertificationCardPhoto.objects.exists()
    file = PrivateFile.objects.get(pk=photo.file_id)
    assert file.deleted_at is not None and not storages["private"].exists(file.storage_key)
    assert AuditEntry.objects.filter(action=card_photos.DELETED, actor_account=holder).exists()
    assert AuditEntry.objects.filter(action=Action.FILE_DELETED, actor_account=holder).exists()


def test_rn_m02_49_only_the_holder_or_ac25_deletes_it(photo, secretary, make_admin):
    for stranger in (a_member("Pau"), make_admin(Role.Code.BOARD)):
        with pytest.raises(Http404):
            card_photos.delete(photo, by=stranger)
    card_photos.delete(photo, by=secretary)
    assert not CertificationCardPhoto.objects.exists()
