"""Registre mínim de llicència a la fitxa del soci (T-M01-23; RN-M01-29, P19, S-M01-22).

Permisos al servidor per rol (configuració inicial de la 059: P19 sencer per a secretaria i
administrador, «Cons.» per a tresorer i responsable de cursos i sortides) i per objecte (el
registre ha de ser del soci de l'URL; conflicte d'interès), validació de dates
(`expires_on ≥ issued_on`) i registre d'activitat amb el valor anterior. Fora d'aquestes proves,
perquè no són d'aquesta tasca: els serveis de lectura (T-M01-30) i el text de la caducitat
desconeguda (T-M01-34). Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse

from apps.accounts.models import Account
from apps.core.models import AuditEntry, Person
from apps.core.permission_catalog import SCOPE_READ
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import licences, services
from apps.members.models import LicenceRecord
from apps.members.services import InactiveAccount, OwnMemberChange
from apps.members.tests.test_member_edit import a_member, give
from apps.members.tests.test_roster import admin_client, remove_permission

ADD = "administration:licence_add"
EDIT = "administration:licence_edit"
DETAIL = "administration:member_detail"
MANAGERS = ["secretary", "administrator"]
READERS_WITH_DETAIL = ["treasurer"]  # P19 «Cons.» i P4 (dades mínimes)
WITHOUT_P19 = ["president", "board", "instructor", "equipment_manager", "history_department"]
ISSUED = datetime.date(2026, 1, 15)
EXPIRES = datetime.date(2026, 12, 31)


def a_record(member, *, expires_on=EXPIRES, source=LicenceRecord.Source.MANUAL):
    return LicenceRecord.objects.create(
        member=member,
        licence_type="Anual FECDAS",
        issued_on=ISSUED,
        expires_on=expires_on,
        source=source,
    )


def body(**changes):
    values = {"licence_type": "Anual FECDAS", "issued_on": "2026-01-15", "expires_on": "2026-12-31"}
    return {**values, **changes}


def entries(action, target=None):
    rows = AuditEntry.objects.filter(action=action)
    if target is not None:
        rows = rows.filter(target_type=target._meta.label_lower, target_id=str(target.pk))
    return {e.field: (e.old_value, e.new_value) for e in rows}


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin("secretary")


# --- Permisos per rol (059, P19; RN-RP-21) -------------------------------------------------


@pytest.mark.django_db
class TestRoles:
    @pytest.mark.parametrize("role", MANAGERS)
    def test_managers_see_the_section_and_the_links(self, make_admin, role):  # noqa: F811
        member = a_member()
        record = a_record(member)
        page = admin_client(make_admin(role)).get(reverse(DETAIL, args=[member.pk])).content
        page = page.decode()
        assert "Anual FECDAS" in page and "31/12/2026" in page
        assert reverse(ADD, args=[member.pk]) in page
        assert reverse(EDIT, args=[member.pk, record.pk]) in page

    @pytest.mark.parametrize("role", MANAGERS)
    def test_managers_open_the_forms(self, make_admin, role):  # noqa: F811
        member = a_member()
        record = a_record(member)
        client = admin_client(make_admin(role))
        for url in (reverse(ADD, args=[member.pk]), reverse(EDIT, args=[member.pk, record.pk])):
            response = client.get(url)
            assert response.status_code == 200
            assert 'method="post"' in response.content.decode()

    @pytest.mark.parametrize("role", READERS_WITH_DETAIL)
    def test_treasurer_only_consults(self, make_admin, role):  # noqa: F811
        member = a_member()
        record = a_record(member)
        client = admin_client(make_admin(role))
        page = client.get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert "Anual FECDAS" in page
        assert reverse(ADD, args=[member.pk]) not in page
        assert reverse(EDIT, args=[member.pk, record.pk]) not in page
        assert client.get(reverse(ADD, args=[member.pk])).status_code == 404
        assert client.post(reverse(ADD, args=[member.pk]), body()).status_code == 404
        edit = reverse(EDIT, args=[member.pk, record.pk])
        assert client.post(edit, body(licence_type="Canviada")).status_code == 404
        assert LicenceRecord.objects.get().licence_type == "Anual FECDAS"

    @pytest.mark.parametrize("role", WITHOUT_P19)
    def test_roles_without_p19_get_not_found(self, make_admin, role):  # noqa: F811
        member = a_member()
        record = a_record(member)
        client = admin_client(make_admin(role))
        assert client.post(reverse(ADD, args=[member.pk]), body()).status_code == 404
        edit = reverse(EDIT, args=[member.pk, record.pk])
        assert client.post(edit, body(licence_type="Canviada")).status_code == 404
        assert LicenceRecord.objects.count() == 1

    def test_courses_manager_consults_but_has_no_detail(self, make_admin):  # noqa: F811
        """P19 «Cons.» sense P4: no hi ha fitxa per a ell (la seva lectura és la T-M01-30)."""
        member = a_member()
        a_record(member)
        client = admin_client(make_admin("courses_manager"))
        assert client.get(reverse(DETAIL, args=[member.pk])).status_code == 404
        assert client.post(reverse(ADD, args=[member.pk]), body()).status_code == 404
        assert LicenceRecord.objects.count() == 1

    def test_without_p19_the_detail_has_no_licence_section(self, secretary):
        member = a_member()
        a_record(member)
        remove_permission("secretary", licences.MANAGE)
        page = admin_client(secretary).get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert "Anual FECDAS" not in page and 'id="llicencia-titol"' not in page
        assert admin_client(secretary).get(reverse(ADD, args=[member.pk])).status_code == 404

    def test_read_scope_cannot_write_even_by_service(self, secretary):
        """Si la matriu deixés la secretaria en «Cons.» (fila P19 quan el 06 entri, 052)."""
        give("secretary", licences.MANAGE, SCOPE_READ)
        member = a_member()
        assert licences.can_view(secretary) and not licences.can_manage(secretary)
        assert admin_client(secretary).get(reverse(ADD, args=[member.pk])).status_code == 404
        with pytest.raises(Http404):
            licences.add_record(
                member, by=secretary, licence_type="X", issued_on=ISSUED, expires_on=EXPIRES
            )

    def test_p19_without_p4_is_not_found(self, secretary):
        member = a_member()
        remove_permission("secretary", "members.list")
        assert not licences.can_manage(secretary)
        assert admin_client(secretary).get(reverse(ADD, args=[member.pk])).status_code == 404

    def test_personal_account_cannot_manage(self, db):
        member = a_member()
        account = Account.objects.create_personal(member.person, "anna.mero@example.org")
        Account.objects.filter(pk=account.pk).update(status=Account.Status.ACTIVE)
        account.refresh_from_db()
        other = a_member("Berta", document=("", ""))
        assert not licences.can_view(account)
        with pytest.raises(Http404):
            licences.add_record(
                other, by=account, licence_type="X", issued_on=ISSUED, expires_on=EXPIRES
            )

    def test_unknown_member_is_not_found(self, secretary):
        assert admin_client(secretary).get(reverse(ADD, args=[999_999])).status_code == 404

    def test_record_of_another_member_is_not_found(self, secretary):
        """Per objecte: el registre ha de ser del soci de l'URL."""
        member, other = a_member(), a_member("Berta", document=("", ""))
        record = a_record(other)
        url = reverse(EDIT, args=[member.pk, record.pk])
        client = admin_client(secretary)
        assert client.get(url).status_code == 404
        assert client.post(url, body(licence_type="Canviada")).status_code == 404
        assert LicenceRecord.objects.get().licence_type == "Anual FECDAS"


