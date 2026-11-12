"""Confirmació en bloc de les caducitats d'any natural pendents (T-M01-36; RN-M01-56, CA-M01-44).

Permisos al servidor (P19 sencer i P4, com afegir i corregir a la T-M01-23), conflicte d'interès
(S-M01-22), tot o res, i registre d'activitat amb el valor anterior per a cada registre. La
declaració del soci (segona meitat de CA-M01-44) no és en aquesta branca. Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.core.models import AuditEntry, Person
from apps.core.tests.conftest import (
    main_of,
    make_admin,  # noqa: F401 (fixture)
)
from apps.members import licences, services
from apps.members.models import LicenceRecord
from apps.members.services import InactiveAccount, OwnMemberChange
from apps.members.tests.test_member_edit import a_member
from apps.members.tests.test_roster import admin_client, remove_permission

URL = "administration:licence_bulk_confirm"
ISSUED = datetime.date(2026, 3, 1)
END_2026 = datetime.date(2026, 12, 31)


@pytest.fixture(autouse=True)
def _year_2026(monkeypatch):
    """Les proves d'aquest fitxer passen l'any 2026: des de la decisió 085 (S-4) només es pot
    confirmar l'any actual o el següent, i els anys d'aquí són fixos."""
    monkeypatch.setattr(licences, "_current_year", lambda: 2026)


WITHOUT_P19_WRITE = [
    "treasurer",
    "courses_manager",
    "president",
    "board",
    "instructor",
    "equipment_manager",
    "history_department",
]


def pending(n, *, issued_on=ISSUED, first="Soci"):
    """`n` socis inventats, cadascun amb un registre de Cluber sense caducitat."""
    records = []
    for i in range(n):
        member = a_member(f"{first}{i}", document=("passport", f"PROVA{first[:2]}{i:04d}"))
        records.append(
            LicenceRecord.objects.create(
                member=member,
                licence_type="Anual FECDAS",
                issued_on=issued_on,
                expires_on=None,
                source=LicenceRecord.Source.CLUBER,
            )
        )
    return records


def confirmed_entries():
    return AuditEntry.objects.filter(action=licences.CONFIRMED_IN_BULK)


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin("secretary")


@pytest.mark.django_db
class TestCriterion:
    def test_ca_m01_44_confirms_eight_of_ten(self, secretary):
        """CA-M01-44, primera meitat: vuit caduquen el 31/12/2026, dos no canvien i el registre
        d'activitat guarda el valor anterior de cada un."""
        records = pending(10)
        chosen, others = records[:8], records[8:]
        response = admin_client(secretary).post(
            reverse(URL), {"records": [r.pk for r in chosen], "year": "2026"}
        )
        assert response.status_code == 303
        for record in chosen:
            record.refresh_from_db()
            assert record.expires_on == END_2026
        for record in others:
            record.refresh_from_db()
            assert record.expires_on is None
        rows = confirmed_entries()
        assert rows.count() == 8
        assert {e.target_id for e in rows} == {str(r.pk) for r in chosen}
        for entry in rows:
            assert entry.field == "expires_on"
            assert entry.old_value is None
            assert entry.new_value == "2026-12-31"
            assert entry.actor_account == secretary

    def test_success_message_and_the_list_shrinks(self, secretary):
        records = pending(3)
        client = admin_client(secretary)
        page = client.post(
            reverse(URL), {"records": [records[0].pk], "year": "2026"}, follow=True
        ).content.decode()
        assert "Confirmada 1 llicència amb caducitat el 31/12/2026" in page
        assert "2 registres pendents" in page
        assert f'value="{records[0].pk}"' not in page

    def test_source_and_other_fields_do_not_change(self, secretary):
        (record,) = pending(1)
        licences.confirm_in_bulk([record.pk], year=2027, by=secretary)
        record.refresh_from_db()
        assert (record.licence_type, record.issued_on, record.source) == (
            "Anual FECDAS",
            ISSUED,
            LicenceRecord.Source.CLUBER,
        )
        assert record.expires_on == datetime.date(2027, 12, 31)


@pytest.mark.django_db
class TestList:
    def test_lists_only_pending_records_of_active_persons(self, secretary):
        (open_record,) = pending(1, first="Oberta")
        (known,) = pending(1, first="Coneguda")
        LicenceRecord.objects.filter(pk=known.pk).update(expires_on=END_2026)
        (gone,) = pending(1, first="Anonima")
        Person.objects.filter(pk=gone.member.person_id).update(
            status=Person.Status.ANONYMISED, anonymous_ref="A-0001"
        )
        page = admin_client(secretary).get(reverse(URL)).content.decode()
        assert f'value="{open_record.pk}"' in page
        assert f'value="{known.pk}"' not in page
        assert f'value="{gone.pk}"' not in page
        assert f'value="{timezone.localdate().year}"' in page  # any proposat: l'actual

    def test_empty_list(self, secretary):
        page = main_of(admin_client(secretary).get(reverse(URL)).content.decode())
        assert "No hi ha cap registre de llicència pendent de confirmar." in page
        assert 'method="post"' not in page


