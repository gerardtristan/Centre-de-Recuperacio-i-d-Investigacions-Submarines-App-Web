"""Caducitat declarada pel soci i enllaç a la confirmació en bloc (T-M01-36; RN-M01-56,
RN-M01-77; CA-M01-44, segona meitat; CA-M01-76; CA-M01-80).

El soci declara al perfil la caducitat desconeguda d'un registre seu; queda «declarada» i cap
consumidor no la tracta com a vigent fins que la secretaria l'accepta o la corregeix a la fitxa.
La primera meitat de CA-M01-44 és a `test_licence_bulk_confirm.py`. Només dades inventades.
"""

import datetime
import time

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import Http404
from django.test import Client
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import audit
from apps.core.models import AuditEntry, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_error_pages import body
from apps.members import cards, licences, services
from apps.members.models import LicenceRecord
from apps.members.services import InactiveAccount
from apps.members.tests.test_cards import paid_member
from apps.members.tests.test_member_edit import a_member
from apps.members.tests.test_roster import admin_client, remove_permission
from conftest import PASSWORD

DECLARE = "members:declare_expiry"
PROFILE = "members:profile"
CARD = "members:card"
EDIT = "administration:licence_edit"
DETAIL = "administration:member_detail"
BULK = "administration:licence_bulk_confirm"
HOME = "administration:home"
ISSUED = datetime.date(2026, 3, 1)
FUTURE = datetime.date(2099, 12, 31)  # futura: si la tractés com a coneguda, seria vigent
NOT_FOUND = audit.Action.PERSONAL_AREA_NOT_FOUND


def unknown_record(member, *, expires_on=None, declared=False):
    return LicenceRecord.objects.create(
        member=member,
        licence_type="Anual FECDAS",
        issued_on=ISSUED,
        expires_on=expires_on,
        expiry_declared=declared,
        source=LicenceRecord.Source.CLUBER,
    )


def personal_account(member, email="soci.declara@example.org"):
    account = Account.objects.create_personal(member.person, email, PASSWORD)
    Account.objects.filter(pk=account.pk).update(status=Account.Status.ACTIVE)
    account.refresh_from_db()
    return account


def personal_client(account):
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_PERSONAL
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


def declare(client, record, value="2099-12-31"):
    return client.post(
        reverse(DECLARE, args=[record.pk]), {f"llicencia-{record.pk}-expires_on": value}
    )


def entries(action, record):
    rows = AuditEntry.objects.filter(
        action=action, target_type="members.licencerecord", target_id=str(record.pk)
    )
    return {e.field: (e.old_value, e.new_value) for e in rows}


@pytest.fixture
def soci(db):
    member = a_member("Declara", document=("passport", "PROVADE0001"))
    return member, personal_account(member)


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin("secretary")


# --- Criteris ---------------------------------------------------------------------------------


