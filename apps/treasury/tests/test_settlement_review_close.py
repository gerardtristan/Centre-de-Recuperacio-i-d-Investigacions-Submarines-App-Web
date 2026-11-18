"""Tancar una liquidació «a revisar» amb nota (T-M04-14c; P-390, resposta B; T10 amb edició).
Proves de permisos per rol, nota obligatòria, llista oberta i «Tancades», doble tancament,
registre amb l'estat anterior, esborrat RGPD i que no canvia res econòmic. Dades inventades."""

import pytest
from django.db import DatabaseError, connection, transaction
from django.http import Http404
from django.urls import reverse

from apps.core import privacy as core_privacy
from apps.core.models import AppendOnlyError, AuditEntry, Payment, Person, Role, RolePermission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.treasury import reconciliation, settlements
from apps.treasury.models import Movement, ProviderSettlement, SettlementReviewClosure
from apps.treasury.settlements import SettlementLine
from apps.treasury.tests.test_record_income import new_transit
from apps.treasury.tests.test_settlements import collected, data, record_it
from apps.treasury.tests.test_views import MANAGEMENT_ROLES, REVIEW, WITH_T1, R, client_for, page

pytestmark = pytest.mark.django_db
NOTE = "Cobrament duplicat al proveïdor, comprovat per telèfon (prova)"


def close_url(settlement):
    return reverse("administration:treasury_settlement_review_close", args=[settlement.pk])


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(R.TREASURER)


@pytest.fixture
def payer(make_person):
    return make_person("Núria", "Coll")


@pytest.fixture
def to_review(payer):
    """Una liquidació «a revisar»: l'import de REF-A no és el del cobrament."""
    new_transit()
    collected(payer, 9000, "REF-A")
    return record_it(data(SettlementLine("REF-A", 8000), external_id="LIQ-DUBTE"))


@pytest.mark.parametrize("role", MANAGEMENT_ROLES)
def test_t10_with_edit_for_each_role(make_admin, to_review, role):  # noqa: F811
    client = client_for(make_admin(role))
    expected = 200 if role in WITH_T1 else 404
    assert client.get(close_url(to_review)).status_code == expected
    response = client.post(close_url(to_review), {"note": NOTE})
    assert response.status_code == (302 if role in WITH_T1 else 404)
    assert SettlementReviewClosure.objects.exists() == (role in WITH_T1)


def test_service_refuses_without_the_permission(make_admin, to_review):  # noqa: F811
    with pytest.raises(Http404):
        settlements.close_review(to_review, note=NOTE, by=make_admin(R.SECRETARY))
    assert not SettlementReviewClosure.objects.exists()


def test_note_required(treasurer, to_review):
    with pytest.raises(ValueError):
        settlements.close_review(to_review, note="  ", by=treasurer)
    with pytest.raises(ValueError):
        settlements.close_review(to_review, note="x" * 501, by=treasurer)
    response = client_for(treasurer).post(close_url(to_review), {"note": ""})
    assert (
        response.status_code == 200 and "Cal una nota per tancar-la." in response.content.decode()
    )
    assert not SettlementReviewClosure.objects.exists()


def test_closing_leaves_the_open_list_and_changes_nothing_financial(treasurer, to_review):
    client = client_for(treasurer)
    assert close_url(to_review) in page(client, REVIEW)
    payments = list(Payment.objects.values())
    movements = Movement.objects.count()
    response = client.post(close_url(to_review), {"note": NOTE}, follow=True)
    html = response.content.decode()
    assert "Liquidació tancada. No s&#x27;ha mogut cap diner." in html
    assert close_url(to_review) not in html and "No hi ha res a revisar." in html
    assert "Tancades" in html and "LIQ-DUBTE" in html and NOTE in html
    to_review.refresh_from_db()
    assert to_review.status == ProviderSettlement.Status.TO_REVIEW  # l'estat no canvia
    assert not to_review.items.exists()
    assert Movement.objects.count() == movements
    assert list(Payment.objects.values()) == payments


def test_closing_twice_is_refused(treasurer, to_review):
    settlements.close_review(to_review, note=NOTE, by=treasurer)
    with pytest.raises(settlements.NotClosable):
        settlements.close_review(to_review, note=NOTE, by=treasurer)
    assert client_for(treasurer).get(close_url(to_review)).status_code == 404
    assert SettlementReviewClosure.objects.count() == 1


