"""Preus de les llicències (T-M06-02; CA-M06-03, 04, 05 i 20; RN-M06-18)."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.utils import DatabaseError

from apps.core.models import AppendOnlyError, AuditEntry, OutgoingEmail
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import prices
from apps.licences.models import LicencePrice

D = datetime.date
MEMBER, NON_MEMBER = LicencePrice.Kind.MEMBER, LicencePrice.Kind.NON_MEMBER


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    account = make_admin("treasurer")
    account.notification_email = "tresorer@example.org"
    account.save()
    return account


def add(licence_type, actor, cost=9000, surcharge=2500, start=None, end=None, **kw):
    return prices.add_price(
        licence_type,
        federation_cost_cents=cost,
        non_member_surcharge_cents=surcharge,
        valid_from=start or D(2027, 1, 1),
        valid_to=end,
        note=kw.pop("note", "Tarifa de la federació (inventada)"),
        actor=actor,
        **kw,
    )


def test_member_pays_the_federation_price_and_non_member_the_surcharge(annual, treasurer):
    # CA-M06-03 i RN-M06-05/06.
    price = add(annual, treasurer)
    assert price.amount_cents(MEMBER) == 9000
    assert price.amount_cents(NON_MEMBER) == 11500


def test_there_is_no_separate_member_price(annual, treasurer):
    # CA-M06-04: no hi ha cap camp ni cap paràmetre per a un preu de soci diferent.
    assert not [f for f in LicencePrice._meta.get_fields() if "member_price" in f.name]
    with pytest.raises(TypeError):
        add(annual, treasurer, member_price_cents=8000)


@pytest.mark.parametrize("note", ["", "   ", None])
def test_a_price_without_a_note_is_rejected(annual, treasurer, note):
    # CA-M06-05, primera part.
    with pytest.raises(ValidationError, match="nota"):
        add(annual, treasurer, note=note)
    assert not LicencePrice.objects.exists()


@pytest.mark.parametrize(
    ("cost", "surcharge"), [(0, 2500), (-1, 2500), (90.0, 2500), (True, 0), (9000, -1), (9000, 1.5)]
)
def test_amounts_are_whole_cents(annual, treasurer, cost, surcharge):
    with pytest.raises(ValidationError):
        add(annual, treasurer, cost=cost, surcharge=surcharge)


def test_a_zero_surcharge_is_allowed(annual, treasurer):
    assert add(annual, treasurer, surcharge=0).amount_cents(NON_MEMBER) == 9000


def test_a_tranche_cannot_end_before_it_starts(annual, treasurer):
    with pytest.raises(ValidationError, match="anterior"):
        add(annual, treasurer, start=D(2027, 7, 1), end=D(2027, 6, 30))


def test_tranches_and_versions_ca_m06_20(annual, treasurer, make_licence):
    add(annual, treasurer, cost=9000, start=D(2027, 1, 1), end=D(2027, 6, 30))
    july = add(annual, treasurer, cost=5000, start=D(2027, 7, 1), end=D(2027, 12, 31))
    assert prices.applicable(annual, D(2027, 9, 10)) == july
    assert prices.applicable(annual, D(2027, 6, 30)).federation_cost_cents == 9000
    # La llicència ja demanada porta la seva còpia del preu (RN-M06-08).
    licence = make_licence(starts_on=D(2027, 9, 10), price_cents=july.amount_cents(MEMBER))
    newer = add(annual, treasurer, cost=5500, start=D(2027, 7, 1), end=D(2027, 12, 31))
    assert prices.applicable(annual, D(2027, 9, 10)) == newer
    licence.refresh_from_db()
    assert licence.price_cents == 5000


def test_no_price_outside_every_tranche(annual, treasurer):
    add(annual, treasurer, start=D(2027, 1, 1), end=D(2027, 6, 30))
    assert prices.applicable(annual, D(2026, 12, 31)) is None
    assert prices.applicable(annual, D(2027, 7, 1)) is None


def test_an_open_ended_price_applies_from_its_start(annual, treasurer):
    price = add(annual, treasurer, start=D(2027, 1, 1))
    assert prices.applicable(annual, D(2030, 5, 1)) == price


def test_a_new_version_is_audited_and_notified(annual, treasurer, make_admin):  # noqa: F811
    # CA-M06-05, segona part: registre, avís al tresorer, a la junta i a la secretaria, un sol
    # correu per adreça.
    board = make_admin("board")
    board.notification_email = "junta@example.org"
    board.save()
    secretary = make_admin("secretary", "board")
    secretary.notification_email = "secretaria@example.org"
    secretary.save()
    only_secretary = make_admin("secretary")
    only_secretary.notification_email = "secretaria2@example.org"
    only_secretary.save()
    first = add(annual, treasurer)
    OutgoingEmail.objects.all().delete()
    second = add(annual, treasurer, cost=9500, note="La federació apuja el preu (inventat)")

    entry = AuditEntry.objects.filter(action=prices.ACTION_PRICE_ADDED).latest("pk")
    assert entry.old_value == first.pk
    assert entry.new_value["federation_cost_cents"] == 9500
    assert entry.reason == "La federació apuja el preu (inventat)"
    assert second.created_by == treasurer
    emails = OutgoingEmail.objects.filter(template="avis-canvi-diners")
    assert sorted(emails.values_list("to_address", flat=True)) == [
        "junta@example.org",
        "secretaria2@example.org",
        "secretaria@example.org",
        "tresorer@example.org",
    ]


def test_prices_are_append_only(annual, treasurer):
    price = add(annual, treasurer)
    price.note = "Canviada"
    with pytest.raises(AppendOnlyError):
        price.save()
    with pytest.raises(AppendOnlyError):
        LicencePrice.objects.update(federation_cost_cents=1)
    with pytest.raises(AppendOnlyError):
        price.delete()


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE licences_licenceprice SET federation_cost_cents = 1",
        "DELETE FROM licences_licenceprice",
        "TRUNCATE licences_licenceprice CASCADE",
    ],
)
def test_prices_are_append_only_in_the_database(annual, treasurer, sql):
    add(annual, treasurer)
    # Claus foranes de la fila nova comprovades abans: si no, PostgreSQL rebutja el TRUNCATE
    # abans de l'activador (com a treasury/tests/test_movements.py).
    connection.check_constraints()
    # Sense les claus foranes pendents, el TRUNCATE arriba a l'activador (patró de treasury).
    connection.check_constraints()
    with pytest.raises(DatabaseError, match="no es poden modificar"), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(sql)
