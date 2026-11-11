"""Editar les dades d'un soci (P5) i corregir la data d'alta (P6) des de la fitxa (T-M01-15b;
HU-M01-07, RN-M01-22, RN-RP-21, S-M01-22).

Permisos al servidor per rol (configuració inicial de la 059), per camp (P4 sencer, C2) i per
objecte (conflicte d'interès), historial i registre d'activitat amb el valor anterior. Fora
d'aquestes proves, perquè no s'implementen: el número de soci, la data de naixement (T-M01-33)
i els camps opcionals de la P-58. Només dades inventades.
"""

import datetime

import pytest
from django.db import DatabaseError, connection, transaction
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import persons
from apps.core.models import AuditEntry, Person, Role, RolePermission
from apps.core.permission_catalog import SCOPE_ALL
from apps.core.tests.conftest import (
    main_of,
    make_admin,  # noqa: F401 (fixture)
)
from apps.members import member_edit, services
from apps.members.models import Member, MemberJoinDateChange, MembershipType
from apps.members.services import InactiveAccount, OwnMemberChange
from apps.members.tests.test_roster import admin_client, remove_permission

EDIT = "administration:member_edit"
JOIN_DATE = "administration:member_join_date"
DETAIL = "administration:member_detail"
EDITORS = ["secretary", "administrator"]
NOT_EDITORS = [
    "treasurer",
    "president",
    "board",
    "instructor",
    "courses_manager",
    "equipment_manager",
    "history_department",
]
JOINED = datetime.date(2019, 3, 12)
REASON = "Motiu inventat de proves"
DNI = "12345678Z"  # lletra correcta (inventat)
OTHER_DNI = "87654321X"  # lletra correcta (inventat)


def a_member(first="Anna", *, document=("passport", "PROVA0001"), **person):
    p = Person.objects.create(
        first_name=first,
        last_name="Mero",
        contact_email="anna.mero@example.org",
        phone="+34600111222",
        address="Carrer Inventat 1",
        id_document_type=document[0],
        id_document_number=document[1],
        origin=Person.Origin.IN_PERSON,
        **person,
    )
    return Member.objects.create(
        person=p,
        member_number=Member.objects.count() + 100,
        type=MembershipType.objects.get(code="full"),
        status=Member.Status.ACTIVE,
        joined_on=JOINED,
    )


def data(member, **changes):
    p = member.person
    values = {
        "first_name": p.first_name,
        "last_name": p.last_name,
        "contact_email": p.contact_email,
        "phone": p.phone,
        "id_document": p.id_document_number,
        "address": p.address,
    }
    return {**values, **changes}


def entries(action, target):
    return list(
        AuditEntry.objects.filter(
            action=action, target_type=target._meta.label_lower, target_id=str(target.pk)
        ).order_by("field")
    )


def give(role, code, scope=SCOPE_ALL):
    RolePermission.objects.update_or_create(
        role=Role.objects.get(code=role),
        permission_code=code,
        defaults={"scope": scope},
    )


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin("secretary")


# --- P5 i P6 per rol (059; RN-RP-21) ---------------------------------------------------------


@pytest.mark.django_db
class TestRoles:
    @pytest.mark.parametrize("role", EDITORS)
    @pytest.mark.parametrize("name", [EDIT, JOIN_DATE])
    def test_editors_open_the_forms(self, make_admin, role, name):  # noqa: F811
        member = a_member()
        response = admin_client(make_admin(role)).get(reverse(name, args=[member.pk]))
        assert response.status_code == 200
        assert 'method="post"' in response.content.decode()

    @pytest.mark.parametrize("role", NOT_EDITORS)
    @pytest.mark.parametrize("name", [EDIT, JOIN_DATE])
    def test_others_get_not_found_also_by_post(self, make_admin, role, name):  # noqa: F811
        member = a_member()
        client = admin_client(make_admin(role))
        url = reverse(name, args=[member.pk])
        assert client.get(url).status_code == 404
        post = {**data(member, first_name="Canviat"), "joined_on": "2001-01-01"}
        assert client.post(url, post).status_code == 404
        member.refresh_from_db()
        assert member.person.first_name == "Anna"
        assert member.joined_on == JOINED

    @pytest.mark.parametrize("name", [EDIT, JOIN_DATE])
    def test_unknown_member_is_not_found(self, secretary, name):
        assert admin_client(secretary).get(reverse(name, args=[999_999])).status_code == 404

    @pytest.mark.parametrize("code", ["members.edit", "members.edit_join_date"])
    def test_edit_without_list_is_not_found(self, secretary, code):
        """RN-RP-21: P5 i P6 demanen P4. Si la matriu es manipulés, el servidor ho comprova."""
        member = a_member()
        remove_permission("secretary", "members.list")
        name = EDIT if code == "members.edit" else JOIN_DATE
        assert admin_client(secretary).get(reverse(name, args=[member.pk])).status_code == 404
        assert member_edit.editable_fields(secretary) == ()
        assert not member_edit.can_correct_join_date(secretary)

    def test_personal_account_has_no_fields(self, db):
        member = a_member()
        account = Account.objects.create_personal(member.person, "anna.mero@example.org")
        Account.objects.filter(pk=account.pk).update(status=Account.Status.ACTIVE)
        account.refresh_from_db()
        assert member_edit.editable_fields(account) == ()
        other = a_member("Berta", document=("", ""))
        with pytest.raises(Http404):
            member_edit.edit_member_data(other, by=account, fields={"first_name": "X"})


