"""Pantalla de la justificació d'una sol·licitud (T-M09A-10c; P-M09A-F, pas 3; CA-M09A-08, 15 i
20; AJ7 i AJ12). Els serveis són de la T-M09A-10a i 10b. Només dades i fitxers inventats."""

import datetime
import io
import zipfile

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.core.models import AuditEntry
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.grants.models import GrantCall
from apps.grants.tests.test_package_10a import PROOF, granted, linked  # noqa: F401 (fixture)
from apps.grants.tests.test_requirements import record
from apps.grants.tests.test_resolution import submitted  # noqa: F401 (fixture)
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db


def url(application):
    return reverse("administration:grant_justification", args=[application.pk])


def post(client, application, **data):
    return client.post(url(application), data, follow=True)


def test_ca_m09a_08_generate_download_and_send_version_1(granted, treasurer):  # noqa: F811
    linked(granted, treasurer, 50000, "F-1")
    linked(granted, treasurer, 6500, "F-3", docs=(PROOF,))
    client = admin_client(treasurer)
    assert "Encara no s'ha generat cap paquet." in main_of(
        client.get(url(granted)).content.decode()
    )
    html = main_of(post(client, granted, action="build").content.decode())
    assert "Paquet generat." in html and "500,00" in html and "Sense factura" in html
    package = granted.packages.get()
    response = client.get(reverse("administration:private_file", args=[package.file_id]))
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert "llistat.csv" in archive.namelist()
    html = main_of(post(client, granted, action="send", paquet=package.pk,
                        enviat="2027-09-01").content.decode())  # fmt: skip
    granted.refresh_from_db()
    assert granted.status == "justified" and "Versió 1 enviada." in html
    assert "Enviat: versió 1, el 01/09/2027" in html
    assert "cal un requeriment obert" in html and "Genera el paquet" not in html


def test_ca_m09a_20_a_new_version_with_the_open_requirement(granted, treasurer):  # noqa: F811
    linked(granted, treasurer, 50000, "F-1")
    client = admin_client(treasurer)
    post(client, granted, action="build")
    post(client, granted, action="send", paquet=granted.packages.get().pk, enviat="2027-09-01")
    requirement = record(granted, treasurer)
    post(client, granted, action="build", requeriment=requirement.pk)
    new = granted.packages.order_by("-pk").first()
    html = main_of(post(client, granted, action="send", paquet=new.pk, enviat="2027-10-10",
                        requeriment=requirement.pk).content.decode())  # fmt: skip
    assert "Versió 2 enviada." in html
    requirement.refresh_from_db()
    assert requirement.answered_on == datetime.date(2027, 10, 10)


def test_ca_m09a_15_the_page_says_when_it_carries_the_originals(granted, treasurer):  # noqa: F811
    GrantCall.objects.filter(pk=granted.call_id).update(accepts_masked_proofs="no")
    linked(granted, treasurer, 50000, "F-1", masked=False)
    html = main_of(post(admin_client(treasurer), granted, action="build").content.decode())
    assert "Originals (la convocatòria no accepta còpies)" in html


def test_errors_are_shown_and_wrong_requests_are_not_found(granted, treasurer):  # noqa: F811
    client = admin_client(treasurer)
    post(client, granted, action="build")
    package = granted.packages.get()
    html = main_of(
        post(client, granted, action="send", paquet=package.pk, enviat="").content.decode()
    )
    assert "Escriu la data d" in html  # l'apòstrof del missatge surt escapat
    post(client, granted, action="send", paquet=package.pk, enviat="2027-09-01")
    html = main_of(post(client, granted, action="send", paquet=package.pk,
                        enviat="2027-09-02").content.decode())  # fmt: skip
    assert "Aquest paquet ja s" in html
    assert client.post(url(granted), {"action": "x"}).status_code == 404
    assert client.post(url(granted), {"action": "send", "paquet": 999999}).status_code == 404
    assert client.post(url(granted), {"action": "build", "requeriment": 999999}).status_code == 404


def test_the_board_sees_it_but_cannot_generate(granted, make_admin):  # noqa: F811
    client = admin_client(make_admin("board"))  # AJ7 de consulta i AJ12
    html = main_of(client.get(url(granted)).content.decode())
    assert "Justificació de l'ajut" in html and "Genera el paquet" not in html
    assert client.post(url(granted), {"action": "build"}).status_code == 404
    assert not AuditEntry.objects.filter(action="grants.package_built").exists()


@pytest.mark.parametrize("role", ["secretary", "instructor"])
def test_without_aj7_not_found(granted, make_admin, role):  # noqa: F811
    assert admin_client(make_admin(role)).get(url(granted)).status_code == 404


def test_the_calendar_links_a_granted_application(granted, treasurer):  # noqa: F811
    GrantCall.objects.filter(pk=granted.call_id).update(
        justification_due_on=timezone.localdate() + datetime.timedelta(days=10)
    )
    html = main_of(
        admin_client(treasurer).get(reverse("administration:grants_calendar")).content.decode()
    )
    assert url(granted) in html
