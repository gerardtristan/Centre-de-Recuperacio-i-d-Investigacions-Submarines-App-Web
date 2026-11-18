"""Mai cap administrador operatiu de menys (RN-RP-13; CA-RP-06), també amb dos canvis alhora
(revisió de #216, punts 1 i 2). Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.db import OperationalError
from django.utils import timezone

from apps.accounts.models import Account, TotpDevice
from apps.core import roles
from apps.core.crypto import encrypt
from apps.core.models import AccountRole, Person, Role
from conftest import CommittedDataTestCase, run_together

R = Role.Code


def admin(username):
    person = Person.objects.create(first_name=username.title(), origin="in_person")
    account = Account.objects.create_admin(person, username)
    TotpDevice.objects.create(
        account=account,
        secret_encrypted=encrypt("JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"),
        confirmed_at=timezone.now(),
    )
    AccountRole.objects.create(admin_account=account, role=Role.objects.get(code=R.ADMINISTRATOR))
    return account


@pytest.mark.django_db
class TestDecidesAfterTheLock:
    """Simulació: mentre s'espera el bloqueig, un altre canvi deixa de comptar com a operatiu
    l'altre administrador i es confirma. La decisió s'ha de prendre amb el que hi ha després."""

    @pytest.fixture
    def pair(self, monkeypatch):
        anna, bernat = admin("anna"), admin("bernat")
        original = roles._lock_admin_accounts

        def lock_then_the_other_commits(account):
            original(account)
            Account.objects.filter(pk=bernat.pk).update(status=Account.Status.DISABLED)

        monkeypatch.setattr(roles, "_lock_admin_accounts", lock_then_the_other_commits)
        return anna, bernat

    def test_deactivating(self, pair):
        anna, _ = pair
        with pytest.raises(ValidationError):
            roles.deactivate_admin_account(anna, by=anna, note="Relleu")

    def test_removing_the_role(self, pair):
        anna, _ = pair
        with pytest.raises(ValidationError):
            roles.remove_role(anna, R.ADMINISTRATOR, by=anna, note="Relleu")


def outcome(function):
    def run():
        try:
            function()
        except ValidationError:
            return "rejected"
        except OperationalError:
            return "database"
        return "done"

    return run


class TestTwoAtOnce(CommittedDataTestCase):
    """Dos administradors operatius, cadascun es treu l'accés alhora: un s'accepta i l'altre es
    rebutja, sense cap error de la base de dades (un sol ordre de bloqueig)."""

    def test_two_self_deactivations(self):
        anna, bernat = admin("anna"), admin("bernat")
        results = run_together(
            [
                outcome(lambda: roles.deactivate_admin_account(anna, by=anna, note="Relleu")),
                outcome(lambda: roles.deactivate_admin_account(bernat, by=bernat, note="Relleu")),
            ]
        )
        assert sorted(results) == ["done", "rejected"]
        assert roles.operational_admins().count() == 1

    def test_a_deactivation_and_a_role_removal(self):
        anna, bernat = admin("anna"), admin("bernat")
        results = run_together(
            [
                outcome(lambda: roles.deactivate_admin_account(anna, by=anna, note="Relleu")),
                outcome(
                    lambda: roles.remove_role(bernat, R.ADMINISTRATOR, by=bernat, note="Relleu")
                ),
            ]
        )
        assert sorted(results) == ["done", "rejected"]
        assert roles.operational_admins().count() == 1