@pytest.mark.django_db
class TestPermissions:
    @pytest.mark.parametrize("role", ["secretary", "administrator"])
    def test_managers_open_and_confirm(self, make_admin, role):  # noqa: F811
        (record,) = pending(1)
        client = admin_client(make_admin(role))
        assert client.get(reverse(URL)).status_code == 200
        client.post(reverse(URL), {"records": [record.pk], "year": "2026"})
        record.refresh_from_db()
        assert record.expires_on == END_2026

    @pytest.mark.parametrize("role", WITHOUT_P19_WRITE)
    def test_other_roles_get_not_found(self, make_admin, role):  # noqa: F811
        (record,) = pending(1)
        account = make_admin(role)
        client = admin_client(account)
        assert client.get(reverse(URL)).status_code == 404
        response = client.post(reverse(URL), {"records": [record.pk], "year": "2026"})
        assert response.status_code == 404
        with pytest.raises(Http404):
            licences.confirm_in_bulk([record.pk], year=2026, by=account)
        record.refresh_from_db()
        assert record.expires_on is None

    def test_p19_without_p4_is_not_found(self, secretary):
        (record,) = pending(1)
        remove_permission("secretary", "members.list")
        client = admin_client(secretary)
        assert client.get(reverse(URL)).status_code == 404
        assert (
            client.post(reverse(URL), {"records": [record.pk], "year": "2026"}).status_code == 404
        )
        with pytest.raises(Http404):
            licences.confirm_in_bulk([record.pk], year=2026, by=secretary)

    def test_personal_account_cannot_confirm(self, db):
        (record,) = pending(1)
        member = a_member("Personal", document=("passport", "PROVAPE0001"))
        account = Account.objects.create_personal(member.person, "personal@example.org")
        Account.objects.filter(pk=account.pk).update(status=Account.Status.ACTIVE)
        account.refresh_from_db()
        with pytest.raises(Http404):
            licences.confirm_in_bulk([record.pk], year=2026, by=account)

    def test_inactive_account_is_rejected(self, secretary):
        (record,) = pending(1)
        Account.objects.filter(pk=secretary.pk).update(status=Account.Status.DISABLED)
        with pytest.raises(InactiveAccount):
            licences.confirm_in_bulk([record.pk], year=2026, by=secretary)
        record.refresh_from_db()
        assert record.expires_on is None

    def test_only_get_and_post(self, secretary):
        assert admin_client(secretary).delete(reverse(URL)).status_code == 405


@pytest.mark.django_db
class TestOwnMember:
    def test_own_record_is_not_listed(self, make_admin):  # noqa: F811
        own_record, other = pending(2)
        own = make_admin("secretary", person=own_record.member.person)
        page = admin_client(own).get(reverse(URL)).content.decode()
        assert f'value="{own_record.pk}"' not in page
        assert f'value="{other.pk}"' in page

    def test_forged_post_is_rejected_and_recorded(self, make_admin):  # noqa: F811
        own_record, other = pending(2)
        own = make_admin("administrator", person=own_record.member.person)
        response = admin_client(own).post(
            reverse(URL), {"records": [own_record.pk, other.pk], "year": "2026"}
        )
        assert response.status_code == 200
        assert "És el teu soci" in response.content.decode()
        assert not LicenceRecord.objects.filter(expires_on__isnull=False).exists()
        assert not confirmed_entries().exists()
        attempt = AuditEntry.objects.get(action=services.OWN_MEMBER_REJECTED)
        assert attempt.actor_account == own
        assert attempt.target_id == str(own_record.member.pk)

    def test_service_rejects_own_member(self, make_admin):  # noqa: F811
        (own_record,) = pending(1)
        own = make_admin("secretary", person=own_record.member.person)
        with pytest.raises(OwnMemberChange):
            licences.confirm_in_bulk([own_record.pk], year=2026, by=own)


