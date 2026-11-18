"""Desactivar un compte d'administrador des de la pantalla, també el propi (T-RP-02d; RN-RP-13 i
20; CA-RP-06 i 16; CA-13.2). Només dades inventades."""

import pytest
from django.db import OperationalError
from django.urls import reverse
from django.utils.html import escape

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN
from apps.core import audit, roles
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

    def test_already_disabled_saves_nothing_and_keeps_the_code(self, admins, make_admin, login_as):
        anna, bernat = admins
        bernat.status = Account.Status.DISABLED
        bernat.save()
        session = login_as(anna, AREA_ADMIN)
        code = code_for(anna)
        response = post(session, bernat, actor=anna, code=code)
        assert escape("el canvi ja estava fet") in response.content.decode()
        assert not AuditEntry.objects.filter(action=audit.Action.ADMIN_ACCOUNT_DISABLED).exists()
        # El codi no s'ha gastat: el mateix serveix per a un canvi que sí que es pot fer.
        carla = make_admin(R.ADMINISTRATOR)
        assert post(session, carla, actor=anna, code=code).status_code == 302
        assert status_of(carla) == Account.Status.DISABLED

    def test_done_by_someone_else_after_the_code_says_it_is_used_up(
        self, admins, login_as, monkeypatch
    ):
        # Revisió de #216, punt 5: la cursa amb un altre administrador, després del codi.
        anna, bernat = admins

        def already(*a, **k):
            raise roles.AlreadyDone(roles.ALREADY_DONE)

        monkeypatch.setattr(roles, "deactivate_admin_account", already)
        html = post(login_as(anna, AREA_ADMIN), bernat, actor=anna).content.decode()
        assert escape(str(roles.ALREADY_DONE)) in html
        assert "El codi TOTP ja s&#x27;ha fet servir" in html
        assert 'name="code"' not in html

    def test_a_database_conflict_is_a_message_not_an_error_page(
        self, admins, login_as, monkeypatch
    ):
        # Punt 2: si tot i l'ordre dels bloquejos la base de dades se'n queixa, un missatge clar.
        anna, bernat = admins

        def conflict(*a, **k):
            raise OperationalError("deadlock detected")

        monkeypatch.setattr(roles, "deactivate_admin_account", conflict)
        response = post(login_as(anna, AREA_ADMIN), bernat, actor=anna)
        assert response.status_code == 200
        html = response.content.decode()
        assert "No s'ha desat res." in html and "torna-ho a provar" in html
        assert status_of(bernat) == Account.Status.ACTIVE

    def test_summary_names_the_affected_account_in_the_notice(self, admins, login_as):
        anna, bernat = admins
        html = login_as(anna, AREA_ADMIN).get(reverse(URL, args=[bernat.pk])).content.decode()
        assert "rol administrador i el compte afectat" in html

    def test_a_disabled_account_is_not_offered_new_roles(self, admins, login_as):
        # Punt 7: ni l'opció a la pantalla ni el canvi al servidor.
        anna, bernat = admins
        bernat.status = Account.Status.DISABLED
        bernat.save()
        session = login_as(anna, AREA_ADMIN)
        roles_url = reverse("administration:account_roles", args=[bernat.pk])
        html = session.get(roles_url).content.decode()
        assert "Assigna un rol" not in html and reverse(URL, args=[bernat.pk]) not in html
        data = {"action": "assign", "role": R.SECRETARY, "note": NOTE, "reviewed": "on"}
        session.post(roles_url, {**data, "code": code_for(anna)})
        assert not bernat.role_assignments.filter(role__code=R.SECRETARY).exists()


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

    def test_last_operational_admin_keeps_the_code(self, make_admin, login_as):
        # Punt 6: el codi d'un intent impossible serveix quan ja es pot fer.
        only = make_admin(R.ADMINISTRATOR)
        session = login_as(only, AREA_ADMIN)
        code = code_for(only)
        post(session, only, actor=only, code=code)
        make_admin(R.ADMINISTRATOR)
        assert post(session, only, actor=only, code=code).status_code == 302
        assert status_of(only) == Account.Status.DISABLED

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
        # Punt 4: la pàgina d'entrada és pública; el missatge no diu que el compte s'ha desactivat.
        assert "Has sortit de l&#x27;administració." in login_page
        assert "desactivat" not in login_page
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
        # Punt 3: només s'avisa els altres administradors.
        assert "rol administrador i el compte afectat" not in html
        assert "els altres comptes amb el rol administrador" in html

    def test_only_the_logout_message_reaches_the_login_page(self, admins, login_as):
        # Punt 4: un missatge pendent d'una altra pantalla no surt a l'entrada.
        from django.contrib.messages import constants
        from django.contrib.messages.storage.cookie import CookieStorage
        from django.http import HttpRequest, HttpResponse

        anna, _ = admins
        session = login_as(anna, AREA_ADMIN)
        storage = CookieStorage(HttpRequest())
        storage.add(constants.SUCCESS, "Missatge d'una altra pantalla")
        carrier = HttpResponse()
        storage.update(carrier)
        session.cookies[storage.cookie_name] = carrier.cookies[storage.cookie_name].value
        response = post(session, anna, actor=anna)
        login_page = session.get(response["Location"]).content.decode()
        assert "Has sortit de l&#x27;administració." in login_page
        assert "una altra pantalla" not in login_page
        assert "Missatge" not in session.get(reverse("administration:login")).content.decode()