# --- Afegir (origen manual, registre d'activitat) -------------------------------------------


@pytest.mark.django_db
class TestAdd:
    def test_adds_a_manual_record_and_records_it(self, secretary):
        member = a_member()
        response = admin_client(secretary).post(reverse(ADD, args=[member.pk]), body())
        assert response.status_code == 303
        assert response["Location"] == reverse(DETAIL, args=[member.pk])
        record = LicenceRecord.objects.get()
        assert (record.member, record.source, record.import_batch) == (member, "manual", None)
        assert (record.licence_type, record.issued_on, record.expires_on) == (
            "Anual FECDAS",
            ISSUED,
            EXPIRES,
        )
        assert entries(licences.ADDED, record) == {
            "licence_type": (None, "Anual FECDAS"),
            "issued_on": (None, "2026-01-15"),
            "expires_on": (None, "2026-12-31"),
        }
        actors = set(AuditEntry.objects.filter(action=licences.ADDED).values_list("actor_account"))
        assert actors == {(secretary.pk,)}

    def test_type_is_stripped_and_required(self, secretary):
        member = a_member()
        client = admin_client(secretary)
        client.post(reverse(ADD, args=[member.pk]), body(licence_type="  Anual  "))
        assert LicenceRecord.objects.get().licence_type == "Anual"
        response = client.post(reverse(ADD, args=[member.pk]), body(licence_type="   "))
        assert response.status_code == 200
        assert LicenceRecord.objects.count() == 1

    def test_anonymised_person_gets_no_record(self, secretary):
        member = a_member(document=("", ""))
        Person.objects.filter(pk=member.person_id).update(
            status=Person.Status.ANONYMISED, anonymous_ref="A-0001"
        )
        client = admin_client(secretary)
        assert "anonimitzades" in client.get(reverse(ADD, args=[member.pk])).content.decode()
        response = client.post(reverse(ADD, args=[member.pk]), body())
        assert response.status_code == 200
        assert not LicenceRecord.objects.exists()

    def test_inactive_account_is_rejected(self, secretary):
        member = a_member()
        Account.objects.filter(pk=secretary.pk).update(status=Account.Status.DISABLED)
        with pytest.raises(InactiveAccount):
            licences.add_record(
                member, by=secretary, licence_type="X", issued_on=ISSUED, expires_on=EXPIRES
            )
        assert not LicenceRecord.objects.exists()


