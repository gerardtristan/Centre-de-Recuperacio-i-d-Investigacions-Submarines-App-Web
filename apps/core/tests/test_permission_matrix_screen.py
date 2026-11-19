"""Pantalla de l'editor de permisos (T-RP-03; RN-RP-06 i 07; CA-RP-03, 04 i 09). El servei és a
`test_permission_matrix.py`. Només dades inventades."""

from datetime import timedelta

import pyotp
import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts import totp
from apps.accounts.models import TotpDevice
from apps.accounts.security import AREA_ADMIN
from apps.core import audit, permission_matrix
from apps.core.models import AuditEntry, OutgoingEmail, PermissionMatrixVersion, Role
from apps.core.permission_catalog import CATALOG

pytestmark = pytest.mark.django_db
R = Role.Code
URL = reverse("administration:permission_matrix")
NOTE = "Acord de junta del 18/11"
MONEY = "core.departments.manage"  # M7: diners, la secretaria no el té d'inici


def code_for(account, steps_ahead=1):
    device = TotpDevice.objects.get(account=account)
    moment = timezone.now() + timedelta(seconds=30 * steps_ahead)
    return pyotp.TOTP(totp.secret_of(device)).at(moment)


def cell(role, code):
    return f"c|{role}|{code}"


def post(session, cells, *, actor, step="save", note=NOTE, code=None, version=None):
    data = {"step": step, "note": note, "reviewed": "on"}
    data["version"] = permission_matrix.latest_version() if version is None else version
    data["code"] = code if code is not None else code_for(actor)
    data.update(cells)
    return session.post(URL, data)


def stored():
    return permission_matrix.current_cells()


@pytest.fixture
def admin(make_admin):
    account = make_admin(R.ADMINISTRATOR, username="anna.admin")
    account.notification_email = "anna@example.org"
    account.save()
    return account


@pytest.fixture
def session(admin, login_as):
    return login_as(admin, AREA_ADMIN)


class TestWhoCanOpenIt:
    @pytest.mark.parametrize("role", [code for code in R.values if code != R.ADMINISTRATOR])
    def test_every_other_role_gets_not_found(self, make_admin, login_as, role):
        # CA-RP-03: només el rol administrador (M3b, protegit). El President tampoc.
        other = make_admin(role)
        client = login_as(other, AREA_ADMIN)
        assert client.get(URL).status_code == 404
        before = stored()
        response = post(client, {cell(R.SECRETARY, MONEY): "all"}, actor=other)
        assert response.status_code == 404
        assert stored() == before

    def test_the_administrator_opens_it_with_the_menu_entry(self, session):
        response = session.get(URL)
        assert response.status_code == 200
        assert "no-cache" in response["Cache-Control"]
        html = response.content.decode()
        assert f'href="{URL}"' in html
        # CA-RP-09: les files protegides no tenen cap control.
        assert cell(R.ADMINISTRATOR, "core.accounts.manage") not in html
        assert cell(R.SECRETARY, MONEY) in html


class TestSummary:
    def test_preview_shows_the_change_and_saves_nothing(self, session, admin, make_admin):
        make_admin(R.SECRETARY, username="sara.secr")
        before = stored()
        response = post(session, {cell(R.SECRETARY, MONEY): "all"}, actor=admin, step="preview")
        html = response.content.decode()
        assert "sara.secr" in html  # RN-RP-07: comptes afectats
        assert "abans: —" in html
        assert "diners, dades personals o camp sensible" in html
        assert stored() == before
        assert not OutgoingEmail.objects.exists()

    def test_back_to_initial_marks_the_difference(self, session, admin):
        permission_matrix.save(
            {**stored(), (R.SECRETARY, MONEY): "all"},
            by=admin,
            note=NOTE,
            base_version=permission_matrix.latest_version(),
        )
        response = session.post(
            f"{URL}?modul=core", {"step": "initial", "version": permission_matrix.latest_version()}
        )
        assert "abans: Sí" in response.content.decode()
        assert stored()[(R.SECRETARY, MONEY)] == "all"  # encara no s'ha desat


