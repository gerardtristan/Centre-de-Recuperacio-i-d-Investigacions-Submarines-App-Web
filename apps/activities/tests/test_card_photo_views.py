# ruff: noqa: F811 (fixtures importades com a paràmetres)
"""Pantalles de pujada de la foto del carnet, T-M02-42b (RN-M02-47 i 56; CA-M02-52): el titular a
l'àrea personal i la secretaria (AC25) a l'administració, només amb VC-56 encès. Dades
inventades."""

import html

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.activities import card_photos, filings
from apps.activities.models import CertificationCardPhoto
from apps.core.models import PrivateFile, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_member
from .test_card_photos import JPEG, cert, holder, photos_on  # noqa: F401 (fixtures)
from .test_filings import levels, padi_cert, secretary  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
MINE = reverse("activities:my_certifications")


def mine(cert):
    return reverse("activities:my_certification_photo", args=[cert.pk])


def admin(cert):
    return reverse("administration:certification_photo", args=[cert.pk])


def text(response):
    return html.unescape(response.content.decode())


def jpeg():
    return SimpleUploadedFile("carnet.jpg", JPEG)


def test_ca_m02_52_with_photos_off_there_is_no_upload_anywhere(login_as, cert, holder, secretary):
    personal = login_as(holder, AREA_PERSONAL)
    assert personal.get(mine(cert)).status_code == 404
    assert "Foto del carnet" not in text(personal.get(MINE))
    staff = login_as(secretary, AREA_ADMIN)
    assert staff.get(admin(cert)).status_code == 404
    filing = filings.request_homologation(cert, by=secretary)
    detail = staff.get(reverse("administration:filing_detail", args=[filing.pk]))
    assert "Puja la foto del carnet" not in text(detail)


def test_the_holder_uploads_from_their_certifications(login_as, photos_on, cert, holder):
    client = login_as(holder, AREA_PERSONAL)
    assert mine(cert) in text(client.get(MINE))
    page = text(client.get(mine(cert)))
    assert "document de salut" in page and "3 mesos" in page  # avís de RN-M02-47 i VC-57

    response = client.post(mine(cert), {"side": "front", "photo": jpeg()})
    assert (response.status_code, response["Location"]) == (303, MINE)
    assert CertificationCardPhoto.objects.get().uploaded_by == holder
    assert "Foto desada" in text(client.get(MINE))
    assert "Anvers" in text(client.get(mine(cert)))


def test_a_bad_file_returns_the_form_with_errata(login_as, photos_on, cert, holder):
    client = login_as(holder, AREA_PERSONAL)
    response = client.post(
        mine(cert), {"side": "front", "photo": SimpleUploadedFile("c.jpg", b"MZ")}
    )
    assert response.status_code == 200 and "no és permès" in text(response)
    assert not PrivateFile.objects.exists()


def test_another_persons_certification_or_an_admin_session_is_not_found(
    login_as, photos_on, cert, secretary
):
    assert login_as(a_member("Pau"), AREA_PERSONAL).get(mine(cert)).status_code == 404
    assert login_as(secretary, AREA_ADMIN).get(mine(cert)).status_code in (302, 401, 404)


def test_the_secretary_uploads_on_behalf_from_the_homologation(
    login_as, photos_on, cert, secretary, make_admin
):
    card_photos.upload(cert, "front", jpeg(), by=secretary)  # amb VC-56 encès, cal l'anvers
    filing = filings.request_homologation(cert, by=secretary)
    staff = login_as(secretary, AREA_ADMIN)
    detail = text(staff.get(reverse("administration:filing_detail", args=[filing.pk])))
    assert admin(cert) in detail

    response = staff.post(admin(cert), {"side": "back", "photo": jpeg()})
    assert (response.status_code, response["Location"]) == (303, admin(cert))
    assert CertificationCardPhoto.objects.get(side="back").uploaded_by == secretary
    for role in (Role.Code.COURSES_MANAGER, Role.Code.BOARD):  # sense AC25
        assert login_as(make_admin(role), AREA_ADMIN).get(admin(cert)).status_code == 404