# --- Prova de dates (fila de la T-M01-23; addenda de la 058) --------------------------------


@pytest.mark.django_db
class TestDates:
    @pytest.mark.parametrize(
        ("issued", "expires", "message"),
        [
            ("2026-06-01", "2026-05-31", "no pot ser anterior a la data d"),
            ("2026-06-01", "", "Cal la data de caducitat."),
            ("", "2026-12-31", "obligatori"),
            ("2026-02-30", "2026-12-31", "Escriu una data vàlida"),
            ("2026-01-15", "31/02/2027", "Escriu una data vàlida"),
        ],
    )
    def test_invalid_dates_are_rejected_on_add(self, secretary, issued, expires, message):
        member = a_member()
        response = admin_client(secretary).post(
            reverse(ADD, args=[member.pk]), body(issued_on=issued, expires_on=expires)
        )
        assert response.status_code == 200
        assert message in response.content.decode()
        assert not LicenceRecord.objects.exists()
        assert not AuditEntry.objects.filter(action=licences.ADDED).exists()

    def test_same_day_is_accepted(self, secretary):
        member = a_member()
        admin_client(secretary).post(
            reverse(ADD, args=[member.pk]), body(issued_on="2026-06-01", expires_on="01/06/2026")
        )
        record = LicenceRecord.objects.get()
        assert record.issued_on == record.expires_on == datetime.date(2026, 6, 1)

    @pytest.mark.parametrize(
        ("issued", "expires"),
        [
            (datetime.date(2026, 6, 1), datetime.date(2026, 5, 31)),
            (datetime.date(2026, 6, 1), None),
            (datetime.datetime(2026, 6, 1, 10, 0), EXPIRES),
            (ISSUED, datetime.datetime(2026, 12, 31, 10, 0)),
            ("2026-06-01", EXPIRES),
        ],
    )
    def test_service_rejects_invalid_dates(self, secretary, issued, expires):
        """El servei ho torna a comprovar: no depèn del formulari."""
        member = a_member()
        with pytest.raises(ValidationError):
            licences.add_record(
                member, by=secretary, licence_type="X", issued_on=issued, expires_on=expires
            )
        assert not LicenceRecord.objects.exists()

    def test_correction_cannot_put_expiry_before_issue(self, secretary):
        member = a_member()
        record = a_record(member)
        response = admin_client(secretary).post(
            reverse(EDIT, args=[member.pk, record.pk]), body(issued_on="2027-01-01")
        )
        assert response.status_code == 200
        assert "no pot ser anterior a la data d" in response.content.decode()
        record.refresh_from_db()
        assert record.issued_on == ISSUED
        with pytest.raises(ValidationError):
            licences.correct_record(
                record,
                by=secretary,
                licence_type="Anual FECDAS",
                issued_on=ISSUED,
                expires_on=datetime.date(2025, 12, 31),
            )
        assert entries(licences.CORRECTED) == {}

    def test_known_expiry_cannot_be_emptied(self, secretary):
        member = a_member()
        record = a_record(member)
        response = admin_client(secretary).post(
            reverse(EDIT, args=[member.pk, record.pk]), body(expires_on="")
        )
        assert response.status_code == 200
        with pytest.raises(ValidationError):
            licences.correct_record(
                record, by=secretary, licence_type="X", issued_on=ISSUED, expires_on=None
            )
        record.refresh_from_db()
        assert record.expires_on == EXPIRES

    def test_unknown_expiry_of_a_cluber_record_can_stay_empty(self, secretary):
        """Registre de Cluber sense caducitat (058): es pot corregir el tipus sense inventar-la.
        L'origen no canvia."""
        member = a_member()
        record = a_record(member, expires_on=None, source=LicenceRecord.Source.CLUBER)
        client = admin_client(secretary)
        page = client.get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert "Anual FECDAS" in page and "Cluber" in page
        response = client.post(
            reverse(EDIT, args=[member.pk, record.pk]),
            body(licence_type="Anual", expires_on=""),
        )
        assert response.status_code == 303
        record.refresh_from_db()
        assert (record.licence_type, record.expires_on, record.source) == ("Anual", None, "cluber")
        assert entries(licences.CORRECTED, record) == {
            "licence_type": ("Anual FECDAS", "Anual"),
        }