@pytest.mark.django_db
class TestCriteria:
    def test_ca_m01_44_and_ca_m01_76_declared_until_the_secretary_accepts(self, soci, secretary):
        """CA-M01-44 (segona meitat) i CA-M01-76: declarar → «declarada pel soci», no vigent i
        fora de la confirmació en bloc; acceptar-la a la fitxa treu la marca amb el valor
        anterior al registre."""
        member, account = soci
        record = unknown_record(member)
        client = personal_client(account)

        response = declare(client, record)
        assert response.status_code == 302
        record.refresh_from_db()
        assert (record.expires_on, record.expiry_declared) == (FUTURE, True)
        assert entries(licences.DECLARED, record) == {
            "expires_on": (None, "2099-12-31"),
            "expiry_declared": (False, True),
        }
        assert "pendent que la secretaria la confirmi" in client.get(reverse(PROFILE)).text

        info = services.licence_record(member.person)
        assert (info.expires_on, info.expiry_unknown, info.declared_expires_on) == (
            None,
            True,
            FUTURE,
        )
        assert record not in licences.pending_records(secretary)

        staff = admin_client(secretary)
        detail = staff.get(reverse(DETAIL, args=[member.pk])).text
        assert "Declarada pel soci, pendent de confirmar" in detail
        assert "Confirma o corregeix" in detail
        accepted = staff.post(
            reverse(EDIT, args=[member.pk, record.pk]),
            {"licence_type": "Anual FECDAS", "issued_on": "2026-03-01", "expires_on": "2099-12-31"},
        )
        assert accepted.status_code == 303
        record.refresh_from_db()
        assert (record.expires_on, record.expiry_declared) == (FUTURE, False)
        assert entries(licences.CORRECTED, record) == {"expiry_declared": (True, False)}
        assert services.licence_record(member.person).expires_on == FUTURE
        assert "Declarada pel soci" not in staff.get(reverse(DETAIL, args=[member.pk])).text

    def test_ca_m01_76_secretary_corrects_the_declared_date(self, soci, secretary):
        member, _account = soci
        record = unknown_record(member, expires_on=FUTURE, declared=True)
        response = admin_client(secretary).post(
            reverse(EDIT, args=[member.pk, record.pk]),
            {"licence_type": "Anual FECDAS", "issued_on": "2026-03-01", "expires_on": "2026-12-31"},
        )
        assert response.status_code == 303
        record.refresh_from_db()
        assert (record.expires_on, record.expiry_declared) == (datetime.date(2026, 12, 31), False)
        assert entries(licences.CORRECTED, record) == {
            "expires_on": ("2099-12-31", "2026-12-31"),
            "expiry_declared": (True, False),
        }

    def test_ca_m01_76_edit_form_says_the_date_was_declared(self, soci, secretary):
        member, _account = soci
        record = unknown_record(member, expires_on=FUTURE, declared=True)
        page = admin_client(secretary).get(reverse(EDIT, args=[member.pk, record.pk])).text
        assert "Declarada pel soci, pendent de confirmar" in page
        assert 'value="2099-12-31"' in page

    def test_ca_m01_76_another_member_cannot_declare_by_direct_url(self, soci):
        """Un registre d'un altre soci o un que no existeix: la mateixa resposta «no trobat»
        i l'intent registrat, com el detall d'una quota (CA-M01-25)."""
        _member, account = soci
        other = unknown_record(a_member("Sentinella", document=("passport", "PROVASE0001")))
        client = personal_client(account)
        foreign = declare(client, other)
        missing = declare(client, LicenceRecord(pk=other.pk + 1000))
        assert foreign.status_code == missing.status_code == 404
        # La mateixa pàgina 404 (T-M01-47); només hi canvia el testimoni CSRF de cada resposta.
        assert body(foreign) == body(missing)
        other.refresh_from_db()
        assert (other.expires_on, other.expiry_declared) == (None, False)
        logged = list(AuditEntry.objects.filter(action=NOT_FOUND).order_by("id"))
        assert len(logged) == 2
        assert logged[0].actor_account == account
        assert (logged[0].target_type, logged[0].target_id) == (
            "members.licencerecord",
            str(other.pk),
        )
        assert logged[0].details == {"object": "members.licencerecord", "id": other.pk}
        assert logged[1].target_id == ""


# --- No vigent mentre és declarada (RN-M01-77, 074 punt 9) ---------------------------------------


@pytest.mark.django_db
class TestNotValidWhileDeclared:
    def test_licence_records_treats_it_as_unknown(self, soci):
        member, _account = soci
        unknown_record(member, expires_on=FUTURE, declared=True)
        (info,) = [i for i in services.licence_records() if i.person_id == member.person_id]
        assert info.expires_on is None and info.expiry_unknown
        assert info.declared_expires_on == FUTURE

    def test_a_known_record_wins_over_a_later_declared_one(self, soci):
        member, _account = soci
        unknown_record(member, expires_on=FUTURE, declared=True)
        known = unknown_record(member, expires_on=datetime.date(2026, 12, 31))
        info = services.licence_record(member.person)
        assert info.record_id == known.pk
        assert (info.expires_on, info.declared_expires_on) == (datetime.date(2026, 12, 31), None)

    def test_card_does_not_show_it_as_valid(self, db):
        member = paid_member(document="00000001R")
        account = personal_account(member)
        cards.issue_card(member, by=audit.system("proves"))
        unknown_record(member, expires_on=FUTURE, declared=True)
        page = personal_client(account).get(reverse(CARD)).text
        assert "Fins al 31/12/2099" not in page
        assert "Caducitat desconeguda (declarada per tu: 31/12/2099" in page

    def test_bulk_confirmation_does_not_show_or_accept_it(self, soci, secretary):
        member, _account = soci
        record = unknown_record(member, expires_on=FUTURE, declared=True)
        assert record not in licences.pending_records(secretary)
        form = licences.BulkConfirmForm({"records": [record.pk], "year": "2026"})
        assert not form.is_valid()
        with pytest.raises(ValidationError):
            licences.confirm_in_bulk([record.pk], year=2026, by=secretary)
        page = admin_client(secretary).get(reverse(BULK)).text
        assert f'value="{record.pk}"' not in page

    def test_declared_without_a_date_is_rejected_by_the_database(self, soci):
        member, _account = soci
        with pytest.raises(IntegrityError):
            unknown_record(member, declared=True)


