"""Registre d'activitat immutable (T-M01-07; spec 00, HU-14, CA-14.1 a CA-14.6, RN-50 a RN-53;
RN-RP-08 i RN-RP-15). Només dades inventades."""

import json
from datetime import UTC, date, datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.db.models import ProtectedError
from django.urls import reverse

from apps.accounts import totp
from apps.accounts.models import Account, RecoveryCode, TotpDevice
from apps.accounts.tests.test_totp import ADMIN_CODE, ENROL, code_for, enrolled, password_step
from apps.core import audit
from apps.core.models import AccountRole, AuditEntry, ImmutableAuditError, Person, Role
from apps.core.roles import assign_role, deactivate_admin_account, remove_role, reset_totp
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
R = Role.Code
A = audit.Action

PERSONAL_LOGIN = "accounts:login"


def entries(action):
    return list(AuditEntry.objects.filter(action=action))


def only(action):
    found = entries(action)
    assert len(found) == 1, found
    return found[0]


def as_text(queryset=None):
    """Tot el registre com a text, per buscar-hi valors que no hi han de ser."""
    rows = (queryset or AuditEntry.objects.all()).values()
    return json.dumps(list(rows), default=str)


@pytest.fixture
def entry(admin_account):
    return audit.record(
        A.LOGOUT, actor=admin_account, target=admin_account, details={"area": "admin"}
    )


class TestImmutableInTheOrm:
    # CA-14.3 i RN-51: cap camí de l'ORM no modifica ni esborra una entrada.

    def test_saving_an_existing_entry_fails(self, entry):
        entry.action = "auth.una_altra_cosa"
        with pytest.raises(ImmutableAuditError):
            entry.save()
        entry.refresh_from_db()
        assert entry.action == A.LOGOUT

    def test_deleting_an_entry_fails(self, entry):
        with pytest.raises(ImmutableAuditError):
            entry.delete()
        assert AuditEntry.objects.filter(pk=entry.pk).exists()

    @pytest.mark.parametrize(
        "operation",
        [
            lambda qs, e: qs.update(action="x"),
            lambda qs, e: qs.delete(),
            lambda qs, e: qs.bulk_update([e], ["action"]),
            lambda qs, e: qs.update_or_create(pk=e.pk, defaults={"action": "x"}),
        ],
        ids=["update", "delete", "bulk_update", "update_or_create"],
    )
    def test_bulk_operations_fail(self, entry, operation):
        entry.action = "x"
        with pytest.raises(ImmutableAuditError):
            operation(AuditEntry.objects.all(), entry)
        assert AuditEntry.objects.get(pk=entry.pk).action == A.LOGOUT

    def test_a_new_entry_with_an_existing_id_does_not_overwrite_it(self, entry):
        copy = AuditEntry(pk=entry.pk, actor_kind="anonymous", action="auth.falsificada")
        with pytest.raises(IntegrityError), transaction.atomic():
            copy.save()
        assert AuditEntry.objects.get(pk=entry.pk).action == A.LOGOUT

    def test_the_actor_cannot_be_deleted_while_it_has_entries(self, make_person):
        # Una persona sense cap compte: només la retenen les seves entrades. En un esborrat
        # RGPD s'anonimitza, no s'esborra (RN-87, RN-89).
        person = make_person("Pau", "Riera")
        audit.record("activities.enrolled", actor=audit.guest(person, 7))
        with pytest.raises(ProtectedError), transaction.atomic():
            person.delete()
        assert AuditEntry.objects.filter(actor_person=person).exists()


class TestImmutableInPostgresql:
    # Prova de la T-M01-07: un UPDATE directe falla. També DELETE i TRUNCATE, i també si es
    # salta la protecció del model.

    @pytest.mark.parametrize(
        "sql",
        [
            "UPDATE core_auditentry SET action = 'x' WHERE id = %s",
            "UPDATE core_auditentry SET old_value = '\"canviat\"'::jsonb WHERE id = %s",
            "DELETE FROM core_auditentry WHERE id = %s",
        ],
        ids=["update", "update-value", "delete"],
    )
    def test_direct_sql_fails(self, entry, sql):
        with pytest.raises(DatabaseError, match="no es pot modificar ni esborrar"):
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute(sql, [entry.pk])
        assert AuditEntry.objects.get(pk=entry.pk).action == A.LOGOUT

    def test_truncate_fails(self, entry):
        with pytest.raises(DatabaseError, match="TRUNCATE"):
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("TRUNCATE core_auditentry")
        assert AuditEntry.objects.filter(pk=entry.pk).exists()

    def test_bypassing_the_model_guard_still_fails(self, entry):
        # `_base_manager` no fa servir el QuerySet protegit: atura-ho la base de dades.
        with pytest.raises(DatabaseError), transaction.atomic():
            AuditEntry._base_manager.filter(pk=entry.pk).update(action="x")
        with pytest.raises(DatabaseError), transaction.atomic():
            AuditEntry._base_manager.filter(pk=entry.pk)._raw_delete(connection.alias)
        assert AuditEntry.objects.get(pk=entry.pk).action == A.LOGOUT

    def test_inserting_is_still_allowed(self, entry):
        audit.record(A.LOGOUT, actor=audit.ANONYMOUS)
        assert AuditEntry.objects.count() == 2


