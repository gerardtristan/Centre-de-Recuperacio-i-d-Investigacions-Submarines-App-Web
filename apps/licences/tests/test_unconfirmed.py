"""Llicències «pendents de confirmar» (T-M06-23; RN-M06-24; CA-M06-29). Només dades inventades."""

import datetime
from types import SimpleNamespace

import pytest
from django.db import IntegrityError, transaction
from django.http import Http404
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities import requirements
from apps.core import events
from apps.core.models import AuditEntry, Event, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import events as licence_events
from apps.licences import imports, listing, reminders
from apps.licences.models import Licence
from apps.licences.services import current, participant_status
from apps.licences.tests.test_services import scope_checks  # noqa: F401 (fixture)
from apps.members import licence_copy
from apps.members.models import LicenceRecord
from apps.members.tests.test_cards import make_member

D = datetime.date
R = Role.Code
S = Licence.Status


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def imported(admin, annual):
    """Un registre del 01 sense caducitat passat al 06 pel pas únic, amb la còpia lligada."""
    member = make_member("Eva", number=3, document="00000003Z")
    record = LicenceRecord.objects.create(
        member=member, licence_type="Aficionat anual (inventat)", issued_on=D(2027, 1, 10),
        expires_on=None, source="cluber",
    )  # fmt: skip
    imports.confirm(admin)
    for event in Event.objects.filter(name=events.LICENCE_ISSUED):
        events.deliver(event.pk)
    record.refresh_from_db()
    return Licence.objects.get(m01_record_ref=record.pk), record


def unconfirmed(make_licence, **fields):
    values = {"status": S.ACTIVE, "origin": "imported_m01", "price_kind": None,
              "price_cents": None, "starts_on": D(2027, 1, 10), "expires_on": None,
              "expiry_confirmed": False}  # fmt: skip
    values.update(fields)
    return make_licence(**values)


# --- Pas únic -----------------------------------------------------------------------------------


def test_ca_m06_29_the_import_creates_an_unconfirmed_licence_linked_to_its_01_row(imported):
    licence, record = imported
    assert (licence.status, licence.expires_on, licence.expiry_confirmed) == (S.ACTIVE, None, False)
    assert licence.display_status(D(2027, 6, 1), 30) == Licence.Display.UNCONFIRMED
    payload = Event.objects.get(name=events.LICENCE_ISSUED).payload
    assert payload["expires_on"] is None
    assert (record.licence_ref, record.expires_on) == (licence.pk, None)
    assert "?" in str(licence)


def test_a_record_of_an_unknown_type_without_expiry_stays_in_the_preview(admin, annual):
    member = make_member("Joan", number=4, document="00000004Z")
    LicenceRecord.objects.create(member=member, licence_type="Tipus que el 06 no té",
                                 issued_on=D(2027, 1, 10), source="cluber")  # fmt: skip
    assert imports.summary(imports.preview(admin)) == {"unknown_type": 1}


def test_no_reminder_and_no_expired_event_while_unconfirmed(make_licence):
    # També amb una data encara no confirmada (la declaració del soci, T-M06-24).
    licence = unconfirmed(make_licence, expires_on=D(2027, 3, 1))
    assert all(licence not in found for found in reminders.due(D(2027, 1, 30)).values())
    assert licence_events.expire_due(D(2027, 3, 5)) == 0
    assert not listing.expiring(60, D(2027, 1, 30)).filter(pk=licence.pk).exists()


def test_the_01_source_never_sees_an_unconfirmed_date(make_licence):
    licence = unconfirmed(make_licence, expires_on=D(2027, 3, 1))
    (row,) = [r for r in licence_events.read_source() if r["licence"] == licence.pk]
    assert row["expires_on"] is None
    assert licence_events.payload(licence)["expires_on"] is None


def test_only_an_imported_active_licence_can_be_unconfirmed(make_licence):
    with pytest.raises(IntegrityError), transaction.atomic():
        make_licence(expires_on=None)  # del club, sense caducitat
    with pytest.raises(IntegrityError), transaction.atomic():
        make_licence(expiry_confirmed=False)


# --- licences.current i LC10 --------------------------------------------------------------------


def test_current_returns_unconfirmed_without_a_date(make_licence):
    licence = unconfirmed(make_licence)
    found = current(licence.person, D(2029, 6, 1))
    assert (found.status, found.expires_on, found.origin) == ("unconfirmed", None, "imported_m01")
    assert current(licence.person, D(2027, 1, 9)) is None  # encara no havia començat


def test_a_confirmed_active_one_wins_and_unconfirmed_wins_over_in_progress(make_licence):
    licence = unconfirmed(make_licence)
    make_licence(status=S.REQUESTED, starts_on=D(2027, 1, 1))
    assert current(licence.person, D(2027, 5, 10)).status == "unconfirmed"
    make_licence(status=S.ACTIVE, origin="external", price_kind=None, price_cents=None,
                 starts_on=D(2027, 2, 1), expires_on=D(2027, 9, 30))  # fmt: skip
    assert current(licence.person, D(2027, 5, 10)).status == "active"


