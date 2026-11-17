"""Llistat de pagaments i «a revisar» del tresorer (T-M05b-16; B6 de M05b-4; CA-M05b-23 per a B6;
P-137, P-247). Proves de permisos per rol i del nom del pagador. Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.core import audit, charges
from apps.core.models import Payment, Role, RolePermission
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.payments import attempts
from apps.payments.models import PaymentAttempt, ProviderEvent
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
URL = reverse("administration:payments_list")
R = Role.Code
S = PaymentAttempt.Status
MANAGEMENT_ROLES = [code for code in R.values if code not in ("member", "visitor", "guest")]
WITH_B6 = {R.TREASURER, R.ADMINISTRATOR}  # matriu inicial de la 059
SYSTEM = audit.system("proves-t-m05b-16")


def fee(person, concept="Quota 2027 (prova)", amount=9000):
    return charges.create_charge(
        person, kind="fee", amount_cents=amount, concept=concept, origin="members", by=SYSTEM
    )


def in_progress(charge, method=PaymentAttempt.Method.CARD):
    attempt = attempts.create_attempt(charge, method)
    return attempts.transition(attempt, S.IN_PROGRESS, by=SYSTEM)


@pytest.fixture
def person(make_person):
    return make_person("Núria", "Coll")


@pytest.fixture
def to_review(person):
    attempt = in_progress(fee(person))
    return attempts.transition(
        attempt, S.TO_REVIEW, by=SYSTEM, reason="L'import de la notificació no quadra (prova)"
    )


def html(client, **params):
    response = client.get(URL, params)
    assert response.status_code == 200
    return main_of(response.content.decode())


@pytest.mark.parametrize("role", MANAGEMENT_ROLES)
def test_b6_cell_of_each_role(make_admin, role):  # noqa: F811
    response = client_for(make_admin(role)).get(URL)
    assert response.status_code == (200 if role in WITH_B6 else 404)


def test_without_an_admin_session_it_asks_for_the_admin_login(client, personal_account):
    login = reverse("administration:login")
    assert client.get(URL)["Location"].startswith(login)
    personal = client_for(personal_account, area=AREA_PERSONAL).get(URL)
    assert personal.status_code == 302 and personal["Location"].startswith(login)


def test_read_only(make_admin):  # noqa: F811
    assert client_for(make_admin(R.TREASURER)).post(URL).status_code == 405
    assert client_for(make_admin(R.SECRETARY)).post(URL).status_code == 404


def test_nothing_to_review(make_admin):  # noqa: F811
    assert "No hi ha cap pagament a revisar." in html(client_for(make_admin(R.TREASURER)))


def test_an_attempt_to_review_with_its_reason_and_payer(make_admin, to_review):  # noqa: F811
    page = html(client_for(make_admin(R.TREASURER)))
    assert "1 intent de pagament a revisar" in page
    assert "L&#x27;import de la notificació no quadra (prova)" in page
    assert "Núria Coll" in page and "90,00 €" in page
    assert "No hi ha cap pagament a revisar." not in page


def test_a_notification_that_matches_no_attempt(make_admin):  # noqa: F811
    ProviderEvent.objects.create(
        provider_code="fake",
        payload_hash="0" * 64,
        event_type="PAID",
        order_id="ORD-PROVA-1",
        amount_cents=3500,
        result=ProviderEvent.Result.TO_REVIEW,
    )
    ProviderEvent.objects.create(  # la xarxa de seguretat la torna a provar: no és a revisar
        provider_code="fake", payload_hash="1" * 64, result=ProviderEvent.Result.ERROR
    )
    page = html(client_for(make_admin(R.TREASURER)))
    assert "1 notificació del proveïdor" in page
    assert "ORD-PROVA-1" in page and "35,00 €" in page


def test_p137_a_reconciled_transfer_without_receipt(make_admin, person):  # noqa: F811
    charge = fee(person, concept="Quota amb targeta a mitges (prova)")
    in_progress(charge)  # ocupa l'únic lloc: la transferència no pot obrir el seu intent
    charges.record_payment(
        charge, method=Payment.Method.TRANSFER, origin="reconciliation", by=SYSTEM
    )
    page = html(client_for(make_admin(R.TREASURER)))
    assert "1 transferència conciliada sense rebut" in page
    assert "Quota amb targeta a mitges (prova)" in page


def test_all_attempts_with_a_status_filter(make_admin, person, to_review):  # noqa: F811
    in_progress(fee(person, concept="Una altra quota (prova)"))
    client = client_for(make_admin(R.TREASURER))
    assert "2 intents" in html(client)
    filtered = html(client, estat=S.IN_PROGRESS)
    assert "1 intent, del més recent" in filtered and "Una altra quota (prova)" in filtered
    assert "Cap intent de pagament amb aquests filtres." in html(client, estat=S.PAID)


def test_p247_without_p4_no_payer_name(make_admin, to_review):  # noqa: F811
    # P4 (`members.list`) decideix el nom; B6 sol ensenya els pagaments sense qui els fa.
    RolePermission.objects.filter(
        role__code=R.ADMINISTRATOR, permission_code="members.list"
    ).delete()
    page = html(client_for(make_admin(R.ADMINISTRATOR)))
    assert "90,00 €" in page
    assert "Núria" not in page and "Coll" not in page and "Pagador" not in page
