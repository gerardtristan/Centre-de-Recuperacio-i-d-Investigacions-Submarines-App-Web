# ruff: noqa: F811 (fixtures importades com a paràmetres)
"""Pantalles de les homologacions, T-M02-44b (AC25 i AC26; RN-M02-50, 51 i 53; CA-M02-53 i 54).
Només dades inventades."""

import datetime

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities import filings
from apps.activities.models import CertificationFiling, DiverCertification
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import a_member
from .test_filings import levels, padi_cert, secretary  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db
R = Role.Code
F = CertificationFiling
LIST = reverse("administration:filings")
REQUEST = reverse("administration:filing_request")


def detail(filing, action=""):
    names = {"": "filing_detail", "filed": "filing_filed", "done": "filing_done",
             "reject": "filing_reject"}  # fmt: skip
    return reverse(f"administration:{names[action]}", args=[filing.pk])


@pytest.fixture
def client_of(login_as):
    return lambda account: login_as(account, AREA_ADMIN)


@pytest.fixture
def requested(levels, secretary):  # noqa: F811
    cert = padi_cert(a_member("Laia").person, levels[0])
    return filings.request_homologation(cert, by=secretary)


@pytest.mark.parametrize("role", [R.INSTRUCTOR, R.COURSES_MANAGER, R.TREASURER, R.BOARD])
def test_without_ac26_every_screen_is_not_found(client_of, make_admin, requested, role):  # noqa: F811
    client = client_of(make_admin(role))
    for url in (LIST, detail(requested), REQUEST):
        assert client.get(url).status_code == 404, url
    assert client.post(reverse("administration:filings_csv")).status_code == 404
    assert client.post(detail(requested, "filed")).status_code == 404


def test_the_secretary_requests_on_behalf_and_sees_the_pending_list(
    client_of,
    secretary,
    levels,  # noqa: F811
):
    person = a_member("Pau").person
    cert = padi_cert(person, levels[0])
    padi_cert(person, levels[1])  # de l'agència de destinació: no s'hi pot demanar
    client = client_of(secretary)
    html = main_of(client.get(REQUEST).content.decode())
    assert html.count("Prova, Pau") == 1
    response = client.post(REQUEST, {"certification": cert.pk}, follow=True)
    assert "Homologació demanada: ja surt a les pendents." in response.content.decode()
    html = main_of(client.get(LIST).content.decode())
    assert "Prova, Pau" in html and "PADI-0001" in html and "1 homologació oberta" in html
    # Ja té una d'oberta: ja no surt per triar-la.
    assert "Prova, Pau" not in main_of(client.get(REQUEST).content.decode())


def test_ca_m02_53_filed_then_done_creates_the_new_certification(
    client_of,
    secretary,
    requested,
    levels,  # noqa: F811
):
    client = client_of(secretary)
    client.post(detail(requested, "filed"))
    requested.refresh_from_db()
    assert requested.status == F.Status.FILED
    html = main_of(client.get(detail(requested)).content.decode())
    assert "Marca tramitada" not in html and "Marca feta" in html
    data = {"target_level": levels[1].pk, "number": "FED-123", "issued_on": "2027-03-01"}
    response = client.post(detail(requested, "done"), data, follow=True)
    assert "la titulació nova ja és a la fitxa" in response.content.decode()
    requested.refresh_from_db()
    assert requested.status == F.Status.DONE
    assert DiverCertification.objects.get(number="FED-123").source == "federation"


def test_done_without_data_returns_the_form_with_errata(client_of, secretary, requested):  # noqa: F811
    response = client_of(secretary).post(detail(requested, "done"), {"number": ""})
    assert response.status_code == 200
    html = main_of(response.content.decode())
    assert "Hi ha 3 errors" in html


def test_ca_m02_54_reject_needs_a_reason(client_of, secretary, requested):  # noqa: F811
    client = client_of(secretary)
    response = client.post(detail(requested, "reject"), {"reason": " "})
    assert response.status_code == 200 and "Hi ha 1 error" in response.content.decode()
    requested.refresh_from_db()
    assert requested.status == F.Status.REQUESTED
    response = client.post(
        detail(requested, "reject"), {"reason": "Carnet il·legible"}, follow=True
    )
    assert "rebutjada amb el motiu" in response.content.decode()
    requested.refresh_from_db()
    assert (requested.status, requested.reason) == (F.Status.REJECTED, "Carnet il·legible")


def test_rn_m02_53_the_csv_downloads_and_leaves_a_trace(client_of, secretary, requested):  # noqa: F811
    response = client_of(secretary).post(reverse("administration:filings_csv"))
    assert response["Content-Type"].startswith("text/csv")
    assert f"homologacions-{datetime.date.today():%Y-%m-%d}.csv" in response["Content-Disposition"]
    content = response.content.decode()
    assert content.splitlines()[0].startswith("cognoms;nom;data_de_naixement")
    assert "Prova;Laia" in content
    assert AuditEntry.objects.filter(action=filings.EXPORTED).count() == 1
    assert client_of(secretary).get(reverse("administration:filings_csv")).status_code == 405
