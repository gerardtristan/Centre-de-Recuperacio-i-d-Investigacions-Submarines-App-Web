"""Desactivar un compte d'administrador des de la pantalla, també el propi (T-RP-02d; RN-RP-13 i
20; CA-RP-06 i 16; CA-13.2). Només dades inventades."""

import pytest
from django.urls import reverse
from django.utils.html import escape

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN
from apps.core import audit
from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.core.roles import NO_OPERATIONAL_ADMIN
from apps.core.tests.test_roles_screen import NOTE, code_for
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
R = Role.Code
URL = "administration:account_deactivate"
TEMPLATE = "avis-desactivacio-admin"


def post(session, target, *, actor, code=None, note=NOTE, reviewed="on"):
    data = {"note": note, "reviewed": reviewed}
    data["code"] = code if code is not None else code_for(actor)
    return session.post(reverse(URL, args=[target.pk]), data)


def with_email(account, address):
    account.notification_email = address
    account.save()
    return account


@pytest.fixture
def admins(make_admin):
    anna = with_email(make_admin(R.ADMINISTRATOR, username="anna.admin"), "anna@example.org")
    bernat = with_email(make_admin(R.ADMINISTRATOR, username="bernat.admin"), "bernat@example.org")
    return anna, bernat


def status_of(account):
    account.refresh_from_db()
    return account.status


class TestWhoCanDoIt:
    @pytest.mark.parametrize("role", [code for code in R.values if code != R.ADMINISTRATOR])
    def test_every_other_role_gets_not_found(self, make_admin, login_as, admins, role):
        # M3 és protegit i exclusiu de l'administrador (CA-RP-03): el President tampoc.
        _, bernat = admins
        other = make_admin(role)
        session = login_as(other, AREA_ADMIN)
        assert session.get(reverse(URL, args=[bernat.pk])).status_code == 404
        assert post(session, bernat, actor=other).status_code == 404
        assert status_of(bernat) == Account.Status.ACTIVE

    def test_personal_account_is_not_a_target(self, admins, login_as, personal_account):
        anna, _ = admins
        response = login_as(anna, AREA_ADMIN).get(reverse(URL, args=[personal_account.pk]))
        assert response.status_code == 404

    def test_the_roles_screen_links_to_it(self, admins, login_as):
        anna, bernat = admins
        url = reverse("administration:account_roles", args=[bernat.pk])
        html = login_as(anna, AREA_ADMIN).get(url).content.decode()
        assert reverse(URL, args=[bernat.pk]) in html