def test_only_a_settlement_to_review(treasurer, payer):
    new_transit()
    collected(payer, 9000, "REF-A")
    received = record_it(data(SettlementLine("REF-A", 9000)))
    with pytest.raises(settlements.NotClosable):
        settlements.close_review(received, note=NOTE, by=treasurer)
    assert client_for(treasurer).get(close_url(received)).status_code == 404


def test_audit_with_the_note_and_the_previous_state(treasurer, to_review):
    closure = settlements.close_review(to_review, note=NOTE, by=treasurer)
    entry = AuditEntry.objects.get(action=settlements.REVIEW_CLOSED)
    assert entry.reason == NOTE
    assert (entry.target_type, entry.target_id) == (
        "treasury.settlementreviewclosure",
        str(closure.pk),
    )
    assert entry.details == {"settlement": to_review.pk, "previous_status": "to_review"}


def test_erasure_leaves_no_note(treasurer, to_review, payer, make_admin):  # noqa: F811
    # La taula no té cap text lliure; la nota, al registre, passa a la referència del pagador.
    settlements.close_review(to_review, note=NOTE, by=treasurer)
    assert {f.name for f in SettlementReviewClosure._meta.fields} == {
        "id",
        "settlement",
        "closed_by",
        "closed_at",
    }
    assert core_privacy.blockers(payer) == []
    core_privacy.anonymise_person(payer, by=make_admin(R.ADMINISTRATOR))
    payer.refresh_from_db()
    entry = AuditEntry.objects.get(action=settlements.REVIEW_CLOSED)
    assert entry.reason == payer.anonymous_ref != NOTE


def test_t10_read_only_sees_the_list_but_not_the_note_nor_can_close(
    treasurer,
    to_review,
    make_admin,  # noqa: F811
):
    # «Cons.» a T10 (P-190, 095): veu la llista i «Tancades», sense la nota ni «Tanca».
    RolePermission.objects.create(
        role=Role.objects.get(code=R.SECRETARY), permission_code=reconciliation.REVIEW, scope="read"
    )
    reader = make_admin(R.SECRETARY)
    client = client_for(reader)
    assert close_url(to_review) not in page(client, REVIEW)
    assert client.get(close_url(to_review)).status_code == 404
    assert client.post(close_url(to_review), {"note": NOTE}).status_code == 404
    with pytest.raises(Http404):
        settlements.close_review(to_review, note=NOTE, by=reader)
    settlements.close_review(to_review, note=NOTE, by=treasurer)
    html = page(client, REVIEW)
    assert "LIQ-DUBTE" in html and NOTE not in html and "—" in html


def test_closed_by_shows_the_name_not_the_login(to_review, make_admin):  # noqa: F811
    person = Person.objects.create(first_name="Laia", last_name="Prova Inventada", origin="web")
    account = make_admin(R.TREASURER, username="tresoreria.login", person=person)
    settlements.close_review(to_review, note=NOTE, by=account)
    html = page(client_for(account), REVIEW)  # només el <main>: el menú sí que porta el login
    assert "Laia Prova Inventada" in html and "tresoreria.login" not in html


def test_settlements_screen_shows_a_closed_one_as_reviewed(treasurer, to_review):
    url = reverse("administration:treasury_settlements")
    before = page(client_for(treasurer), url)
    assert "L&#x27;import no és el del cobrament" in before and "✕" in before
    settlements.close_review(to_review, note=NOTE, by=treasurer)
    html = page(client_for(treasurer), url)
    assert "Revisada i tancada" in html and f"{REVIEW}#tancades" in html
    assert "L&#x27;import no és el del cobrament" not in html and "✕" not in html


def test_append_only(treasurer, to_review):
    closure = settlements.close_review(to_review, note=NOTE, by=treasurer)
    with pytest.raises(AppendOnlyError):
        closure.save()
    with pytest.raises(AppendOnlyError):
        closure.delete()
    for sql in ("UPDATE {} SET closed_at = now()", "DELETE FROM {}"):
        with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
            cur.execute(sql.format(SettlementReviewClosure._meta.db_table))