# --- Declarar: només una caducitat desconeguda i una data vàlida -------------------------------


@pytest.mark.django_db
class TestDeclare:
    def test_profile_offers_the_form_only_for_unknown_expiry(self, soci):
        member, account = soci
        unknown = unknown_record(member)
        known = unknown_record(member, expires_on=datetime.date(2026, 12, 31))
        declared = unknown_record(member, expires_on=FUTURE, declared=True)
        page = personal_client(account).get(reverse(PROFILE)).text
        assert reverse(DECLARE, args=[unknown.pk]) in page
        assert reverse(DECLARE, args=[known.pk]) not in page
        assert reverse(DECLARE, args=[declared.pk]) not in page

    @pytest.mark.parametrize("declared", [False, True])
    def test_a_record_with_an_expiry_cannot_be_declared(self, soci, declared):
        member, account = soci
        record = unknown_record(member, expires_on=datetime.date(2026, 12, 31), declared=declared)
        response = declare(personal_client(account), record, "2030-12-31")
        assert response.status_code == 200
        assert "ja té data de caducitat" in response.text
        record.refresh_from_db()
        assert record.expires_on == datetime.date(2026, 12, 31)
        assert not entries(licences.DECLARED, record)

    def test_date_before_the_issue_date_is_rejected(self, soci):
        member, account = soci
        record = unknown_record(member)
        response = declare(personal_client(account), record, "2026-02-28")
        assert response.status_code == 200
        assert "no pot ser anterior a la data" in response.text
        record.refresh_from_db()
        assert record.expires_on is None and not record.expiry_declared

    @pytest.mark.parametrize("value", ["", "no-és-una-data"])
    def test_missing_or_invalid_date_is_rejected(self, soci, value):
        member, account = soci
        record = unknown_record(member)
        assert declare(personal_client(account), record, value).status_code == 200
        record.refresh_from_db()
        assert record.expires_on is None

    def test_only_post(self, soci):
        member, account = soci
        record = unknown_record(member)
        assert personal_client(account).get(reverse(DECLARE, args=[record.pk])).status_code == 405

    def test_without_session_goes_to_the_login(self, soci, client):
        member, _account = soci
        record = unknown_record(member)
        response = declare(client, record)
        assert response.status_code == 302
        record.refresh_from_db()
        assert record.expires_on is None

    def test_service_rejects_another_persons_record(self, soci):
        _member, account = soci
        other = unknown_record(a_member("Altre", document=("passport", "PROVAAL0001")))
        with pytest.raises(Http404):
            licences.declare_expiry(other, by=account, expires_on=FUTURE)

    def test_service_rejects_an_inactive_account(self, soci):
        member, account = soci
        record = unknown_record(member)
        Account.objects.filter(pk=account.pk).update(status=Account.Status.DISABLED)
        with pytest.raises(InactiveAccount):
            licences.declare_expiry(record, by=account, expires_on=FUTURE)
        record.refresh_from_db()
        assert record.expires_on is None

    def test_service_rejects_an_anonymised_person(self, soci):
        member, account = soci
        record = unknown_record(member)
        Person.objects.filter(pk=member.person_id).update(
            status=Person.Status.ANONYMISED, anonymous_ref="A-0001"
        )
        with pytest.raises(ValidationError):
            licences.declare_expiry(record, by=account, expires_on=FUTURE)


# --- Enllaç a la confirmació en bloc (CA-M01-80, 074 punt 12) ----------------------------------


@pytest.mark.django_db
class TestBulkLink:
    def test_ca_m01_80_link_with_p19_and_p4(self, secretary):
        page = admin_client(secretary).get(reverse(HOME)).text
        assert reverse(BULK) in page

    @pytest.mark.parametrize("role", ["treasurer", "president", "courses_manager"])
    def test_ca_m01_80_no_link_and_denied_without_p19(self, make_admin, role):  # noqa: F811
        client = admin_client(make_admin(role))
        assert reverse(BULK) not in client.get(reverse(HOME)).text
        assert client.get(reverse(BULK)).status_code == 404

    def test_ca_m01_80_no_link_and_denied_without_p4(self, secretary):
        remove_permission("secretary", "members.list")
        client = admin_client(secretary)
        assert reverse(BULK) not in client.get(reverse(HOME)).text
        assert client.get(reverse(BULK)).status_code == 404
