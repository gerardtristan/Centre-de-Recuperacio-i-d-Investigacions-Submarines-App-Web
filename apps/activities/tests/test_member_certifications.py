# ruff: noqa: F811 (fixtures importades com a paràmetres)
"""«Les meves titulacions» a l'àrea personal, T-M02-44c (RN-M02-50): el titular demana
l'homologació d'una titulació seva d'una altra agència. Només dades inventades."""

import html

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.activities.models import CertificationFiling, DiverCertification
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_member
from .test_filings import levels, padi_cert, setting  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db
URL = reverse("activities:my_certifications")
F = CertificationFiling


def cert(person, level, number):
    return DiverCertification.objects.create(
        person=person, level=level, agency=level.agency, number=number, source="declared"
    )


def page(client):
    return html.unescape(client.get(URL).content.decode())


def test_the_holder_sees_only_their_certifications_and_requests_one(login_as, levels):
    account = a_member("Laia")
    padi = padi_cert(account.person, levels[0])
    cert(account.person, levels[1], "FED-9")  # de la destinació: sense botó
    cert(a_member("Pau").person, levels[0], "ALTRA-1")  # d'una altra persona
    client = login_as(account, AREA_PERSONAL)
    text = page(client)
    assert "2 titulacions" in text and "ALTRA-1" not in text
    assert text.count("Demana l'homologació<") == 1
    response = client.post(URL, {"titulacio": padi.pk})
    assert response.status_code == 303
    filing = F.objects.get()
    assert (filing.person, filing.source_certification, filing.requested_by) == (
        account.person,
        padi,
        account,
    )
    text = page(client)
    assert "Homologació demanada." in text and "Demanada" in text
    assert "Demana l'homologació<" not in text  # ja n'hi ha una d'oberta


def test_a_certification_of_another_person_is_not_found(login_as, levels):
    other = padi_cert(a_member("Pau").person, levels[0])
    client = login_as(a_member("Laia"), AREA_PERSONAL)
    assert client.post(URL, {"titulacio": other.pk}).status_code == 404
    assert client.post(URL, {"titulacio": "x"}).status_code == 404
    assert not F.objects.exists()


def test_with_photos_required_the_request_is_refused_with_a_message(login_as, levels, make_admin):
    account = a_member("Laia")
    padi = padi_cert(account.person, levels[0])
    setting("activities.card_photos_enabled", True, make_admin(Role.Code.ADMINISTRATOR))
    client = login_as(account, AREA_PERSONAL)
    client.post(URL, {"titulacio": padi.pk})
    assert not F.objects.exists()
    assert "Cal la foto de l'anvers" in page(client)


def test_an_admin_account_does_not_reach_the_personal_page(login_as, make_admin):
    assert login_as(make_admin(Role.Code.SECRETARY), AREA_ADMIN).get(URL).status_code in (302, 404)


def test_without_a_session_it_asks_to_log_in(client):
    assert client.get(URL).status_code == 302
