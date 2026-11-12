"""Comptes personal i d'administrador (spec 00, RN-11 a RN-19; CA-06.x). Dades inventades."""

import pytest
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import Account
from apps.core.models import Person

pytestmark = pytest.mark.django_db

PASSWORD = "contrasenya-de-proves-1954"  # noqa: S105 (dada inventada de proves)


@pytest.fixture
def anna():
    return Person.objects.create(first_name="Anna", last_name="Puig", origin=Person.Origin.WEB)


@pytest.fixture
def joan():
    return Person.objects.create(first_name="Joan", last_name="Vila", origin=Person.Origin.WEB)


def test_auth_user_model_is_account():
    assert settings.AUTH_USER_MODEL == "accounts.Account"
    assert get_user_model() is Account


class TestPersonalAccount:
    def test_created_pending_with_normalized_email(self, anna):
        account = Account.objects.create_personal(anna, " Anna@Example.ORG ", PASSWORD)
        assert account.kind == Account.Kind.PERSONAL
        assert account.login == "anna@example.org"
        assert account.status == Account.Status.PENDING
        assert account.person == anna
        assert not account.is_superuser

    def test_password_is_hashed(self, anna):
        account = Account.objects.create_personal(anna, "anna@example.org", PASSWORD)
        assert account.password != PASSWORD
        assert account.check_password(PASSWORD)

    def test_without_password_it_is_unusable(self, anna):
        account = Account.objects.create_personal(anna, "anna@example.org")
        assert not account.has_usable_password()

    def test_pending_account_cannot_log_in(self, anna):
        # RN-18: no obté sessió fins que confirma el correu.
        Account.objects.create_personal(anna, "anna@example.org", PASSWORD)
        assert authenticate(login="anna@example.org", password=PASSWORD) is None

    def test_active_account_logs_in_with_email_in_any_case(self, anna):
        account = Account.objects.create_personal(anna, "anna@example.org", PASSWORD)
        account.status = Account.Status.ACTIVE
        account.save()
        assert authenticate(login="ANNA@example.org", password=PASSWORD) == account

    def test_disabled_is_not_active(self, anna):
        account = Account.objects.create_personal(anna, "anna@example.org")
        account.status = Account.Status.DISABLED
        assert not account.is_active

    def test_email_is_unique_ignoring_case(self, anna, joan):
        # RN-10, V-05: el correu d'entrada d'un compte personal és únic.
        Account.objects.create_personal(anna, "anna@example.org")
        with pytest.raises(ValidationError):
            Account.objects.create_personal(joan, "ANNA@example.org")

    def test_login_must_be_an_email(self, anna):
        with pytest.raises(ValidationError):
            Account.objects.create_personal(anna, "anna-sense-arroba")

    @pytest.mark.parametrize(
        "fields",
        [
            {"notification_email": "avisos@example.org"},
            {"is_emergency": True},
            {"is_superuser": True},
        ],
    )
    def test_admin_only_fields_are_rejected(self, anna, fields):
        account = Account(
            person=anna, kind="personal", login="anna@example.org", status="pending", **fields
        )
        with pytest.raises(ValidationError):
            account.full_clean(exclude=["password"])
        with pytest.raises(IntegrityError), transaction.atomic():
            account.save()


class TestAdminAccount:
    def test_created_active_with_notification_email(self, anna):
        account = Account.objects.create_admin(
            anna, "Anna.Puig", PASSWORD, notification_email="Anna@Example.org"
        )
        assert account.kind == Account.Kind.ADMIN
        assert account.login == "anna.puig"
        assert account.notification_email == "anna@example.org"
        assert account.status == Account.Status.ACTIVE
        assert not account.is_superuser

    def test_username_is_unique_ignoring_case(self, anna, joan):
        # CA-06.2
        Account.objects.create_admin(anna, "secretaria")
        with pytest.raises(ValidationError):
            Account.objects.create_admin(joan, "Secretaria")

    def test_notification_email_is_not_unique(self, anna, joan):
        # CA-06.3
        Account.objects.create_admin(anna, "anna", notification_email="junta@example.org")
        Account.objects.create_admin(joan, "joan", notification_email="junta@example.org")

    @pytest.mark.parametrize("username", ["anna@example.org", "an", "anna puig", "àngels"])
    def test_invalid_username_is_rejected(self, anna, username):
        with pytest.raises(ValidationError):
            Account.objects.create_admin(anna, username)

    def test_cannot_log_in_with_notification_email(self, anna):
        # CA-07.5
        Account.objects.create_admin(anna, "anna", PASSWORD, notification_email="anna@example.org")
        assert authenticate(login="anna@example.org", password=PASSWORD) is None
        assert authenticate(login="anna", password=PASSWORD) is not None


class TestOnePerKind:
    def test_personal_and_admin_on_the_same_person(self, anna):
        # RN-12, CA-06.1: tots dos comptes lligats al mateix perfil.
        personal = Account.objects.create_personal(anna, "anna@example.org")
        admin = Account.objects.create_admin(anna, "anna")
        assert set(anna.accounts.all()) == {personal, admin}

    def test_second_admin_account_is_rejected(self, anna):
        # CA-06.4 (sense l'excepció d'emergència fins que es respongui Q-02).
        Account.objects.create_admin(anna, "anna")
        with pytest.raises(ValidationError):
            Account.objects.create_admin(anna, "anna2")

    def test_database_rejects_a_second_account_of_the_same_kind(self, anna):
        Account.objects.create_personal(anna, "anna@example.org")
        with pytest.raises(IntegrityError), transaction.atomic():
            Account.objects.bulk_create(
                [Account(person=anna, kind="personal", login="anna2@example.org", status="pending")]
            )


class TestDatabaseConstraints:
    """Les regles valen encara que algú se salti el gestor."""

    @pytest.mark.parametrize(
        ("kind", "login"),
        [("personal", "anna"), ("admin", "anna@example.org"), ("admin", "Anna")],
    )
    def test_login_shape_is_enforced(self, anna, kind, login):
        with pytest.raises(IntegrityError), transaction.atomic():
            Account.objects.bulk_create(
                [Account(person=anna, kind=kind, login=login, status="active")]
            )

    def test_person_with_accounts_cannot_be_deleted(self, anna):
        # RN-25: els comptes es desactiven, no s'esborren.
        from django.db.models import ProtectedError

        Account.objects.create_personal(anna, "anna@example.org")
        with pytest.raises(ProtectedError):
            anna.delete()


class TestSuperuser:
    def test_create_superuser_is_an_admin_account(self):
        account = Account.objects.create_superuser("Administrador", PASSWORD)
        assert account.kind == Account.Kind.ADMIN
        assert account.login == "administrador"
        assert account.is_superuser
        assert account.is_active
        assert account.person.first_name == "Administrador"

    def test_create_superuser_with_existing_person(self, anna):
        account = Account.objects.create_superuser("anna", PASSWORD, person=anna)
        assert account.person == anna

    def test_superuser_cannot_log_in_with_an_email(self):
        with pytest.raises(ValueError):
            Account.objects.create_superuser("admin@example.org", PASSWORD)
        assert not Person.objects.exists()

    def test_createsuperuser_command(self):
        from django.core.management import call_command

        call_command("createsuperuser", "--noinput", "--login", "arrel", verbosity=0)
        account = Account.objects.get(login="arrel")
        assert account.is_superuser
        assert not account.has_usable_password()


def test_create_user_dispatches_by_identifier(anna, joan):
    assert Account.objects.create_user("anna@example.org", person=anna).kind == "personal"
    assert Account.objects.create_user("joan", person=joan).kind == "admin"