class TestContent:
    def test_a_field_change_records_who_when_what_and_the_values(self, admin_account):
        # CA-14.1 i RN-50
        person = Person.objects.create(first_name="Marta", last_name="Soler", origin="web")
        before = {"phone": person.phone, "last_name": person.last_name}
        person.phone, person.last_name = "600000001", "Soler i Roig"
        person.save()
        created = audit.record_changes(
            "people.updated",
            actor=admin_account,
            target=person,
            changes={
                "phone": (before["phone"], person.phone),
                "last_name": (before["last_name"], person.last_name),
                "first_name": ("Marta", "Marta"),  # no canvia: sense entrada
            },
        )
        assert len(created) == 2
        rows = {e.field: e for e in AuditEntry.objects.filter(action="people.updated")}
        assert set(rows) == {"phone", "last_name"}
        row = rows["last_name"]
        assert (row.old_value, row.new_value) == ("Soler", "Soler i Roig")
        assert (row.target_type, row.target_id) == ("core.person", str(person.pk))
        assert row.actor_account == admin_account
        assert row.actor_person_id == admin_account.person_id
        assert row.created_at is not None

    def test_nothing_changed_records_nothing(self, admin_account):
        assert (
            audit.record_changes(
                "people.updated", actor=admin_account, target=admin_account.person, changes={}
            )
            == []
        )
        assert not AuditEntry.objects.exists()

    def test_time_is_stored_in_utc(self, entry):
        entry.refresh_from_db()
        assert entry.created_at.utcoffset() == timedelta(0)

    def test_each_account_of_the_same_person_is_told_apart(self, admin_account):
        # CA-14.2
        personal = Account.objects.create_personal(
            admin_account.person, "joan@example.org", PASSWORD
        )
        audit.record(A.LOGOUT, actor=personal)
        audit.record(A.LOGOUT, actor=admin_account)
        first, second = entries(A.LOGOUT)
        assert (first.actor_account, second.actor_account) == (personal, admin_account)
        assert first.actor_person_id == second.actor_person_id == admin_account.person_id

    def test_reason_and_details_are_kept(self, admin_account):
        row = audit.record(
            "people.updated",
            actor=admin_account,
            reason="  Error de transcripció  ",
            details={"area": "admin"},
        )
        row.refresh_from_db()
        assert row.reason == "Error de transcripció"
        assert row.details == {"area": "admin"}

    def test_dates_and_times_are_kept_exactly(self, admin_account):
        moment = datetime(2026, 11, 2, 9, 30, 15, 123456, tzinfo=UTC)
        row = audit.record(
            "members.join_date_corrected",
            actor=admin_account,
            field="join_date",
            old=date(1998, 3, 1),
            new=date(1998, 1, 3),
            details={"requested_at": moment},
        )
        row.refresh_from_db()
        assert (row.old_value, row.new_value) == ("1998-03-01", "1998-01-03")
        assert row.details["requested_at"] == "2026-11-02T09:30:15.123456+00:00"

    def test_the_ip_comes_from_the_request(self, rf, admin_account):
        request = rf.get("/", REMOTE_ADDR="198.51.100.20")
        row = audit.record(A.LOGOUT, actor=admin_account, request=request)
        assert row.ip_address == "198.51.100.20"

    def test_without_a_request_there_is_no_ip(self, entry):
        assert entry.ip_address is None


