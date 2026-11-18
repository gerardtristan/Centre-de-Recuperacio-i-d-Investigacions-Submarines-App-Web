"""Pantalla de tipus de soci (T-M01-52, part b; 091, RN-M01-107, CA-M01-125): veure, crear,
editar i desactivar tipus, cada tipus amb el seu preu editable, permisos per rol i registre.
Només dades inventades."""

import pytest
from django.urls import reverse

from apps.core import business_settings
from apps.core.models import AuditEntry, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import types
from apps.members.models import MembershipType
from apps.members.tests.test_join import submit, texts  # noqa: F401 (fixture)
from apps.members.tests.test_join_minors import GUARDIAN, today  # noqa: F401 (fixture)
from apps.members.tests.test_member_requests import make_member
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db

LIST = "administration:membership_types"
EDIT = "administration:membership_type_edit"
VIEWERS = {"treasurer", "administrator", "secretary"}  # «Cons.» de l'apartat
EDITORS = {"treasurer", "administrator"}  # P-376
ROLES = ["treasurer", "administrator", "secretary", "president", "board", "instructor"]
NEW = {"name": "Juvenil", "code": "juvenil", "price": "20,00", "min_age": "0"}


def full():
    return MembershipType.objects.get(code="full")


@pytest.mark.parametrize("role", ROLES)
def test_who_sees_and_who_creates(make_admin, role):  # noqa: F811
    client = admin_client(make_admin(role))
    page = client.get(reverse(LIST))
    assert page.status_code == (200 if role in VIEWERS else 404)
    if role in VIEWERS:
        assert ('name="code"' in page.content.decode()) is (role in EDITORS)
    response = client.post(reverse(LIST), NEW)
    assert response.status_code == (302 if role in EDITORS else 404)
    assert MembershipType.objects.filter(code="juvenil").exists() is (role in EDITORS)
    denied = AuditEntry.objects.filter(action=types.DENIED).exists()
    assert denied is (role in VIEWERS - EDITORS)  # qui només veu i ho intenta, al registre


def test_a_new_type_comes_with_its_editable_price(make_admin):  # noqa: F811
    treasurer = make_admin("treasurer")
    admin_client(treasurer).post(reverse(LIST), NEW)
    created = MembershipType.objects.get(code="juvenil")
    price = Setting.objects.get(key="members.annual_fee_cents.juvenil")
    assert (created.annual_fee_cents, price.initial_value) == (2000, 2000)
    assert price.affects_money and price.effective_dated and price.module == "members"
    assert business_settings.can_edit(treasurer, price)
    assert not business_settings.can_edit(make_admin("secretary"), price)
    entry = AuditEntry.objects.get(action=types.CREATED)
    assert entry.details["annual_fee_cents"] == 2000 and entry.actor_account == treasurer
    section = admin_client(treasurer).get(
        reverse("administration:settings_section", args=["members"])
    )
    assert "Quota anual de cada tipus de soci: Juvenil" in section.content.decode()


def test_the_existing_prices_keep_their_editors(make_admin):  # noqa: F811
    for key in ("members.annual_fee_cents.full", "members.annual_fee_cents.supporter"):
        setting = Setting.objects.get(key=key)
        assert business_settings.can_edit(make_admin("administrator"), setting)
        assert not business_settings.can_edit(make_admin("secretary"), setting)


@pytest.mark.parametrize(
    "data",
    [
        {**NEW, "full_rights": "on", "min_age": "10"},  # RN-M01-64
        {**NEW, "code": "full"},  # el codi és únic
        {**NEW, "code": "Juvenil"},
        {**NEW, "price": "0"},
    ],
)
def test_an_invalid_type_saves_nothing(make_admin, data):  # noqa: F811
    response = admin_client(make_admin("administrator")).post(reverse(LIST), data)
    assert response.status_code == 200
    assert MembershipType.objects.count() == 2
    assert not Setting.objects.filter(key="members.annual_fee_cents.juvenil").exists()


@pytest.mark.usefixtures("texts", "today")
def test_ca_m01_125_a_type_created_like_supporter_admits_a_10_year_old(make_admin):  # noqa: F811
    admin_client(make_admin("administrator")).post(reverse(LIST), NEW)
    created = MembershipType.objects.get(code="juvenil")
    response = submit(birth_date="2016-04-01", membership_type=created.pk, **GUARDIAN)
    assert response.status_code == 303


class TestEdit:
    def test_a_type_with_members_only_changes_its_name(self, make_admin):  # noqa: F811
        make_member(type_code="full")
        client = admin_client(make_admin("administrator"))
        data = {"name": "Ple dret", "full_rights": "on", "min_age": "14", "active": "on"}
        client.post(reverse(EDIT, args=[full().pk]), {**data, "name": "Soci de ple dret"})
        assert full().name == "Soci de ple dret"
        entry = AuditEntry.objects.get(action=types.CHANGED)
        assert (entry.field, entry.old_value) == ("name", "Ple dret")
        for change in ({"min_age": "16"}, {"active": ""}, {"full_rights": ""}):
            response = client.post(reverse(EDIT, args=[full().pk]), {**data, **change})
            assert "No s'ha desat res." in response.content.decode()
        assert (full().min_age, full().active, full().full_rights) == (14, True, True)

    def test_a_type_without_members_is_deactivated(self, make_admin):  # noqa: F811
        client = admin_client(make_admin("treasurer"))
        data = {"name": "Ple dret", "full_rights": "on", "min_age": "14"}  # sense «actiu»
        assert client.post(reverse(EDIT, args=[full().pk]), data).status_code == 302
        assert not full().active
        entry = AuditEntry.objects.get(action=types.CHANGED)
        assert (entry.field, entry.old_value, entry.new_value) == ("active", True, False)

    def test_who_only_views_cannot_edit(self, make_admin):  # noqa: F811
        client = admin_client(make_admin("secretary"))
        assert client.get(reverse(EDIT, args=[full().pk])).status_code == 200
        response = client.post(reverse(EDIT, args=[full().pk]), {"name": "X", "min_age": "14"})
        assert response.status_code == 404 and full().name == "Ple dret"
