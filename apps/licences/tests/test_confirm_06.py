"""Confirmació de les llicències «pendents de confirmar» (T-M06-24; RN-M06-24 i 26; CA-M06-29 i
32; LC5): en bloc les d'any natural, una a una, i la declaració del titular. Només dades
inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_PERSONAL
from apps.core import events
from apps.core.models import AuditEntry, Event, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import imports, reminders, services
from apps.licences.models import Licence, ValidityRule
from apps.members import licence_copy
from apps.members import licences as member_licences
from apps.members.models import LicenceRecord
from apps.members.tests.test_cards import make_member

D = datetime.date
R = Role.Code
TODAY = D(2026, 6, 1)
END_2026 = D(2026, 12, 31)
PASSWORD = "contrasenya-de-proves-1954"  # noqa: S105 (dada inventada de proves)


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin(R.SECRETARY)


@pytest.fixture
def pending(make_person, annual):
    """Llicències del pas únic sense caducitat, d'any natural."""

    def make(n=1, **fields):
        values = {
            "licence_type": annual, "validity_rule": ValidityRule.CALENDAR_YEAR,
            "status": Licence.Status.ACTIVE, "origin": Licence.Origin.IMPORTED_M01,
            "starts_on": D(2026, 1, 10), "expires_on": None, "expiry_confirmed": False,
        }  # fmt: skip
        values.update(fields)
        return [
            Licence.objects.create(person=make_person(f"Soci{i}", "Prova"), **values)
            for i in range(n)
        ]

    return make