class TestActiveRoles:
    # RN-RP-15: cada entrada feta amb un compte d'administrador guarda els rols actius.

    def test_roles_at_the_moment_of_the_action(self, make_admin):
        account = make_admin(R.TREASURER, R.EQUIPMENT_MANAGER)
        first = audit.record(A.LOGOUT, actor=account)
        AccountRole.objects.filter(admin_account=account, role__code=R.TREASURER).update(
            removed_at=first.created_at
        )
        second = audit.record(A.LOGOUT, actor=account)
        first.refresh_from_db()
        assert first.actor_roles == [R.EQUIPMENT_MANAGER, R.TREASURER]
        assert second.actor_roles == [R.EQUIPMENT_MANAGER]

    def test_personal_accounts_have_no_roles(self, personal_account):
        assert audit.record(A.LOGOUT, actor=personal_account).actor_roles == []

    def test_admin_without_roles(self, make_admin):
        assert audit.record(A.LOGOUT, actor=make_admin()).actor_roles == []

    def test_non_account_actors_have_no_roles(self):
        assert audit.record(A.LOGOUT, actor=audit.system("prova")).actor_roles == []

    def test_assigning_a_role_records_the_roles_before_the_change(self, make_admin):
        admin = make_admin(R.ADMINISTRATOR)
        assign_role(admin, R.TREASURER, by=admin)
        row = only(A.ROLE_ASSIGNED)
        assert row.actor_roles == [R.ADMINISTRATOR]
        assert (row.field, row.old_value, row.new_value) == ("role", None, R.TREASURER)

    def test_self_deactivation_keeps_the_roles_it_had(self, make_admin):
        # RN-RP-20: l'entrada es fa abans de desactivar el compte.
        first = make_admin(R.ADMINISTRATOR, R.TREASURER)
        make_admin(R.ADMINISTRATOR)
        deactivate_admin_account(first, by=first)
        row = only(A.ADMIN_ACCOUNT_DISABLED)
        assert row.actor_roles == [R.ADMINISTRATOR, R.TREASURER]
        assert (row.old_value, row.new_value) == ("active", "disabled")


class TestActors:
    def test_system_needs_an_origin(self):
        # CA-14.5
        with pytest.raises(ValueError):
            audit.system("  ")
        row = audit.record(A.LOGOUT, actor=audit.system("generate-annual-fees"))
        assert (row.actor_kind, row.actor_origin, row.actor_account) == (
            "system",
            "generate-annual-fees",
            None,
        )

    def test_guest_keeps_the_internal_link_id_never_the_token(self, make_person):
        # CA-14.6
        person = make_person("Pau", "Riera")
        with pytest.raises(TypeError):
            audit.guest(person, "testimoni-secret-de-l-enllac")
        row = audit.record("activities.enrolled", actor=audit.guest(person, 42))
        assert (row.actor_kind, row.actor_person, row.actor_origin) == (
            "guest",
            person,
            "guest_link:42",
        )

    def test_no_actor_means_unidentified(self):
        row = audit.record(A.LOGIN_FAILED)
        assert (row.actor_kind, row.actor_person, row.actor_account) == ("anonymous", None, None)

    def test_unknown_actor_type_is_refused(self):
        with pytest.raises(TypeError):
            audit.record(A.LOGOUT, actor="algú")

    @pytest.mark.parametrize(
        "fields",
        [
            {"actor_kind": "account"},
            {"actor_kind": "system"},
            {"actor_kind": "guest", "actor_origin": "guest_link:1"},
            {"actor_kind": "anonymous", "actor_roles": ["administrator"]},
        ],
        ids=["account-without-account", "system-without-origin", "guest-without-person", "roles"],
    )
    def test_the_database_refuses_incoherent_actors(self, fields):
        with pytest.raises(IntegrityError), transaction.atomic():
            AuditEntry.objects.create(action="x", **fields)


class TestNoSecrets:
    # RN-52 i CA-14.4

    @pytest.mark.parametrize(
        "name", ["password", "new_password", "totp_secret", "token", "recovery_codes", "iban"]
    )
    def test_secret_looking_names_are_refused(self, admin_account, name):
        with pytest.raises(ValueError, match="RN-52"):
            audit.record(A.LOGOUT, actor=admin_account, field=name)
        with pytest.raises(ValueError, match="RN-52"):
            audit.record(A.LOGOUT, actor=admin_account, details={name: "x"})
        with pytest.raises(ValueError, match="RN-52"):
            audit.record_changes(
                A.LOGOUT, actor=admin_account, target=admin_account, changes={name: ("a", "b")}
            )
        assert not AuditEntry.objects.exists()

    def test_totp_enrolment_records_what_happened_without_secrets(self, client, admin_account):
        password_step(client)
        client.get(reverse(ENROL))
        device = TotpDevice.objects.get(account=admin_account)
        secret = totp.secret_of(device)
        response = client.post(reverse(ENROL), {"code": code_for(device)})
        codes = response.context["codes"]

        row = only(A.TOTP_ENROLLED)
        assert row.actor_account == admin_account
        assert row.ip_address == "127.0.0.1"
        text = as_text()
        assert secret not in text
        assert device.secret_encrypted not in text
        assert not any(code in text for code in codes)
        assert PASSWORD not in text

    def test_recovery_code_use_is_recorded_without_the_code(self, client, admin_account):
        _, codes = enrolled(admin_account)
        password_step(client)
        client.post(reverse(ADMIN_CODE), {"code": codes[0]})
        assert only(A.RECOVERY_CODE_USED).actor_account == admin_account
        assert codes[0] not in as_text()