@pytest.mark.parametrize(
    ("role", "seen"),
    [(R.INSTRUCTOR, "no"), (R.COURSES_MANAGER, "unconfirmed"), (R.SECRETARY, "unconfirmed")],
)
def test_rn_m06_24_the_manager_sees_unconfirmed_and_the_instructor_no(
    make_admin,  # noqa: F811
    make_licence,
    scope_checks,  # noqa: F811
    role,
    seen,
):
    licence = unconfirmed(make_licence)
    assert participant_status(make_admin(role), licence.person, D(2027, 5, 10), "meva") == seen


def test_the_02_requirement_is_not_met_while_unconfirmed(make_licence):
    licence = unconfirmed(make_licence)
    check = requirements._licence(SimpleNamespace(starts_on=D(2027, 5, 10)), licence.person)
    assert (check.state, check.detail) == (requirements.NOT_MET, "Pendent de confirmar.")


# --- Llistat ------------------------------------------------------------------------------------


def test_the_list_shows_it_pending_without_a_date(login_as, admin, make_licence):
    licence = unconfirmed(make_licence)
    (row,) = listing.licence_list(admin, today=D(2027, 5, 10))
    assert (row.licence_id, row.status, row.expires_on) == (licence.pk, "unconfirmed", None)
    assert listing.licence_list(admin, today=D(2027, 5, 10), status="unconfirmed") == [row]
    client = login_as(admin, AREA_ADMIN)
    response = client.get(reverse("administration:licences"), {"estat": "unconfirmed"})
    html = response.content.decode()
    assert "Pendent de confirmar" in html and "Per confirmar" in html


# --- La secretaria hi posa la data (CA-M06-29) --------------------------------------------------


def test_ca_m06_29_once_dated_it_is_normal_gets_reminders_and_the_01_copies_it(
    make_admin,  # noqa: F811
    imported,
):
    licence, record = imported
    secretary = make_admin(R.SECRETARY)
    dated = imports.confirm_expiry(licence, D(2027, 12, 31), actor=secretary)
    assert (dated.expires_on, dated.expiry_confirmed, dated.version) == (
        D(2027, 12, 31), True, licence.version + 1,
    )  # fmt: skip
    entry = AuditEntry.objects.get(action=imports.ACTION_EXPIRY_CONFIRMED)
    assert (entry.old_value, entry.new_value) == (None, "2027-12-31")
    assert dated.display_status(D(2027, 6, 1), 30) == Licence.Display.VALID
    assert dated in reminders.due(D(2027, 11, 1))[60]
    assert current(dated.person, D(2027, 6, 1)).expires_on == D(2027, 12, 31)
    licence_copy.daily_check()
    record.refresh_from_db()
    assert (record.expires_on, record.source_version) == (D(2027, 12, 31), dated.version)


def test_confirm_expiry_checks_the_date_and_that_it_was_pending(make_admin, make_licence):  # noqa: F811
    secretary = make_admin(R.SECRETARY)
    licence = unconfirmed(make_licence)
    with pytest.raises(imports.ExpiryBeforeStart):
        imports.confirm_expiry(licence, D(2027, 1, 9), actor=secretary)
    imports.confirm_expiry(licence, D(2027, 12, 31), actor=secretary)
    with pytest.raises(imports.AlreadyConfirmed):
        imports.confirm_expiry(licence, D(2028, 1, 31), actor=secretary)


@pytest.mark.parametrize("role", [R.TREASURER, R.INSTRUCTOR, None])
def test_confirm_expiry_without_lc5_is_not_found(make_admin, make_licence, role):  # noqa: F811
    licence = unconfirmed(make_licence)
    with pytest.raises(Http404):
        imports.confirm_expiry(licence, D(2027, 12, 31),
                               actor=make_admin(*([role] if role else [])))  # fmt: skip
    licence.refresh_from_db()
    assert not licence.expiry_confirmed


def test_my_licence_shows_it_pending_without_a_date(make_licence, make_person, login_as):
    from apps.accounts.models import Account
    from apps.accounts.security import AREA_PERSONAL

    person = make_person("Marta", "Soler")
    unconfirmed(make_licence, person=person, expires_on=D(2027, 3, 1))  # declarada, no confirmada
    account = Account.objects.create_personal(person, "marta@example.org",
                                              "contrasenya-de-proves-1954")  # fmt: skip
    account.status = Account.Status.ACTIVE
    account.save()
    html = login_as(account, AREA_PERSONAL).get(reverse("licences:mine")).content.decode()
    assert "Pendent de confirmar" in html and "Per confirmar" in html
    assert "Has dit que caduca el 01/03/2027" in html  # declarada, però no com a caducitat
