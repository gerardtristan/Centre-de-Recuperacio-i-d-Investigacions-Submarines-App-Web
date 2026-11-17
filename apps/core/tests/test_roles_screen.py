"""Pantalla d'assignar i retirar rols (T-RP-02; 059 i 060; RN-RP-07, 08, 09, 11, 13 i 14;
CA-RP-03, 06, 11 i 14). Només dades inventades."""

from datetime import timedelta

import pyotp
import pytest
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from apps.accounts import totp
from apps.accounts.models import TotpDevice
from apps.accounts.security import AREA_ADMIN
from apps.core import audit
from apps.core.models import AccountRole, AuditEntry, OutgoingEmail, Role
from apps.core.roles import NO_OPERATIONAL_ADMIN, SECOND_TREASURER
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
R = Role.Code
URL = "administration:account_roles"
NOTE = "Canvi de càrrec acordat a la junta"


def active_roles(account):
    return set(
        AccountRole.objects.filter(admin_account=account, removed_at__isnull=True).values_list(
            "role__code", flat=True
        )
    )


def code_for(account, steps_ahead=1):
    device = TotpDevice.objects.get(account=account)
    moment = timezone.now() + timedelta(seconds=30 * steps_ahead)
    return pyotp.TOTP(totp.secret_of(device)).at(moment)


def post(session, target, action, role, *, actor, code=None, note=NOTE, reviewed="on"):
    data = {"action": action, "role": role, "note": note, "reviewed": reviewed}
    data["code"] = code if code is not None else code_for(actor)
    return session.post(reverse(URL, args=[target.pk]), data)


@pytest.fixture
def pair(make_admin):
    admin = make_admin(R.ADMINISTRATOR, username="anna.admin")
    target = make_admin(R.INSTRUCTOR, username="bernat.instr")
    target.notification_email = "bernat@example.org"
    target.save()
    return admin, target


class TestWhoCanOpenIt:
    @pytest.mark.parametrize("role", [code for code in R.values if code != R.ADMINISTRATOR])
    def test_every_other_role_gets_not_found(self, make_admin, login_as, pair, role):
        # CA-RP-03: només el rol administrador (M3, protegit). El President tampoc.
        _, target = pair
        session = login_as(make_admin(role), AREA_ADMIN)
        assert session.get(reverse(URL, args=[target.pk])).status_code == 404
        assert session.post(reverse(URL, args=[target.pk]), {}).status_code == 404

    def test_the_administrator_opens_it(self, pair, login_as):
        admin, target = pair
        response = login_as(admin, AREA_ADMIN).get(reverse(URL, args=[target.pk]))
        assert response.status_code == 200
        assert "no-cache" in response["Cache-Control"]

    def test_the_president_cannot_assign_by_post(self, make_admin, login_as, pair):
        _, target = pair
        president = make_admin(R.PRESIDENT)
        response = post(
            login_as(president, AREA_ADMIN), target, "assign", R.TREASURER, actor=president
        )
        assert response.status_code == 404
        assert active_roles(target) == {R.INSTRUCTOR}

    def test_personal_account_is_not_an_admin_target(self, pair, login_as, personal_account):
        admin, _ = pair
        response = login_as(admin, AREA_ADMIN).get(reverse(URL, args=[personal_account.pk]))
        assert response.status_code == 404

    def test_the_accounts_list_links_to_roles(self, pair, login_as):
        admin, target = pair
        html = login_as(admin, AREA_ADMIN).get(reverse("administration:accounts")).content.decode()
        assert reverse(URL, args=[target.pk]) in html
        assert "Instructor" in html


class TestSummary:
    def test_summary_before_saving(self, pair, login_as):
        # RN-RP-07: què canvia i quins comptes queden afectats, abans de desar res.
        admin, target = pair
        url = reverse(URL, args=[target.pk])
        response = login_as(admin, AREA_ADMIN).get(url, {"action": "assign", "role": R.SECRETARY})
        html = response.content.decode()
        assert "Secretaria" in html and "bernat.instr" in html
        assert 'name="code"' in html and 'name="note"' in html
        assert active_roles(target) == {R.INSTRUCTOR}

    def test_second_treasurer_warning_and_it_saves(self, pair, make_admin, login_as):
        # CA-RP-14
        admin, target = pair
        make_admin(R.TREASURER)
        session = login_as(admin, AREA_ADMIN)
        url = reverse(URL, args=[target.pk])
        summary = session.get(url, {"action": "assign", "role": R.TREASURER})
        assert escape(str(SECOND_TREASURER)) in summary.content.decode()
        post(session, target, "assign", R.TREASURER, actor=admin)
        assert R.TREASURER in active_roles(target)

    def test_last_role_warns_about_sessions(self, pair, login_as):
        admin, target = pair
        url = reverse(URL, args=[target.pk])
        html = login_as(admin, AREA_ADMIN).get(url, {"action": "remove", "role": R.INSTRUCTOR})
        assert "se&#x27;n tancaran les sessions" in html.content.decode()

    def test_unknown_role_shows_no_summary(self, pair, login_as):
        admin, target = pair
        url = reverse(URL, args=[target.pk])
        html = login_as(admin, AREA_ADMIN).get(url, {"action": "assign", "role": "member"})
        assert 'name="code"' not in html.content.decode()