class TestAuthenticationEvents:
    def post_login(self, client, login, password=PASSWORD, **extra):
        return client.post(reverse(PERSONAL_LOGIN), {"login": login, "password": password}, **extra)

    def test_successful_login(self, client, personal_account):
        self.post_login(client, "anna@example.org", REMOTE_ADDR="203.0.113.5")
        row = only(A.LOGIN_SUCCEEDED)
        assert row.actor_account == personal_account
        assert row.ip_address == "203.0.113.5"
        assert row.details == {"area": "personal"}

    def test_failure_with_an_unknown_login_stores_neither_login_nor_password(self, client):
        self.post_login(client, "ningu@example.org", "no-es-aquesta")
        row = only(A.LOGIN_FAILED)
        assert row.actor_kind == "anonymous"
        assert row.target_id == ""
        assert row.details == {"area": "personal", "reason": "unknown_login"}
        assert "ningu@example.org" not in as_text()
        assert "no-es-aquesta" not in as_text()

    def test_wrong_password_points_at_the_account(self, client, personal_account):
        self.post_login(client, "anna@example.org", "no-es-aquesta")
        row = only(A.LOGIN_FAILED)
        assert row.actor_kind == "anonymous"
        assert (row.target_type, row.target_id) == ("accounts.account", str(personal_account.pk))
        assert row.details["reason"] == "bad_password"
        assert "no-es-aquesta" not in as_text()

    def test_lock_is_recorded_by_the_system(self, client, personal_account):
        for _ in range(5):
            self.post_login(client, "anna@example.org", "no-es-aquesta")
        row = only(A.ACCOUNT_LOCKED)
        personal_account.refresh_from_db()
        assert (row.actor_kind, row.actor_origin) == ("system", "login-attempt-limit")
        assert row.target_id == str(personal_account.pk)
        assert row.field == "locked_until"
        assert row.new_value == personal_account.locked_until.isoformat()
        assert len(entries(A.LOGIN_FAILED)) == 5

    def test_origin_block_is_recorded_once(self, client, db):
        for i in range(22):
            self.post_login(client, f"ningu{i}@example.org", "x", REMOTE_ADDR="192.0.2.9")
        row = only(A.IP_BLOCKED)
        assert row.ip_address == "192.0.2.9"
        assert row.actor_origin == "login-attempt-limit"

    def test_logout(self, client, personal_account):
        self.post_login(client, "anna@example.org")
        client.post(reverse("accounts:logout"))
        assert only(A.LOGOUT).actor_account == personal_account


class TestRoleEvents:
    # RN-RP-08: cada canvi de rols d'un compte deixa una entrada.

    def test_removing_a_role(self, make_admin):
        admin = make_admin(R.ADMINISTRATOR)
        other = make_admin(R.TREASURER)
        remove_role(other, R.TREASURER, by=admin)
        row = only(A.ROLE_REMOVED)
        assert (row.actor_account, row.target_id) == (admin, str(other.pk))
        assert (row.field, row.old_value, row.new_value) == ("role", R.TREASURER, None)

    def test_a_refused_change_leaves_no_entry(self, make_admin):
        # L'entrada va dins la transacció de l'acció: si es rebutja, no queda res.
        admin = make_admin(R.ADMINISTRATOR)
        with pytest.raises(ValidationError):
            remove_role(admin, R.ADMINISTRATOR, by=admin)
        assert not entries(A.ROLE_REMOVED)

    def test_totp_reset_keeps_the_note_and_no_secret(self, make_admin):
        # RN-RP-18 i CA-14.4
        last = make_admin(R.ADMINISTRATOR)
        emergency = make_admin(R.ADMINISTRATOR, emergency=True)
        secret = last.totp_device.secret_encrypted
        RecoveryCode.objects.create(account=last, code_hash="a" * 64)
        reset_totp(last, by=emergency, note="Ha perdut el mòbil")
        row = only(A.TOTP_RESET)
        assert (row.actor_account, row.target_id) == (emergency, str(last.pk))
        assert row.reason == "Ha perdut el mòbil"
        assert row.details == {"emergency": True}
        assert secret not in as_text()
        assert "a" * 64 not in as_text()
