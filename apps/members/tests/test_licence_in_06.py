"""Un registre de llicència que ja és al 06 (pas únic o còpia de lectura, `licence_ref`) no es
corregeix des de la fitxa del soci: el 06 en té la font (P-M06-H, pas 3; 052) i la comprovació
diària desfaria el canvi. Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import licences
from apps.members.tests.test_licences import EXPIRES, ISSUED, a_record, body
from apps.members.tests.test_member_edit import a_member
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db


@pytest.fixture
def linked():
    record = a_record(a_member())
    record.licence_ref = 4242
    record.save(update_fields=["licence_ref"])
    return record


def test_the_service_refuses_to_correct_a_row_owned_by_the_06(make_admin, linked):  # noqa: F811
    with pytest.raises(ValidationError):
        licences.correct_record(linked, by=make_admin("secretary"), licence_type="Un altre",
                                issued_on=ISSUED, expires_on=EXPIRES)  # fmt: skip
    linked.refresh_from_db()
    assert linked.licence_type == "Anual FECDAS"


def test_the_card_has_no_link_and_the_edit_page_is_not_found(make_admin, linked):  # noqa: F811
    client = admin_client(make_admin("secretary"))
    url = reverse("administration:licence_edit", args=[linked.member.pk, linked.pk])
    assert client.get(url).status_code == 404
    assert client.post(url, body(licence_type="Un altre")).status_code == 404
    detail = client.get(reverse("administration:member_detail", args=[linked.member.pk]))
    assert url not in detail.content.decode()