class TestSaving:
    def test_without_totp_or_note_nothing_is_saved(self, session, admin):
        # CA-RP-04
        before, versions = stored(), PermissionMatrixVersion.objects.count()
        post(session, {cell(R.SECRETARY, MONEY): "all"}, actor=admin, code="000000")
        post(session, {cell(R.SECRETARY, MONEY): "all"}, actor=admin, note="")
        assert stored() == before
        assert PermissionMatrixVersion.objects.count() == versions

    def test_a_valid_change_redirects_with_the_version(self, session, admin):
        last = permission_matrix.latest_version()
        response = post(session, {cell(R.SECRETARY, MONEY): "all"}, actor=admin)
        assert response.status_code == 302
        assert permission_matrix.latest_version() == last + 1
        assert stored()[(R.SECRETARY, MONEY)] == "all"


class TestRejected:
    def assert_nothing_saved(self, response, before, text):
        assert response.status_code == 200
        assert text in response.content.decode()
        assert stored() == before
        assert not AuditEntry.objects.filter(action=audit.Action.PERMISSION_CHANGED).exists()

    def test_a_permission_without_what_it_requires(self, session, admin):
        # CA-RP-07 (RN-RP-03): no s'afegeix cap permís sol.
        code = "core.charges.record_manual"
        assert CATALOG[code].requires == ("treasury.view",)
        before = stored()
        response = post(session, {cell(R.SECRETARY, code): "all"}, actor=admin)
        self.assert_nothing_saved(response, before, "demana també")

    def test_a_protected_cell_by_direct_request(self, session, admin):
        # CA-RP-09 i CA-RP-03: gestionar usuaris i rols al President.
        before = stored()
        response = post(session, {cell(R.PRESIDENT, "core.accounts.manage"): "all"}, actor=admin)
        self.assert_nothing_saved(response, before, "cel·la protegida")

    def test_a_matrix_changed_meanwhile(self, session, admin):
        before = stored()
        response = post(
            session,
            {cell(R.SECRETARY, MONEY): "all"},
            actor=admin,
            version=permission_matrix.latest_version() - 1,
        )
        self.assert_nothing_saved(response, before, "Un altre administrador ha canviat")


class TestFilters:
    def test_every_catalog_module_has_a_filter(self):
        from apps.core.views.permission_matrix import MODULES

        assert {perm.module for perm in CATALOG.values()} <= set(MODULES)

    def test_one_module_and_one_role(self, session):
        html = session.get(URL, {"modul": "members", "rol": R.TREASURER}).content.decode()
        assert cell(R.TREASURER, "members.fees.generate") in html
        assert cell(R.SECRETARY, "members.fees.generate") not in html
        assert cell(R.TREASURER, MONEY) not in html

    def test_cells_not_shown_are_kept(self, session, admin):
        # Desar des d'un filtre no toca la resta de la matriu.
        before = stored()
        session.post(
            f"{URL}?modul=core&rol={R.SECRETARY}",
            {
                "step": "save",
                "note": NOTE,
                "reviewed": "on",
                "code": code_for(admin),
                "version": permission_matrix.latest_version(),
                cell(R.SECRETARY, MONEY): "all",
            },
        )
        assert stored() == {**before, (R.SECRETARY, MONEY): "all"}

    def test_back_to_initial_only_for_what_is_shown(self, session, admin):
        changed = {**stored(), (R.SECRETARY, MONEY): "all", (R.TREASURER, MONEY): "all"}
        permission_matrix.save(
            changed, by=admin, note=NOTE, base_version=permission_matrix.latest_version()
        )
        response = session.post(
            f"{URL}?modul=core&rol={R.SECRETARY}",
            {"step": "initial", "version": permission_matrix.latest_version()},
        )
        assert len(response.context["changes"]) == 1