# --- Corregir (valor anterior al registre d'activitat) --------------------------------------


@pytest.mark.django_db
class TestCorrect:
    def test_records_each_changed_field_with_the_old_value(self, secretary):
        member = a_member()
        record = a_record(member)
        response = admin_client(secretary).post(
            reverse(EDIT, args=[member.pk, record.pk]),
            body(licence_type="Anual FECDAS ampliada", expires_on="2027-01-14"),
        )
        assert response.status_code == 303
        record.refresh_from_db()
        assert (record.licence_type, record.expires_on) == (
            "Anual FECDAS ampliada",
            datetime.date(2027, 1, 14),
        )
        assert entries(licences.CORRECTED, record) == {
            "licence_type": ("Anual FECDAS", "Anual FECDAS ampliada"),
            "expires_on": ("2026-12-31", "2027-01-14"),
        }

    def test_no_change_writes_nothing(self, secretary):
        member = a_member()
        record = a_record(member)
        client = admin_client(secretary)
        response = client.post(reverse(EDIT, args=[member.pk, record.pk]), body())
        assert response.status_code == 303
        assert entries(licences.CORRECTED) == {}
        page = client.get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert "No hi havia cap canvi per desar." in page

    def test_nothing_is_deleted(self, secretary):
        """RN-M01-36: no hi ha cap ruta ni servei per esborrar un registre."""
        member = a_member()
        record = a_record(member)
        client = admin_client(secretary)
        assert client.delete(reverse(EDIT, args=[member.pk, record.pk])).status_code == 405
        assert LicenceRecord.objects.filter(pk=record.pk).exists()
        assert not hasattr(licences, "delete_record")


# --- Conflicte d'interès (S-M01-22, regla protegida) ----------------------------------------


@pytest.mark.django_db
class TestOwnMember:
    def test_form_and_links_are_not_offered(self, make_admin):  # noqa: F811
        member = a_member()
        record = a_record(member)
        own = make_admin("secretary", person=member.person)
        client = admin_client(own)
        page = client.get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert "Anual FECDAS" in page
        assert reverse(ADD, args=[member.pk]) not in page
        assert reverse(EDIT, args=[member.pk, record.pk]) not in page
        page = client.get(reverse(ADD, args=[member.pk])).content.decode()
        assert "És el teu soci" in page and 'method="post"' not in page

    @pytest.mark.parametrize("edit", [False, True])
    def test_post_is_rejected_and_recorded(self, make_admin, edit):  # noqa: F811
        member = a_member()
        record = a_record(member)
        own = make_admin("administrator", person=member.person)
        url = reverse(EDIT, args=[member.pk, record.pk]) if edit else reverse(ADD, args=[member.pk])
        response = admin_client(own).post(url, body(licence_type="Meva"))
        assert response.status_code == 303
        assert list(LicenceRecord.objects.values_list("licence_type", flat=True)) == [
            "Anual FECDAS"
        ]
        attempt = AuditEntry.objects.get(action=services.OWN_MEMBER_REJECTED)
        assert attempt.actor_account == own
        assert attempt.target_id == str(member.pk)

    def test_service_rejects_own_member(self, make_admin):  # noqa: F811
        member = a_member()
        own = make_admin("secretary", person=member.person)
        with pytest.raises(OwnMemberChange):
            licences.add_record(
                member, by=own, licence_type="X", issued_on=ISSUED, expires_on=EXPIRES
            )
        assert not LicenceRecord.objects.exists()
