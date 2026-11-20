"""Llocs i preu estàndard de la sortida amb versions (T-M02-37; addenda de llocs del 02; RN-M02-38
i 39; part de CA-M02-42 i CA-M02-44 que no necessita activitats). Només dades inventades.

Les activitats, les sessions i els blocs amb `place` arriben amb la T-M02-03; els permisos AC21 i
AC22, amb la T-M02-38; la pantalla «Llocs», amb la T-M02-39.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.activities import catalogue
from apps.activities.models import Place, PlacePrice
from apps.core.business_settings import EMAIL_TEMPLATE
from apps.core.models import AppendOnlyError, AuditEntry, OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db

TODAY = datetime.date(2026, 11, 20)
TOMORROW = TODAY + datetime.timedelta(days=1)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    account = make_admin(Role.Code.TREASURER)
    account.notification_email = "tresorer@example.org"
    account.save()
    return account


@pytest.fixture
def place(manager):
    return catalogue.create_place(by=manager, name="Lloc de prova", notes="Nota inventada.")


def set_price(place, by, member, non_member, valid_from=TODAY, note="Nota inventada."):
    return catalogue.change_place_price(
        place,
        by=by,
        price_member_cents=member,
        price_non_member_cents=non_member,
        valid_from=valid_from,
        note=note,
        today=TODAY,
    )


# --- RN-M02-38: el lloc és una dada ---------------------------------------------------------------


def test_ca_m02_42_a_new_place_is_active_without_price_and_recorded(manager, place):
    assert place.active and place.created_by == manager
    assert catalogue.place_price_on(place, TODAY) is None  # l'aula, per exemple
    record = AuditEntry.objects.get(action=catalogue.PLACE_CREATED)
    assert record.actor_account == manager and record.target_id == str(place.pk)


@pytest.mark.parametrize("name", ["Lloc de prova", "LLOC DE PROVA", "  lloc de prova "])
def test_names_are_unique_ignoring_case(manager, place, name):
    with pytest.raises(ValidationError):
        catalogue.create_place(by=manager, name=name)
    with pytest.raises(IntegrityError), transaction.atomic():
        Place.objects.create(name=name.strip().upper())


@pytest.mark.parametrize("fields", [{"name": "  "}, {"name": "Un altre", "notes": "x" * 1001}])
def test_create_place_rejects_wrong_values(manager, fields):
    with pytest.raises(ValidationError):
        catalogue.create_place(by=manager, **fields)
    assert not Place.objects.exists()


def test_editing_a_place_records_the_previous_value(manager, place):
    changed = catalogue.update_place(place, by=manager, name="Lloc nou", notes="Nota inventada.")
    assert changed == ["name"]
    place.refresh_from_db()
    assert place.name == "Lloc nou"
    record = AuditEntry.objects.get(action=catalogue.PLACE_UPDATED)
    assert (record.field, record.old_value, record.new_value) == (
        "name",
        "Lloc de prova",
        "Lloc nou",
    )
    other = catalogue.create_place(by=manager, name="Un altre lloc")
    with pytest.raises(ValidationError):
        catalogue.update_place(other, by=manager, name="lloc NOU")
    assert catalogue.update_place(place, by=manager, name="Lloc nou", notes="Nota inventada.") == []


def test_a_place_is_deactivated_and_reactivated_not_deleted(manager, place):
    assert catalogue.set_active(place, False, by=manager) is True
    place.refresh_from_db()
    assert place.active is False
    assert catalogue.set_active(place, True, by=manager) is True
    assert AuditEntry.objects.filter(action=catalogue.ACTIVE_CHANGED).count() == 2


# --- RN-M02-39: preu estàndard amb data d'entrada en vigor ---------------------------------------


def test_ca_m02_44_a_new_standard_price_applies_from_its_date(manager, place):
    set_price(place, manager, 4500, 6000)
    set_price(place, manager, 5000, 6000, valid_from=TOMORROW)
    assert catalogue.place_price_on(place, TODAY).price_member_cents == 4500
    assert catalogue.place_price_on(place, TOMORROW).price_member_cents == 5000
    assert catalogue.place_price_on(place, TOMORROW).price_non_member_cents == 6000
    assert catalogue.place_price_on(place, TODAY - datetime.timedelta(days=1)) is None


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"note": "  "}, "motiu"),
        ({"valid_from": TODAY - datetime.timedelta(days=1)}, "passada"),
        ({"member": -1}, "cèntims"),
        ({"non_member": 60.5}, "cèntims"),
        ({"member": 4500, "non_member": 6000}, "mateix"),
    ],
)
def test_ca_m02_44_wrong_price_changes_are_rejected(manager, place, fields, message):
    set_price(place, manager, 4500, 6000)
    request = {"member": 5000, "non_member": 6000, "valid_from": TODAY, "note": "Nota.", **fields}
    with pytest.raises(ValidationError) as error:
        set_price(place, manager, **request)
    assert message in " ".join(error.value.messages)
    assert PlacePrice.objects.count() == 1


def test_a_price_change_is_recorded_with_the_previous_value(manager, place):
    set_price(place, manager, 4500, 6000)
    set_price(place, manager, 5000, 6000, valid_from=TOMORROW, note="Puja (nota inventada).")
    changes = {
        (e.field, e.old_value, e.new_value)
        for e in AuditEntry.objects.filter(action=catalogue.PLACE_PRICE_CHANGED)
    }
    assert ("price_member_cents", None, 4500) in changes  # el primer preu no en tenia cap
    assert ("price_member_cents", 4500, 5000) in changes
    assert not any(old == new for _, old, new in changes)  # el no soci no ha canviat


def test_ca_m02_44_a_price_change_sends_one_notice(manager, treasurer, place):
    set_price(place, manager, 4500, 6000)
    set_price(place, manager, 5000, 6000, valid_from=TOMORROW, note="Puja (nota inventada).")
    emails = OutgoingEmail.objects.filter(template=EMAIL_TEMPLATE).order_by("pk")
    assert [e.to_address for e in emails] == ["tresorer@example.org"] * 2  # un per canvi
    body = emails.last().body_text
    assert "Lloc de prova" in body and "45,00 €" in body and "50,00 €" in body
    assert "Puja (nota inventada)." in body
    assert "Nota inventada." not in body  # les notes del lloc no surten mai


def test_place_prices_are_append_only(manager, place):
    price = set_price(place, manager, 4500, 6000)
    price.price_member_cents = 1
    with pytest.raises(AppendOnlyError):
        price.save()
    with pytest.raises(AppendOnlyError):
        price.delete()
    with pytest.raises(AppendOnlyError):
        PlacePrice.objects.all().update(price_member_cents=1)


@pytest.mark.parametrize("role", [Role.Code.EQUIPMENT_MANAGER, Role.Code.SECRETARY])
def test_without_ac22_places_are_not_changed(make_admin, manager, place, role):  # noqa: F811
    # RN-M02-46: el responsable de material veu els llocs (AC21) però no els edita.
    other = make_admin(role)
    for call in (
        lambda: catalogue.create_place(by=other, name="Un altre lloc"),
        lambda: catalogue.update_place(place, by=other, name="Un altre nom"),
        lambda: catalogue.set_active(place, False, by=other),
        lambda: set_price(place, other, 4500, 6000),
    ):
        with pytest.raises(Http404):
            call()
    place.refresh_from_db()
    assert (place.name, place.active, Place.objects.count()) == ("Lloc de prova", True, 1)
    assert not PlacePrice.objects.exists()