# --- Camps segons el que es pot veure (roster.Visibility) ----------------------------------


@pytest.mark.django_db
class TestFields:
    def test_editor_with_c2_edits_everything(self, secretary):
        assert member_edit.editable_fields(secretary) == (
            "first_name",
            "last_name",
            "contact_email",
            "phone",
            "landline",  # camps opcionals de la 072 (P-58)
            "id_document_type",
            "id_document_number",
            "address",
            "postal_code",
            "city",
            "province",
        )

    def test_without_c2_document_and_address_are_ignored(self, secretary):
        member = a_member()
        remove_permission("secretary", "members.field.identity")
        client = admin_client(secretary)
        page = client.get(reverse(EDIT, args=[member.pk])).content.decode()
        assert "PROVA0001" not in page and "Carrer Inventat" not in page
        client.post(
            reverse(EDIT, args=[member.pk]),
            data(member, first_name="Anna Maria", id_document=DNI, address="Carrer Fals 2"),
        )
        person = Person.objects.get(pk=member.person_id)
        assert person.first_name == "Anna Maria"
        assert person.id_document_number == "PROVA0001"
        assert person.address == "Carrer Inventat 1"

    def test_service_rejects_fields_the_account_cannot_edit(self, secretary):
        member = a_member()
        remove_permission("secretary", "members.field.identity")
        with pytest.raises(Http404):
            member_edit.edit_member_data(member, by=secretary, fields={"address": "Carrer Fals 2"})
        assert Person.objects.get(pk=member.person_id).address == "Carrer Inventat 1"

    def test_minimal_data_edits_only_the_name_and_not_the_join_date(self, make_admin):  # noqa: F811
        """Si la matriu donés P5 i P6 a «dades mínimes» (tresorer), no veu ni edita el contacte
        ni la data d'alta."""
        give("treasurer", "members.edit")
        give("treasurer", "members.edit_join_date")
        treasurer = make_admin("treasurer")
        member = a_member()
        assert member_edit.editable_fields(treasurer) == ("first_name", "last_name")
        client = admin_client(treasurer)
        page = client.get(reverse(EDIT, args=[member.pk])).content.decode()
        assert "anna.mero@example.org" not in page and "+34600111222" not in page
        client.post(reverse(EDIT, args=[member.pk]), data(member, contact_email="x@example.org"))
        assert Person.objects.get(pk=member.person_id).contact_email == "anna.mero@example.org"
        assert client.get(reverse(JOIN_DATE, args=[member.pk])).status_code == 404


# --- P5: editar les dades, amb el valor anterior al registre --------------------------------


