"""Governança de rols (059 i 060; RN-RP-03, 11, 13, 14, 18 i 20; CA-RP-01, 03, 06, 07, 09,
11, 14, 15 i 16). Només dades inventades."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account, RecoveryCode, TotpDevice
from apps.core.crypto import encrypt
from apps.core.models import AccountRole, Role
from apps.core.permissions import has_perm
from apps.core.roles import (
    NO_OPERATIONAL_ADMIN,
    SECOND_TREASURER,
    admin_shortage_warning,
    assign_role,
    deactivate_admin_account,
    operational_admins,
    remove_role,
    reset_totp,
    validate_role_permissions,
)

pytestmark = pytest.mark.django_db
R = Role.Code


def active_roles(account):
    return set(
        AccountRole.objects.filter(admin_account=account, removed_at__isnull=True).values_list(
            "role__code", flat=True
        )
    )


def message_of(exc_info):
    return " ".join(exc_info.value.messages)


class TestWhoManagesRoles:
    @pytest.mark.parametrize("role", [R.PRESIDENT, R.SECRETARY, R.TREASURER, R.BOARD])
    def test_only_the_administrator_role(self, make_admin, role):
        # CA-RP-03: el President (i qualsevol altre rol) rep «no trobat».
        target = make_admin(R.INSTRUCTOR)
        with pytest.raises(Http404):
            assign_role(target, R.TREASURER, by=make_admin(role))
        with pytest.raises(Http404):
            remove_role(target, R.INSTRUCTOR, by=make_admin(role))
        with pytest.raises(Http404):
            deactivate_admin_account(target, by=make_admin(role))
        assert active_roles(target) == {R.INSTRUCTOR}

    def test_superuser_without_the_role_cannot_manage(self, make_admin):
        actor = make_admin()
        actor.is_superuser = True
        actor.save()
        with pytest.raises(Http404):
            assign_role(make_admin(), R.TREASURER, by=actor)


class TestAssign:
    def test_assign(self, make_admin):
        admin, target = make_admin(R.ADMINISTRATOR), make_admin()
        assert assign_role(target, R.SECRETARY, by=admin) == []
        assignment = AccountRole.objects.get(admin_account=target, role__code=R.SECRETARY)
        assert assignment.assigned_by == admin
        assert has_perm(target, "members.create_in_person")

    def test_assign_twice_is_harmless(self, make_admin):
        admin, target = make_admin(R.ADMINISTRATOR), make_admin()
        assign_role(target, R.SECRETARY, by=admin)
        assign_role(target, R.SECRETARY, by=admin)
        assert AccountRole.objects.filter(admin_account=target).count() == 1

    @pytest.mark.parametrize("role", [R.MEMBER, R.VISITOR, R.GUEST])
    def test_non_management_roles_are_not_assigned(self, make_admin, role):
        with pytest.raises(ValidationError):
            assign_role(make_admin(), role, by=make_admin(R.ADMINISTRATOR))

    def test_personal_accounts_get_no_roles(self, make_admin, personal_account):
        with pytest.raises(ValidationError):
            assign_role(personal_account, R.SECRETARY, by=make_admin(R.ADMINISTRATOR))

    def test_second_treasurer_warns_but_is_saved(self, make_admin):
        # CA-RP-14
        admin = make_admin(R.ADMINISTRATOR)
        make_admin(R.TREASURER)
        target = make_admin()
        assert assign_role(target, R.TREASURER, by=admin) == [SECOND_TREASURER]
        assert R.TREASURER in active_roles(target)

    def test_first_treasurer_has_no_warning(self, make_admin):
        assert assign_role(make_admin(), R.TREASURER, by=make_admin(R.ADMINISTRATOR)) == []


class TestRemove:
    def test_remove_keeps_the_row_and_the_session(self, make_admin):
        # CA-RP-01
        admin = make_admin(R.ADMINISTRATOR)
        target = make_admin(R.TREASURER, R.EQUIPMENT_MANAGER)
        epoch = target.session_epoch
        remove_role(target, R.TREASURER, by=admin)
        row = AccountRole.objects.get(admin_account=target, role__code=R.TREASURER)
        assert row.removed_at and row.removed_by == admin
        assert not has_perm(target, "members.unpaid.mark")
        target.refresh_from_db()
        assert target.session_epoch == epoch

    def test_role_can_be_assigned_again_after_removal(self, make_admin):
        admin, target = make_admin(R.ADMINISTRATOR), make_admin(R.SECRETARY, R.TREASURER)
        remove_role(target, R.SECRETARY, by=admin)
        assign_role(target, R.SECRETARY, by=admin)
        assert AccountRole.objects.filter(admin_account=target).count() == 3

    def test_removing_a_role_it_does_not_have(self, make_admin):
        with pytest.raises(ValidationError):
            remove_role(make_admin(), R.SECRETARY, by=make_admin(R.ADMINISTRATOR))

    def test_losing_the_only_role_closes_sessions(self, make_admin, login_as):
        # CA-RP-11 (RN-RP-11): sessions tancades, compte actiu.
        admin, target = make_admin(R.ADMINISTRATOR), make_admin(R.SECRETARY)
        client = login_as(target, "admin")
        assert client.get(reverse("administration:home")).status_code == 200
        remove_role(target, R.SECRETARY, by=admin)
        assert client.get(reverse("administration:home")).status_code == 302
        target.refresh_from_db()
        assert target.status == Account.Status.ACTIVE


class TestOperationalAdministrator:
    """RN-RP-13 i CA-RP-06."""

    def test_definition(self, make_admin):
        operational = make_admin(R.ADMINISTRATOR)
        make_admin(R.ADMINISTRATOR, totp=False)
        make_admin(R.ADMINISTRATOR, emergency=True)
        make_admin(R.SECRETARY)
        locked = make_admin(R.ADMINISTRATOR)
        locked.locked_until = timezone.now() + timedelta(minutes=10)
        locked.save()
        disabled = make_admin(R.ADMINISTRATOR)
        disabled.status = Account.Status.DISABLED
        disabled.save()
        assert list(operational_admins()) == [operational]

    def test_unconfirmed_totp_does_not_count(self, make_admin):
        account = make_admin(R.ADMINISTRATOR, totp=False)
        TotpDevice.objects.create(account=account, secret_encrypted=encrypt("JBSWY3DPEHPK3PXP"))
        assert not operational_admins().exists()

    def test_last_one_cannot_lose_the_role(self, make_admin):
        only = make_admin(R.ADMINISTRATOR)
        with pytest.raises(ValidationError) as exc:
            remove_role(only, R.ADMINISTRATOR, by=only)
        assert NO_OPERATIONAL_ADMIN in message_of(exc)
        assert R.ADMINISTRATOR in active_roles(only)

    def test_last_one_cannot_be_deactivated(self, make_admin):
        only = make_admin(R.ADMINISTRATOR)
        with pytest.raises(ValidationError):
            deactivate_admin_account(only, by=only)
        only.refresh_from_db()
        assert only.status == Account.Status.ACTIVE

    def test_non_operational_admins_do_not_save_the_last_one(self, make_admin):
        only = make_admin(R.ADMINISTRATOR)
        make_admin(R.ADMINISTRATOR, totp=False)
        make_admin(R.ADMINISTRATOR, emergency=True)
        with pytest.raises(ValidationError):
            remove_role(only, R.ADMINISTRATOR, by=only)

    def test_with_two_it_is_accepted_and_the_warning_shows(self, make_admin):
        first, second = make_admin(R.ADMINISTRATOR), make_admin(R.ADMINISTRATOR)
        assert not admin_shortage_warning()
        remove_role(second, R.ADMINISTRATOR, by=first)
        assert admin_shortage_warning()

    def test_removing_a_non_operational_admin_is_allowed(self, make_admin):
        only = make_admin(R.ADMINISTRATOR)
        no_totp = make_admin(R.ADMINISTRATOR, totp=False)
        remove_role(no_totp, R.ADMINISTRATOR, by=only)


class TestSelfDeactivation:
    """RN-RP-20 i CA-RP-16."""

    def test_closes_every_session_and_keeps_the_personal_account(
        self, make_admin, make_person, client, django_user_model
    ):
        from django.test import Client

        from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY

        person = make_person()
        personal = Account.objects.create_personal(person, "anna@example.org")
        personal.status = Account.Status.ACTIVE
        personal.save()
        me = make_admin(R.ADMINISTRATOR, person=person)
        make_admin(R.ADMINISTRATOR)

        devices = []
        for _ in range(2):
            device = Client()
            device.force_login(me)
            session = device.session
            session[AREA_SESSION_KEY] = "admin"
            session[AUTH_AT_SESSION_KEY] = timezone.now().timestamp()
            session.save()
            assert device.get(reverse("administration:home")).status_code == 200
            devices.append(device)

        deactivate_admin_account(me, by=me)

        for device in devices:
            response = device.get(reverse("administration:home"))
            assert response["Location"].startswith(reverse("administration:login"))
        me.refresh_from_db()
        personal.refresh_from_db()
        assert me.status == Account.Status.DISABLED
        assert personal.status == Account.Status.ACTIVE

    def test_rejected_when_only_one_operational(self, make_admin):
        me = make_admin(R.ADMINISTRATOR)
        make_admin(R.ADMINISTRATOR, totp=False)
        with pytest.raises(ValidationError):
            deactivate_admin_account(me, by=me)


class TestResetTotp:
    def test_resets_another_admin(self, make_admin):
        actor, target = make_admin(R.ADMINISTRATOR), make_admin(R.ADMINISTRATOR)
        RecoveryCode.objects.create(account=target, code_hash="a" * 64)
        epoch = target.session_epoch
        reset_totp(target, by=actor)
        assert not TotpDevice.objects.filter(account=target).exists()
        assert not RecoveryCode.objects.filter(account=target).exists()
        target.refresh_from_db()
        assert target.session_epoch == epoch + 1

    def test_never_on_oneself(self, make_admin):
        me = make_admin(R.ADMINISTRATOR)
        make_admin(R.ADMINISTRATOR)
        with pytest.raises(ValidationError):
            reset_totp(me, by=me)

    def test_needs_the_protected_permission(self, make_admin):
        with pytest.raises(Http404):
            reset_totp(make_admin(R.SECRETARY), by=make_admin(R.PRESIDENT))

    def test_last_operational_admin_is_protected(self, make_admin):
        # CA-RP-06: un compte que no és d'emergència no ho pot fer.
        only = make_admin(R.ADMINISTRATOR)
        other = make_admin(R.ADMINISTRATOR, totp=False)
        with pytest.raises(ValidationError):
            reset_totp(only, by=other, note="Ha perdut el mòbil")
        assert TotpDevice.objects.filter(account=only).exists()

    def test_emergency_account_can_reset_the_last_one_with_a_note(self, make_admin):
        # RN-RP-18 i CA-RP-15
        only = make_admin(R.ADMINISTRATOR)
        emergency = make_admin(R.ADMINISTRATOR, emergency=True)
        with pytest.raises(ValidationError):
            reset_totp(only, by=emergency, note="  ")
        reset_totp(only, by=emergency, note="Ha perdut el mòbil; trucada verificada.")
        assert not TotpDevice.objects.filter(account=only).exists()
        assert admin_shortage_warning()


class TestMatrixValidation:
    """Comprovacions de l'editor (T-RP-03) i de les migracions que canviïn la matriu."""

    def test_requirement_is_not_added_on_its_own(self):
        # CA-RP-07
        with pytest.raises(ValidationError) as exc:
            validate_role_permissions(R.BOARD, {"members.requests.approve_join": "all"})
        assert "demana també" in message_of(exc)
        validate_role_permissions(
            R.BOARD,
            {"members.requests.approve_join": "all", "members.requests.view": "all"},
        )

    @pytest.mark.parametrize(
        "code",
        [
            "core.accounts.manage",
            "core.permissions.edit",
            "core.accounts.reset_credentials",
            "members.field.birth_date",
            "core.locked_data.view",
        ],
    )
    def test_protected_rules_cannot_be_given(self, code):
        # CA-RP-03 (gestió d'usuaris al President) i CA-RP-09
        with pytest.raises(ValidationError) as exc:
            validate_role_permissions(R.PRESIDENT, {code: "all"})
        assert "regla protegida" in message_of(exc)

    def test_scope_must_be_allowed(self):
        with pytest.raises(ValidationError):
            validate_role_permissions(R.INSTRUCTOR, {"members.export": "own_sessions"})

    def test_unknown_permission(self):
        with pytest.raises(ValidationError):
            validate_role_permissions(R.INSTRUCTOR, {"members.no_existeix": "all"})

    @pytest.mark.parametrize("role", [R.MEMBER, R.GUEST, "no-existeix"])
    def test_only_management_roles(self, role):
        with pytest.raises(ValidationError):
            validate_role_permissions(role, {"members.export": "all"})

    @pytest.mark.parametrize(
        "role", [r for r in R.values if r not in ("member", "visitor", "guest")]
    )
    def test_initial_configuration_is_valid(self, role):
        from apps.core.permission_catalog import editable_initial_cells

        cells = {code: scope for r, code, scope in editable_initial_cells() if r == role}
        validate_role_permissions(role, cells)


def test_createsuperuser_gets_the_administrator_role():
    call_command("createsuperuser", "--noinput", "--login", "arrel", verbosity=0)
    account = Account.objects.get(login="arrel")
    assert active_roles(account) == {R.ADMINISTRATOR}
    assert has_perm(account, "core.accounts.manage")