class TestDeactivateAnother:
    def test_summary_saves_nothing(self, admins, login_as):
        anna, bernat = admins
        html = login_as(anna, AREA_ADMIN).get(reverse(URL, args=[bernat.pk])).content.decode()
        assert "bernat.admin" in html and 'name="code"' in html and 'name="note"' in html
        assert status_of(bernat) == Account.Status.ACTIVE

    def test_deactivates_closes_sessions_audits_and_notifies(
        self, admins, make_admin, login_as, django_capture_on_commit_callbacks
    ):
        anna, bernat = admins
        with_email(make_admin(R.PRESIDENT), "presidencia@example.org")
        with_email(make_admin(R.TREASURER), "tresoreria@example.org")
        theirs = client_for(bernat)
        with django_capture_on_commit_callbacks(execute=True):
            response = post(login_as(anna, AREA_ADMIN), bernat, actor=anna)
        assert response.status_code == 302
        assert status_of(bernat) == Account.Status.DISABLED
        assert theirs.get(reverse("administration:home")).status_code in (302, 401)  # CA-13.2
        entry = AuditEntry.objects.get(action=audit.Action.ADMIN_ACCOUNT_DISABLED)
        assert (entry.actor_account_id, entry.reason) == (anna.pk, NOTE)
        # RN-RP-20: els administradors i el compte afectat (P-370), cap altre rol.
        sent = OutgoingEmail.objects.filter(template=TEMPLATE)
        assert set(sent.values_list("to_address", flat=True)) == {
            "anna@example.org",
            "bernat@example.org",
        }
        body = sent.first().body_text
        assert "bernat.admin" in body and "anna.admin" in body and NOTE in body

    @pytest.mark.parametrize("code", ["", "000000"])
    def test_wrong_code_changes_nothing(self, admins, login_as, code):
        anna, bernat = admins
        response = post(login_as(anna, AREA_ADMIN), bernat, actor=anna, code=code)
        assert response.status_code == 200
        assert response.context["form"].has_error("code")
        assert status_of(bernat) == Account.Status.ACTIVE
        assert not AuditEntry.objects.filter(action=audit.Action.ADMIN_ACCOUNT_DISABLED).exists()
        assert not OutgoingEmail.objects.filter(template=TEMPLATE).exists()

    def test_note_and_review_are_required(self, admins, login_as):
        anna, bernat = admins
        response = post(login_as(anna, AREA_ADMIN), bernat, actor=anna, note="", reviewed="")
        form = response.context["form"]
        assert form.has_error("note") and form.has_error("reviewed")
        assert status_of(bernat) == Account.Status.ACTIVE

    def test_already_disabled_saves_nothing_and_keeps_the_code(self, admins, login_as):
        anna, bernat = admins
        bernat.status = Account.Status.DISABLED
        bernat.save()
        response = post(login_as(anna, AREA_ADMIN), bernat, actor=anna)
        assert escape("el canvi ja estava fet") in response.content.decode()
        assert not AuditEntry.objects.filter(action=audit.Action.ADMIN_ACCOUNT_DISABLED).exists()
        anna.refresh_from_db()
        assert anna.failed_login_count == 0


class TestDeactivateOneself:
    def test_last_operational_admin_cannot(self, make_admin, login_as):
        # CA-RP-06: el resum ho diu, sense formulari, i el servidor ho rebutja igualment.
        only = make_admin(R.ADMINISTRATOR)
        make_admin(R.ADMINISTRATOR, totp=False)  # no és operatiu
        session = login_as(only, AREA_ADMIN)
        summary = session.get(reverse(URL, args=[only.pk])).content.decode()
        assert escape(str(NO_OPERATIONAL_ADMIN)) in summary and 'name="code"' not in summary
        response = post(session, only, actor=only)
        assert escape(str(NO_OPERATIONAL_ADMIN)) in response.content.decode()
        assert status_of(only) == Account.Status.ACTIVE
        only.refresh_from_db()
        assert only.failed_login_count == 0  # el codi no s'ha gastat

    def test_closes_every_session_and_goes_to_the_login(
        self, admins, login_as, django_capture_on_commit_callbacks
    ):
        # CA-RP-16: dues sessions d'A, la petició en curs surt de l'administració i B rep el correu.
        anna, _ = admins
        other_device = client_for(anna)
        session = login_as(anna, AREA_ADMIN)
        with django_capture_on_commit_callbacks(execute=True):
            response = post(session, anna, actor=anna)
        assert response.status_code == 302
        assert response["Location"] == reverse("administration:login")
        assert status_of(anna) == Account.Status.DISABLED
        login_page = session.get(response["Location"]).content.decode()
        assert "Has desactivat el teu compte d&#x27;administrador" in login_page
        for device in (session, other_device):
            assert device.get(reverse("administration:home")).status_code in (302, 401)
        sent = OutgoingEmail.objects.filter(template=TEMPLATE)
        assert list(sent.values_list("to_address", flat=True)) == ["bernat@example.org"]
        entry = AuditEntry.objects.get(action=audit.Action.ADMIN_ACCOUNT_DISABLED)
        assert (entry.actor_account_id, entry.reason) == (anna.pk, NOTE)

    def test_summary_warns_about_leaving(self, admins, login_as):
        anna, _ = admins
        html = login_as(anna, AREA_ADMIN).get(reverse(URL, args=[anna.pk])).content.decode()
        assert "Sortiràs de l'administració" in html