@pytest.mark.django_db
class TestEditData:
    def test_saves_and_records_each_field_with_the_old_value(self, secretary):
        member = a_member()
        response = admin_client(secretary).post(
            reverse(EDIT, args=[member.pk]),
            data(member, last_name="Mero Vidal", phone="600 999 888", id_document=DNI.lower()),
        )
        assert response.status_code == 303
        assert response["Location"] == reverse(DETAIL, args=[member.pk])
        person = Person.objects.get(pk=member.person_id)
        assert (person.last_name, person.phone) == ("Mero Vidal", "600999888")
        assert (person.id_document_type, person.id_document_number) == ("dni", DNI)
        recorded = {e.field: (e.old_value, e.new_value) for e in entries(persons.UPDATED, person)}
        assert recorded == {
            "last_name": ("Mero", "Mero Vidal"),
            "phone": ("+34600111222", "600999888"),
            "id_document_type": ("passport", "dni"),
            "id_document_number": ("PROVA0001", DNI),
        }
        assert {e.actor_account_id for e in entries(persons.UPDATED, person)} == {secretary.pk}

    def test_no_change_writes_nothing(self, secretary):
        member = a_member()
        client = admin_client(secretary)
        client.post(reverse(EDIT, args=[member.pk]), data(member))
        assert entries(persons.UPDATED, member.person) == []
        page = client.get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert "No hi havia cap canvi per desar." in page

    def test_current_passport_can_stay(self, secretary):
        member = a_member()
        admin_client(secretary).post(
            reverse(EDIT, args=[member.pk]), data(member, first_name="Anna Maria")
        )
        person = Person.objects.get(pk=member.person_id)
        assert (person.first_name, person.id_document_number) == ("Anna Maria", "PROVA0001")

    @pytest.mark.parametrize(
        ("value", "message"),
        [
            ("12345678A", "Escriu un DNI o un NIE vàlid, amb la lletra."),
            # 079 (A-08): només es pot buidar el d'un menor; aquesta persona no té data.
            ("", "El document només es pot treure a una persona menor d&#x27;edat."),
        ],
    )
    def test_invalid_document_is_rejected(self, secretary, value, message):
        member = a_member()
        response = admin_client(secretary).post(
            reverse(EDIT, args=[member.pk]), data(member, id_document=value)
        )
        assert response.status_code == 200
        assert message in response.content.decode()
        assert Person.objects.get(pk=member.person_id).id_document_number == "PROVA0001"

    def test_document_of_another_person_is_rejected_without_merging(self, secretary):
        a_member("Berta", document=("dni", OTHER_DNI))
        member = a_member()
        response = admin_client(secretary).post(
            reverse(EDIT, args=[member.pk]), data(member, id_document=OTHER_DNI, last_name="Nou")
        )
        assert response.status_code == 200
        assert "Aquest document ja és d&#x27;una altra persona" in response.content.decode()
        person = Person.objects.get(pk=member.person_id)
        assert (person.id_document_number, person.last_name) == ("PROVA0001", "Mero")
        assert entries(persons.UPDATED, person) == []

    @pytest.mark.parametrize(
        "changes",
        [{"first_name": ""}, {"contact_email": "no-és-un-correu"}, {"phone": "123"}],
    )
    def test_required_and_format_rules(self, secretary, changes):
        member = a_member()
        response = admin_client(secretary).post(
            reverse(EDIT, args=[member.pk]), data(member, **changes)
        )
        assert response.status_code == 200
        assert entries(persons.UPDATED, member.person) == []

    def test_anonymised_person_is_not_edited(self, secretary):
        member = a_member(document=("", ""))
        Person.objects.filter(pk=member.person_id).update(
            status=Person.Status.ANONYMISED, anonymous_ref="A-0001"
        )
        client = admin_client(secretary)
        assert "anonimitzades" in client.get(reverse(EDIT, args=[member.pk])).content.decode()
        response = client.post(reverse(EDIT, args=[member.pk]), data(member, first_name="Nou"))
        assert response.status_code == 200
        assert Person.objects.get(pk=member.person_id).first_name == "Anna"

    def test_inactive_account_is_rejected(self, secretary):
        member = a_member()
        Account.objects.filter(pk=secretary.pk).update(status=Account.Status.DISABLED)
        with pytest.raises(InactiveAccount):
            member_edit.edit_member_data(member, by=secretary, fields={"first_name": "X"})


# --- P6: corregir la data d'alta (RN-M01-22; historial i registre, CA-M01-08) ---------------


@pytest.mark.django_db
class TestJoinDate:
    def post(self, account, member, joined_on, approximate=False):
        body = {"joined_on": joined_on, "reason": REASON}  # 079 (A-23): motiu obligatori
        if approximate:
            body["approximate"] = "on"
        return admin_client(account).post(reverse(JOIN_DATE, args=[member.pk]), body)

    def test_correction_keeps_the_old_value_in_history_and_audit(self, secretary):
        member = a_member()
        response = self.post(secretary, member, "1987-05-01", approximate=True)
        assert response.status_code == 303
        member.refresh_from_db()
        assert (member.joined_on, member.joined_on_is_approximate) == (
            datetime.date(1987, 5, 1),
            True,
        )
        change = MemberJoinDateChange.objects.get(member=member)
        assert (change.from_joined_on, change.from_is_approximate) == (JOINED, False)
        assert (change.to_joined_on, change.to_is_approximate) == (datetime.date(1987, 5, 1), True)
        assert change.actor_account == secretary
        recorded = {
            e.field: (e.old_value, e.new_value)
            for e in entries(member_edit.JOIN_DATE_CORRECTED, member)
        }
        assert recorded == {
            "joined_on": ("2019-03-12", "1987-05-01"),
            "joined_on_is_approximate": (False, True),
        }
        page = admin_client(secretary).get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert "Correccions de la data d'alta" in page
        assert "01/05/1987 (abans 12/03/2019)" in page

    def test_only_the_approximate_mark_also_counts(self, secretary):
        member = a_member()
        self.post(secretary, member, JOINED.isoformat(), approximate=True)
        assert MemberJoinDateChange.objects.filter(member=member).count() == 1

    def test_no_change_writes_nothing(self, secretary):
        member = a_member()
        self.post(secretary, member, JOINED.isoformat())
        assert not MemberJoinDateChange.objects.exists()
        assert entries(member_edit.JOIN_DATE_CORRECTED, member) == []

    def test_future_date_is_rejected(self, secretary):
        member = a_member()
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        response = self.post(secretary, member, tomorrow.isoformat())
        assert "La data d&#x27;alta no pot ser posterior a avui." in response.content.decode()
        member.refresh_from_db()
        assert member.joined_on == JOINED

    def test_not_after_the_leaving_date(self, secretary):
        member = a_member()
        Member.objects.filter(pk=member.pk).update(
            status=Member.Status.LEFT, left_on=datetime.date(2022, 6, 30)
        )
        response = self.post(secretary, member, "2023-01-01")
        assert "posterior a la data de baixa" in response.content.decode()
        assert not MemberJoinDateChange.objects.exists()

    def test_invalid_date_is_rejected(self, secretary):
        member = a_member()
        response = self.post(secretary, member, "2026-02-30")
        assert response.status_code == 200
        assert not MemberJoinDateChange.objects.exists()

    def test_history_is_append_only_also_with_sql(self, secretary):
        member = a_member()
        self.post(secretary, member, "1990-01-01")
        for sql in (
            "UPDATE members_memberjoindatechange SET to_is_approximate = true",
            "DELETE FROM members_memberjoindatechange",
        ):
            with (
                pytest.raises(DatabaseError, match="no es poden modificar"),
                transaction.atomic(),
                connection.cursor() as cursor,
            ):
                cursor.execute(sql)
        assert MemberJoinDateChange.objects.count() == 1

    def test_minimal_view_does_not_see_the_corrections(self, secretary, make_admin):  # noqa: F811
        member = a_member()
        self.post(secretary, member, "1990-01-01")
        page = admin_client(make_admin("treasurer")).get(reverse(DETAIL, args=[member.pk]))
        assert "Correccions de la data" not in page.content.decode()


