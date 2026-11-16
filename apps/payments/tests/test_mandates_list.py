"""«Mètodes i mandats» per al tresorer (T-M05a-14; C6 de M05a-3; A4 i A9 de M05a-4; RN-M05a-06;
P-121, P-193). Proves de permisos per rol i per abast. Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.core.models import Role, RolePermission
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.members.models import Member
from apps.members.tests.test_cards import make_member
from apps.payments import admin_views, crypto
from apps.payments.tests import test_mandates
from apps.payments.tests.test_preferences import card, prefer
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
URL = reverse("administration:payments_mandates")
R = Role.Code
MANAGEMENT_ROLES = [code for code in R.values if code not in ("member", "visitor", "guest")]
WITH_A4 = {R.TREASURER, R.ADMINISTRATOR}  # la Secretaria comença sense (P-193)
# Les mateixes fixtures que les proves del mandat.
member, account, text, sign = (
    test_mandates.member,
    test_mandates.account,
    test_mandates.text,
    test_mandates.sign,
)


@pytest.fixture
def members(sign, member, account):
    """Un soci de cada mena: domiciliació (Anna, el mandat de `sign`), targeta guardada, pagar
    cada vegada, sense resposta, i un de baixa que no hi surt."""
    prefer(member, account, "direct_debit", mandate=sign())
    jordi = make_member("Jordi", number=311, document="00000001R")
    prefer(jordi, account, "saved_card", saved_card=card(jordi, expiry_month=8, expiry_year=2029))
    prefer(make_member("Oriol", number=239, document="00000002W"), account, "pay_each_time")
    make_member("Laia", number=502, document="00000003A")
    make_member("Pau", number=88, document="00000004G", status=Member.Status.LEFT)


def html(client, **params):
    response = client.get(URL, params)
    assert response.status_code == 200
    return main_of(response.content.decode())


@pytest.mark.parametrize("role", MANAGEMENT_ROLES)
def test_a4_cell_of_each_role(make_admin, role):  # noqa: F811
    response = client_for(make_admin(role)).get(URL)
    assert response.status_code == (200 if role in WITH_A4 else 404)


def test_without_an_admin_session_it_asks_for_the_admin_login(client, personal_account):
    login = reverse("administration:login")
    assert client.get(URL)["Location"].startswith(login)
    personal = client_for(personal_account, area=AREA_PERSONAL).get(URL)
    assert personal.status_code == 302 and personal["Location"].startswith(login)


def test_read_only_no_method_writes(make_admin):  # noqa: F811
    assert client_for(make_admin(R.TREASURER)).post(URL).status_code == 405
    assert client_for(make_admin(R.SECRETARY)).post(URL).status_code == 404


def test_treasurer_sees_method_mandate_card_and_masked_iban_never_decrypted(
    make_admin,  # noqa: F811
    members,
    monkeypatch,
):
    def refuse(*args):
        raise AssertionError("La llista no desxifra mai l'IBAN (A9)")

    monkeypatch.setattr(crypto, "decrypt", refuse)
    page = html(client_for(make_admin(R.TREASURER)))
    assert "ES … 0001" in page and test_mandates.IBAN not in page  # P-121: «…», mai el pic
    assert "CRIS001287M01" in page and "Domiciliació" in page
    assert "… 4242 · 08/2029" in page and "Targeta guardada" in page
    assert "Pagar cada vegada" in page and "Sense resposta" in page
    assert "Laia" in page and "Pau" not in page  # només socis actius
    assert "4 de 4 socis actius" in page
    assert "Té mètode" not in page


def test_the_filter_by_method(make_admin, members):  # noqa: F811
    client = client_for(make_admin(R.ADMINISTRATOR))
    page = html(client, metode=admin_views.NO_ANSWER)
    assert "Laia" in page and "Anna" not in page and "1 de 4 socis actius" in page
    page = html(client, metode="saved_card")
    assert "Jordi" in page and "Oriol" not in page


def test_consultation_scope_only_has_method_yes_or_no(make_admin, members):  # noqa: F811
    """Si l'administrador dona a la Secretaria «Cons.» (P-193), només veu «té mètode: sí/no»:
    cap mètode, referència, targeta ni IBAN arriba a l'HTML, i no hi ha filtre."""
    RolePermission.objects.create(
        role=Role.objects.get(code=R.SECRETARY), permission_code=admin_views.VIEW, scope="read"
    )
    page = html(client_for(make_admin(R.SECRETARY)), metode="saved_card")
    assert "Té mètode" in page and page.count(">Sí<") == 3 and page.count(">No<") == 1
    for hidden in ("CRIS001287M01", "ES …", "4242", "Domiciliació", "Targeta", "Filtra", "IBAN"):
        assert hidden not in page