def personal(person, email):
    account = Account.objects.create_personal(person, email, PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    return account


# --- En bloc (CA-M06-32) ------------------------------------------------------------------------


def test_ca_m06_32_fifteen_of_twenty_confirmed_in_bulk_get_reminders_and_reach_the_01(
    secretary,
    annual,
    make_admin,  # noqa: F811
):
    members = [make_member(f"Soci{i}", number=i + 1, document=f"{i + 1:08d}Z") for i in range(20)]
    for member in members:
        LicenceRecord.objects.create(member=member, licence_type=annual.name,
                                     issued_on=D(2026, 1, 10), source="cluber")  # fmt: skip
    imports.confirm(make_admin(R.ADMINISTRATOR))
    for event in Event.objects.filter(name=events.LICENCE_ISSUED):
        events.deliver(event.pk)
    licences = list(Licence.objects.order_by("pk"))
    assert len(licences) == 20 and not any(lic.expiry_confirmed for lic in licences)
    chosen = [lic.pk for lic in licences[:15]]
    assert imports.confirm_in_bulk(chosen, 2026, actor=secretary, today=TODAY) == 15
    confirmed = Licence.objects.filter(pk__in=chosen)
    assert all(lic.expires_on == END_2026 and lic.expiry_confirmed for lic in confirmed)
    assert set(Licence.objects.filter(expiry_confirmed=False).values_list("pk", flat=True)) == {
        lic.pk for lic in licences[15:]
    }
    assert {lic.pk for lic in reminders.due(D(2026, 11, 1))[60]} == set(chosen)
    assert AuditEntry.objects.filter(action=imports.ACTION_EXPIRY_CONFIRMED).count() == 15
    licence_copy.daily_check()
    dated = LicenceRecord.objects.filter(expires_on=END_2026).count()
    assert dated == 15 and LicenceRecord.objects.filter(expires_on__isnull=True).count() == 5


def test_bulk_is_all_or_nothing_and_only_for_undated_calendar_year(secretary, pending):
    plain, declared, days = (
        pending()[0], pending(expires_on=D(2026, 9, 30))[0],
        pending(validity_rule=ValidityRule.DAYS_365)[0],
    )  # fmt: skip
    for other in (declared, days):
        with pytest.raises(imports.NotPending):
            imports.confirm_in_bulk([plain.pk, other.pk], 2026, actor=secretary, today=TODAY)
    plain.refresh_from_db()
    assert not plain.expiry_confirmed


def test_bulk_checks_the_year_the_start_and_the_selection(secretary, pending):
    (late,) = pending(starts_on=D(2027, 1, 1))
    with pytest.raises(imports.YearNotAllowed):
        imports.confirm_in_bulk([late.pk], 2025, actor=secretary, today=TODAY)
    with pytest.raises(imports.StartsAfterYear):
        imports.confirm_in_bulk([late.pk], 2026, actor=secretary, today=TODAY)
    with pytest.raises(imports.NothingSelected):
        imports.confirm_in_bulk([], 2026, actor=secretary, today=TODAY)
    assert imports.confirm_in_bulk([late.pk], 2027, actor=secretary, today=TODAY) == 1


@pytest.mark.parametrize("role", [R.TREASURER, R.COURSES_MANAGER, None])
def test_without_lc5_not_found(make_admin, pending, role):  # noqa: F811
    actor = make_admin(*([role] if role else []))
    (licence,) = pending()
    with pytest.raises(Http404):
        imports.confirm_in_bulk([licence.pk], 2026, actor=actor, today=TODAY)
    with pytest.raises(Http404):
        imports.unconfirmed(actor)


# --- Declaració del titular (RN-M06-26) ---------------------------------------------------------


def test_the_holder_declares_and_it_stays_pending_until_confirmed(secretary, pending):
    (licence,) = pending()
    holder = personal(licence.person, "soci0@example.org")
    declared = services.declare_expiry(licence, D(2026, 12, 31), actor=holder)
    assert (declared.expires_on, declared.expiry_confirmed) == (D(2026, 12, 31), False)
    assert declared.display_status(TODAY, 30) == Licence.Display.UNCONFIRMED
    assert not any(declared in found for found in reminders.due(D(2026, 11, 1)).values())
    assert AuditEntry.objects.filter(action=services.ACTION_EXPIRY_DECLARED).exists()
    with pytest.raises(services.AlreadyDated):
        services.declare_expiry(declared, D(2026, 11, 30), actor=holder)
    confirmed = imports.confirm_expiry(declared, D(2026, 12, 31), actor=secretary)
    assert confirmed.expiry_confirmed


def test_only_the_holder_declares_and_not_before_the_start(make_person, pending):
    (licence,) = pending()
    other = personal(make_person("Pau", "Altre"), "pau@example.org")
    with pytest.raises(Http404):
        services.declare_expiry(licence, D(2026, 12, 31), actor=other)
    with pytest.raises(services.ExpiryBeforeStart):
        services.declare_expiry(licence, D(2026, 1, 9),
                                actor=personal(licence.person, "s@example.org"))  # fmt: skip


# --- Pantalles ----------------------------------------------------------------------------------


def test_my_licence_lets_the_holder_declare_only_their_own(login_as, make_person, pending):
    mine, theirs = pending(), pending()
    licence = mine[0]
    client = login_as(personal(licence.person, "soci@example.org"), AREA_PERSONAL)
    url = reverse("licences:mine")
    assert "Desa la data" in client.get(url).content.decode()
    data = {"declara_caducitat": "1", "c-llicencia": licence.pk, "c-caducitat": "2026-12-31"}
    assert "la secretaria ho confirmarà" in client.post(url, data, follow=True).content.decode()
    licence.refresh_from_db()
    assert (licence.expires_on, licence.expiry_confirmed) == (D(2026, 12, 31), False)
    other = {**data, "c-llicencia": theirs[0].pk}
    assert client.post(url, other).status_code == 404


# --- El 01 ja no confirma les que són al 06 -----------------------------------------------------


def test_the_01_pending_screens_skip_rows_already_in_the_06(secretary):
    member = make_member("Eva", number=3, document="00000003Z")
    linked = LicenceRecord.objects.create(member=member, licence_type="Anual (inventat)",
                                          issued_on=D(2026, 1, 10), source="cluber",
                                          licence_ref=999)  # fmt: skip
    assert linked not in member_licences.pending_records(secretary)
    holder = personal(member.person, "eva@example.org")
    with pytest.raises(ValidationError):
        member_licences.declare_expiry(linked, by=holder, expires_on=D(2026, 12, 31))