# --- Conflicte d'interès (S-M01-22): ningú no edita el seu propi soci ----------------------


@pytest.mark.django_db
class TestOwnMember:
    @pytest.mark.parametrize("name", [EDIT, JOIN_DATE])
    def test_form_is_not_offered(self, make_admin, name):  # noqa: F811
        member = a_member()
        own = make_admin("secretary", person=member.person)
        page = main_of(admin_client(own).get(reverse(name, args=[member.pk])).content.decode())
        assert "És el teu soci" in page
        assert 'method="post"' not in page

    @pytest.mark.parametrize("name", [EDIT, JOIN_DATE])
    def test_post_is_rejected_and_recorded(self, make_admin, name):  # noqa: F811
        member = a_member()
        own = make_admin("administrator", person=member.person)
        body = {
            **data(member, first_name="Jo mateixa"),
            "joined_on": "1980-01-01",
            "reason": REASON,
        }
        response = admin_client(own).post(reverse(name, args=[member.pk]), body)
        assert response.status_code == 303
        member.refresh_from_db()
        assert member.person.first_name == "Anna"
        assert member.joined_on == JOINED
        (attempt,) = entries(services.OWN_MEMBER_REJECTED, member)
        assert attempt.actor_account == own

    def test_invalid_post_is_also_recorded(self, make_admin):  # noqa: F811
        member = a_member()
        own = make_admin("secretary", person=member.person)
        admin_client(own).post(reverse(EDIT, args=[member.pk]), {"first_name": ""})
        assert len(entries(services.OWN_MEMBER_REJECTED, member)) == 1

    def test_service_rejects_own_member(self, make_admin):  # noqa: F811
        member = a_member()
        own = make_admin("secretary", person=member.person)
        with pytest.raises(OwnMemberChange):
            member_edit.correct_join_date(
                member,
                by=own,
                joined_on=datetime.date(1980, 1, 1),
                approximate=False,
                reason=REASON,
            )

    def test_detail_hides_the_links_for_own_member(self, make_admin):  # noqa: F811
        member = a_member()
        own = make_admin("secretary", person=member.person)
        page = admin_client(own).get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert reverse(EDIT, args=[member.pk]) not in page
        assert "no pots editar-ne les dades" in page


# --- Enllaços de la fitxa (només ajuda: el control és al servidor) ------------------------


@pytest.mark.django_db
class TestDetailLinks:
    def test_editor_sees_both_links(self, secretary):
        member = a_member()
        page = admin_client(secretary).get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert reverse(EDIT, args=[member.pk]) in page
        assert reverse(JOIN_DATE, args=[member.pk]) in page

    def test_treasurer_sees_none(self, make_admin):  # noqa: F811
        member = a_member()
        page = admin_client(make_admin("treasurer")).get(reverse(DETAIL, args=[member.pk]))
        assert reverse(EDIT, args=[member.pk]) not in page.content.decode()
        assert reverse(JOIN_DATE, args=[member.pk]) not in page.content.decode()