class TestAssignAndRemove:
    def test_assign_with_code_and_note(self, pair, login_as):
        admin, target = pair
        response = post(login_as(admin, AREA_ADMIN), target, "assign", R.SECRETARY, actor=admin)
        assert response.status_code == 302
        assert active_roles(target) == {R.INSTRUCTOR, R.SECRETARY}
        # RN-RP-08: qui, compte, rol, valor nou i la nota.
        entry = AuditEntry.objects.get(action=audit.Action.ROLE_ASSIGNED, new_value=R.SECRETARY)
        assert entry.reason == NOTE
        assert entry.actor_account_id == admin.pk

    def test_remove_keeps_the_old_value_and_the_note(self, pair, make_admin, login_as):
        admin, target = pair
        AccountRole.objects.create(admin_account=target, role=Role.objects.get(code=R.SECRETARY))
        post(login_as(admin, AREA_ADMIN), target, "remove", R.INSTRUCTOR, actor=admin)
        assert active_roles(target) == {R.SECRETARY}
        entry = AuditEntry.objects.get(action=audit.Action.ROLE_REMOVED)
        assert (entry.old_value, entry.reason) == (R.INSTRUCTOR, NOTE)

    @pytest.mark.parametrize("code", ["", "000000"])
    def test_wrong_code_changes_nothing(self, pair, login_as, code):
        admin, target = pair
        response = post(
            login_as(admin, AREA_ADMIN), target, "assign", R.SECRETARY, actor=admin, code=code
        )
        assert response.status_code == 200
        assert response.context["form"].has_error("code")
        assert active_roles(target) == {R.INSTRUCTOR}
        assert not AuditEntry.objects.filter(action=audit.Action.ROLE_ASSIGNED).exists()

    def test_a_change_already_made_saves_nothing(self, pair, login_as):
        admin, target = pair
        response = post(login_as(admin, AREA_ADMIN), target, "assign", R.INSTRUCTOR, actor=admin)
        html = response.content.decode()
        assert "No s'ha desat res." in html and "ja no es pot fer" in html
        assert not AuditEntry.objects.filter(action=audit.Action.ROLE_ASSIGNED).exists()

    def test_note_and_review_are_required(self, pair, login_as):
        admin, target = pair
        session = login_as(admin, AREA_ADMIN)
        response = post(session, target, "assign", R.SECRETARY, actor=admin, note="", reviewed="")
        form = response.context["form"]
        assert form.has_error("note") and form.has_error("reviewed")
        assert active_roles(target) == {R.INSTRUCTOR}

    def test_last_operational_admin_cannot_lose_the_role(self, pair, login_as):
        # CA-RP-06: el resum ho diu i el servidor ho rebutja igualment.
        admin, _ = pair
        session = login_as(admin, AREA_ADMIN)
        url = reverse(URL, args=[admin.pk])
        summary = session.get(url, {"action": "remove", "role": R.ADMINISTRATOR}).content.decode()
        assert "administrador operatiu" in summary
        assert 'name="code"' not in summary
        response = post(session, admin, "remove", R.ADMINISTRATOR, actor=admin)
        assert escape(str(NO_OPERATIONAL_ADMIN)) in response.content.decode()
        assert R.ADMINISTRATOR in active_roles(admin)

    def test_losing_the_only_role_ends_its_sessions(self, pair, login_as):
        # CA-RP-11 (sense la part de «sense responsable», que és del 02).
        admin, target = pair
        theirs = client_for(target)
        assert theirs.get(reverse("administration:home")).status_code == 200
        post(login_as(admin, AREA_ADMIN), target, "remove", R.INSTRUCTOR, actor=admin)
        target.refresh_from_db()
        assert target.status == target.Status.ACTIVE
        assert theirs.get(reverse("administration:home")).status_code in (302, 401)

    def test_notifies_admins_the_affected_account_and_the_president(
        self, pair, make_admin, login_as
    ):
        # RN-RP-09: què ha canviat i qui ho ha fet, sense dades de terceres persones.
        admin, target = pair
        admin.notification_email = "anna@example.org"
        admin.save()
        president = make_admin(R.PRESIDENT)
        president.notification_email = "presidencia@example.org"
        president.save()
        treasurer = make_admin(R.TREASURER)
        treasurer.notification_email = "tresoreria@example.org"
        treasurer.save()
        post(login_as(admin, AREA_ADMIN), target, "assign", R.SECRETARY, actor=admin)
        sent = OutgoingEmail.objects.filter(template="avis-canvi-rol")
        assert set(sent.values_list("to_address", flat=True)) == {
            "anna@example.org",
            "bernat@example.org",
            "presidencia@example.org",
        }
        body = sent.first().body_text
        assert "bernat.instr" in body and "anna.admin" in body and "Secretaria" in body