@pytest.mark.django_db
class TestAllOrNothing:
    def test_issue_date_after_the_year_end_rejects_the_whole_batch(self, secretary):
        early = pending(2)
        (late,) = pending(1, issued_on=datetime.date(2027, 1, 10), first="Tard")
        response = admin_client(secretary).post(
            reverse(URL), {"records": [r.pk for r in [*early, late]], "year": "2026"}
        )
        assert response.status_code == 200
        assert "Hi ha 1 registre(s) amb la data d&#x27;alta posterior al 31/12/2026" in (
            response.content.decode()
        )
        assert not LicenceRecord.objects.filter(expires_on__isnull=False).exists()
        assert not confirmed_entries().exists()

    def test_record_confirmed_meanwhile_rejects_the_whole_batch(self, secretary):
        first, second = pending(2)
        LicenceRecord.objects.filter(pk=second.pk).update(expires_on=datetime.date(2027, 6, 30))
        with pytest.raises(ValidationError):
            licences.confirm_in_bulk([first.pk, second.pk], year=2026, by=secretary)
        first.refresh_from_db()
        second.refresh_from_db()
        assert first.expires_on is None
        assert second.expires_on == datetime.date(2027, 6, 30)
        assert not confirmed_entries().exists()

    def test_known_expiry_in_the_post_is_rejected_by_the_form(self, secretary):
        (record,) = pending(1)
        LicenceRecord.objects.filter(pk=record.pk).update(expires_on=datetime.date(2027, 6, 30))
        response = admin_client(secretary).post(
            reverse(URL), {"records": [record.pk], "year": "2026"}
        )
        assert response.status_code == 200
        record.refresh_from_db()
        assert record.expires_on == datetime.date(2027, 6, 30)

    def test_anonymised_person_is_rejected(self, secretary):
        (record,) = pending(1)
        Person.objects.filter(pk=record.member.person_id).update(
            status=Person.Status.ANONYMISED, anonymous_ref="A-0002"
        )
        with pytest.raises(ValidationError):
            licences.confirm_in_bulk([record.pk], year=2026, by=secretary)
        record.refresh_from_db()
        assert record.expires_on is None

    def test_unknown_id_is_rejected(self, secretary):
        (record,) = pending(1)
        with pytest.raises(ValidationError):
            licences.confirm_in_bulk([record.pk, 999_999], year=2026, by=secretary)
        record.refresh_from_db()
        assert record.expires_on is None


@pytest.mark.django_db
class TestValidation:
    def test_nothing_selected(self, secretary):
        pending(1)
        response = admin_client(secretary).post(reverse(URL), {"year": "2026"})
        assert response.status_code == 200
        assert "Selecciona almenys un registre." in response.content.decode()
        with pytest.raises(ValidationError):
            licences.confirm_in_bulk([], year=2026, by=secretary)

    @pytest.mark.parametrize("year", ["", "abc", "0", "10000"])
    def test_invalid_year_in_the_form(self, secretary, year):
        (record,) = pending(1)
        response = admin_client(secretary).post(
            reverse(URL), {"records": [record.pk], "year": year}
        )
        assert response.status_code == 200
        record.refresh_from_db()
        assert record.expires_on is None

    @pytest.mark.parametrize("year", [0, 10000, True, "2026", 2026.0])
    def test_invalid_year_in_the_service(self, secretary, year):
        (record,) = pending(1)
        with pytest.raises(ValidationError):
            licences.confirm_in_bulk([record.pk], year=year, by=secretary)
        record.refresh_from_db()
        assert record.expires_on is None


class TestYearLimit085:
    """Decisió 085 (S-4, opció B): en confirmar en bloc només es pot posar l'any actual o el
    següent, al formulari i al servei, per evitar errors de teclat."""

    @pytest.mark.parametrize("year", [2025, 2028, 2062])
    def test_other_years_are_rejected_by_the_service(self, secretary, year):
        (record,) = pending(1)
        with pytest.raises(ValidationError) as error:
            licences.confirm_in_bulk([record.pk], year=year, by=secretary)
        assert "2026 o 2027" in " ".join(error.value.messages)
        record.refresh_from_db()
        assert record.expires_on is None

    @pytest.mark.parametrize("year", [2026, 2027])
    def test_this_year_and_the_next_are_accepted(self, secretary, year):
        (record,) = pending(1)
        assert licences.confirm_in_bulk([record.pk], year=year, by=secretary) == 1

    def test_the_form_says_which_years_and_rejects_the_rest(self, secretary):
        (record,) = pending(1)
        client = admin_client(secretary)
        page = client.get(reverse(URL)).content.decode()
        assert 'min="2026"' in page and 'max="2027"' in page
        response = client.post(reverse(URL), {"records": [record.pk], "year": "2062"})
        assert response.status_code == 200
        record.refresh_from_db()
        assert record.expires_on is None
