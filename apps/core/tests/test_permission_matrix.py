"""Servei de l'editor de permisos (T-RP-03; 059 i 060; RN-RP-03, 07 a 11; CA-RP-03, 04, 05, 07, 09
i 10). La pantalla és a `test_permission_matrix_screen.py`. Només dades inventades."""

import time

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import Client
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import audit
from apps.core import permission_matrix as matrix
from apps.core.models import AuditEntry, OutgoingEmail, PermissionMatrixVersion, Role
from apps.core.permission_catalog import CATALOG
from apps.core.permissions import has_perm

pytestmark = pytest.mark.django_db
R = Role.Code
NOTE = "Acord de junta del 18/11"
MONEY = "core.departments.manage"  # M7: diners, la secretaria no el té d'inici


def save(by, changes, *, note=NOTE, version=None):
    proposed = matrix.current_cells()
    for key, scope in changes.items():
        if scope is None:
            proposed.pop(key, None)
        else:
            proposed[key] = scope
    base = matrix.latest_version() if version is None else version
    return matrix.save(proposed, by=by, note=note, base_version=base)


@pytest.fixture
def admin(make_admin):
    account = make_admin(R.ADMINISTRATOR, username="anna.admin")
    account.notification_email = "anna@example.org"
    account.save()
    return account


def test_money_cell_starts_empty_for_the_secretary():
    assert R.SECRETARY not in CATALOG[MONEY].initial
    assert CATALOG[MONEY].touches_money


@pytest.mark.parametrize("role", [code for code in R.values if code != R.ADMINISTRATOR])
def test_only_the_administrator(make_admin, role):
    # CA-RP-03: M3b és protegit i exclusiu de l'administrador. El President tampoc.
    with pytest.raises(Http404):
        save(make_admin(role), {(R.SECRETARY, MONEY): "all"})


def test_a_valid_change(admin, make_admin, django_capture_on_commit_callbacks):
    # CA-RP-05 i RN-RP-08, 09: versió, una entrada per cel·la i correu.
    secretary = make_admin(R.SECRETARY, username="sara.secr")
    secretary.notification_email = "sara@example.org"
    secretary.save()
    president = make_admin(R.PRESIDENT)
    president.notification_email = "pres@example.org"
    president.save()
    make_admin(R.INSTRUCTOR)  # un compte no afectat
    last = matrix.latest_version()
    with django_capture_on_commit_callbacks(execute=True):
        version = save(admin, {(R.SECRETARY, MONEY): "all"})
    assert has_perm(secretary, MONEY)
    assert version.number == last + 1
    assert (version.changed_by, version.note) == (admin, NOTE)
    assert version.diff == [
        {"role": R.SECRETARY, "permission": MONEY, "before": None, "after": "all"}
    ]
    assert version.affected_accounts == [secretary.pk]
    entry = AuditEntry.objects.get(action=audit.Action.PERMISSION_CHANGED)
    assert (entry.old_value, entry.new_value, entry.reason) == (None, "all", NOTE)
    assert entry.details == {"role": R.SECRETARY, "permission": MONEY}
    sent = OutgoingEmail.objects.filter(template="avis-canvi-permisos")
    assert set(sent.values_list("to_address", flat=True)) == {
        "anna@example.org",
        "sara@example.org",
        "pres@example.org",
    }
    body = sent.first().body_text
    assert "anna.admin" in body and "Secretaria" in body and "M7" in body and NOTE in body


def test_removing_a_cell(admin):
    code = "core.audit.view"  # M6: administrador d'inici
    save(admin, {(R.ADMINISTRATOR, code): None})
    assert (R.ADMINISTRATOR, code) not in matrix.current_cells()
    assert not has_perm(admin, code)


def test_back_to_initial_is_one_more_change(admin):
    save(admin, {(R.SECRETARY, MONEY): "all"})
    matrix.save(matrix.initial_cells(), by=admin, note=NOTE, base_version=matrix.latest_version())
    assert matrix.current_cells() == matrix.initial_cells()
    assert PermissionMatrixVersion.objects.filter(note=NOTE).count() == 2


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        # CA-RP-07 (RN-RP-03): no s'afegeix cap permís sol.
        ({(R.SECRETARY, "core.charges.record_manual"): "all"}, "demana també"),
        # CA-RP-09 i CA-RP-03: gestionar usuaris i rols al President.
        ({(R.PRESIDENT, "core.accounts.manage"): "all"}, "regla protegida"),
        ({(R.MEMBER, MONEY): "all"}, "rols de gestió"),
        ({(R.SECRETARY, MONEY): "own_sessions"}, "no admet l"),
        ({}, "No hi ha cap canvi"),
    ],
)
def test_rejected(admin, changes, message):
    before, versions = matrix.current_cells(), matrix.latest_version()
    with pytest.raises(ValidationError) as exc:
        save(admin, changes)
    assert message in " ".join(exc.value.messages)
    assert matrix.current_cells() == before
    assert matrix.latest_version() == versions
    assert not AuditEntry.objects.filter(action=audit.Action.PERMISSION_CHANGED).exists()


def test_without_a_note(admin):
    # CA-RP-04 (la part del servei; el TOTP el comprova la vista)
    with pytest.raises(ValidationError):
        save(admin, {(R.SECRETARY, MONEY): "all"}, note="  ")


def test_a_matrix_changed_meanwhile(admin):
    with pytest.raises(ValidationError, match="Un altre administrador"):
        save(admin, {(R.SECRETARY, MONEY): "all"}, version=matrix.latest_version() - 1)


class TestSessions:
    """CA-RP-10 (RN-RP-11) i P-401."""

    home = reverse("administration:home")

    def test_widening_money_closes_the_sessions_of_the_role(
        self, admin, make_admin, client_factory
    ):
        secretary = client_factory(make_admin(R.SECRETARY))
        instructor = client_factory(make_admin(R.INSTRUCTOR))
        own = client_factory(admin)
        save(admin, {(R.SECRETARY, MONEY): "all"})
        assert secretary.get(self.home).status_code == 401
        assert instructor.get(self.home).status_code == 200
        assert own.get(self.home).status_code == 200  # P-401: qui desa acaba d'escriure el TOTP

    def test_narrowing_keeps_the_sessions(self, admin, make_admin, client_factory):
        save(admin, {(R.SECRETARY, MONEY): "all"})
        secretary = client_factory(make_admin(R.SECRETARY))
        save(admin, {(R.SECRETARY, MONEY): None})
        assert secretary.get(self.home).status_code == 200


@pytest.fixture
def client_factory():
    def make(account):
        client = Client()
        client.force_login(account)
        data = client.session
        data[AREA_SESSION_KEY] = AREA_ADMIN
        data[AUTH_AT_SESSION_KEY] = time.time()
        data.save()
        return client

    return make


def test_widens():
    def cell(code, before, after):
        return {"role": R.SECRETARY, "permission": code, "before": before, "after": after}

    assert matrix.widens(cell(MONEY, None, "all"))
    assert not matrix.widens(cell(MONEY, "all", None))
    assert not matrix.widens(cell("core.under_construction.view", None, "all"))
