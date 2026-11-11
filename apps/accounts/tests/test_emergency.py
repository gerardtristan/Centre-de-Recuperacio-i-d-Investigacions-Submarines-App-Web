"""Comptes d'emergència (T-M00-03; spec 00, HU-10, CA-10.1 i CA-10.2; 079, A-30). Només dades
inventades. L'excepció de RN-RP-18 i els codis de recuperació ja tenen les seves proves
(`apps/core/tests/test_roles.py`, `test_totp.py`).
"""

from io import StringIO
from unittest import mock

import pyotp
import pytest
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from django.test import Client
from django.urls import reverse

from apps.accounts import emergency
from apps.accounts.models import Account
from apps.core import audit
from apps.core.models import AccountRole, AuditEntry, OutgoingEmail, Person, Role
from apps.core.roles import operational_admins
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
SECRET = "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"  # el de `make_admin`, inventat


class TestCreate:
    def test_a30_linked_to_a_technical_person_without_personal_data(self):
        account = emergency.create("emergencia.u", PASSWORD)
        person = account.person
        assert account.is_emergency and account.kind == Account.Kind.ADMIN
        assert person.origin == Person.Origin.TECHNICAL
        assert person.first_name == emergency.TECHNICAL_NAME
        for field in ("last_name", "contact_email", "phone", "address", "id_document_number"):
            assert getattr(person, field) == ""
        assert person.birth_date is None
        assert not account.has_totp  # el dona d'alta en la primera entrada (CA-09.1)

    def test_rn_13_each_emergency_account_has_its_own_person(self):
        first = emergency.create("emergencia.u", PASSWORD)
        second = emergency.create("emergencia.dos", PASSWORD)
        assert first.person_id != second.person_id

    def test_it_has_the_administrator_role_but_is_not_operational(self):
        account = emergency.create("emergencia.u", PASSWORD)
        assert AccountRole.objects.filter(
            admin_account=account, role__code=Role.Code.ADMINISTRATOR, removed_at__isnull=True
        ).exists()
        assert account not in operational_admins()  # RN-RP-13

    def test_the_audit_log_has_the_system_as_actor_and_no_password(self):
        account = emergency.create("emergencia.u", PASSWORD)
        entry = AuditEntry.objects.get(action=emergency.CREATED)
        assert entry.target_id == str(account.pk)
        assert (entry.actor_kind, entry.actor_origin) == ("system", emergency.COMMAND)
        assert PASSWORD not in str(list(AuditEntry.objects.values()))

    def test_a_weak_password_is_rejected_and_nothing_is_created(self):
        with pytest.raises(ValidationError):
            emergency.create("emergencia.u", "1234")
        assert not Account.objects.exists()
        assert not Person.objects.filter(origin=Person.Origin.TECHNICAL).exists()

    def test_the_command_never_prints_the_password(self):
        out = StringIO()
        with mock.patch(
            "apps.accounts.management.commands.crea_compte_emergencia.getpass",
            side_effect=[PASSWORD, PASSWORD],
        ):
            call_command("crea_compte_emergencia", "emergencia.u", stdout=out)
        assert "emergencia.u" in out.getvalue() and PASSWORD not in out.getvalue()
        assert Account.objects.get(login="emergencia.u").is_emergency

    def test_the_command_refuses_different_passwords(self):
        with (
            mock.patch(
                "apps.accounts.management.commands.crea_compte_emergencia.getpass",
                side_effect=[PASSWORD, "una-altra-cosa"],
            ),
            pytest.raises(CommandError),
        ):
            call_command("crea_compte_emergencia", "emergencia.u", stdout=StringIO())
        assert not Account.objects.exists()


class TestCa101Warning:
    def test_ca_10_1_administrators_are_warned_with_fewer_than_two(self, make_admin):  # noqa: F811
        admin = make_admin("administrator")
        make_admin("administrator", emergency=True)
        make_admin("administrator", emergency=True, totp=False)  # sense TOTP no compta
        assert emergency.warning_for(admin) == 1
        for name in ("administration:home", "administration:accounts"):
            text = admin_client(admin).get(reverse(name)).content.decode()
            assert "Falten comptes d'emergència." in text

    def test_ca_10_1_no_warning_with_two_ready(self, make_admin):  # noqa: F811
        admin = make_admin("administrator")
        make_admin("administrator", emergency=True)
        make_admin("administrator", emergency=True)
        assert emergency.warning_for(admin) is None
        text = admin_client(admin).get(reverse("administration:home")).content.decode()
        assert "Falten comptes d'emergència." not in text

    def test_ca_10_1_disabled_accounts_do_not_count(self, make_admin):  # noqa: F811
        admin = make_admin("administrator")
        make_admin("administrator", emergency=True)
        disabled = make_admin("administrator", emergency=True)
        Account.objects.filter(pk=disabled.pk).update(status=Account.Status.DISABLED)
        assert emergency.warning_for(admin) == 1

    @pytest.mark.parametrize("role", ["secretary", "treasurer", "president"])
    def test_ca_10_1_other_roles_are_not_warned(self, make_admin, role):  # noqa: F811
        account = make_admin(role)
        assert emergency.warning_for(account) is None
        text = admin_client(account).get(reverse("administration:home")).content.decode()
        assert "Falten comptes d'emergència." not in text


def login(username):
    client = Client()
    client.post(reverse("administration:login"), {"login": username, "password": PASSWORD})
    response = client.post(reverse("administration:login_totp"), {"code": pyotp.TOTP(SECRET).now()})
    assert response.status_code == 302
    return client


def with_password(account, email=""):
    account.set_password(PASSWORD)
    account.notification_email = email
    account.save()
    return account


class TestCa102Use:
    def test_ca_10_2_using_it_is_logged_and_administrators_are_notified(self, make_admin):  # noqa: F811
        other = with_password(make_admin("administrator"), "admin.u@example.org")
        with_password(make_admin("administrator"), "admin.dos@example.org")
        with_password(make_admin("secretary"), "secretaria@example.org")
        used = with_password(make_admin("administrator", emergency=True))
        login(used.login)
        entry = AuditEntry.objects.get(action=emergency.USED)
        assert entry.actor_account == used
        assert entry.details == {"area": "admin", "notified": 2}
        sent = OutgoingEmail.objects.filter(template=emergency.NOTICE_TEMPLATE)
        assert sorted(sent.values_list("to_address", flat=True)) == [
            "admin.dos@example.org",
            "admin.u@example.org",
        ]
        assert used.login in sent.first().body_text
        assert other.login not in sent.first().body_text

    def test_a_normal_login_sends_nothing(self, make_admin):  # noqa: F811
        with_password(make_admin("administrator"), "admin.u@example.org")
        account = with_password(make_admin("administrator"), "admin.dos@example.org")
        login(account.login)
        assert not AuditEntry.objects.filter(action=emergency.USED).exists()
        assert not OutgoingEmail.objects.filter(template=emergency.NOTICE_TEMPLATE).exists()

    def test_the_notice_never_carries_secrets(self, make_admin):  # noqa: F811
        with_password(make_admin("administrator"), "admin.u@example.org")
        used = with_password(make_admin("administrator", emergency=True))
        emergency.record_use(used, area="admin")
        body = OutgoingEmail.objects.get(template=emergency.NOTICE_TEMPLATE).body_text
        assert PASSWORD not in body and SECRET not in body and "http" not in body
        assert audit.Action.LOGIN_SUCCEEDED not in body
