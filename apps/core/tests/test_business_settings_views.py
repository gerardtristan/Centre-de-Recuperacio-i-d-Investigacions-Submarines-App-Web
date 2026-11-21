"""Pantalla base d'ajustos (T-AJ-02; 055, RN-AJ-05, CA-AJ-01, 02 i 05; RN-RP-22 i RN-RP-03).
Només dades inventades. L'apartat «proves» i les seves claus són de prova."""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.core import business_settings as service
from apps.core import permissions
from apps.core.models import AuditEntry, Role, RolePermission, Setting, SettingVersion
from apps.core.permission_catalog import CATALOG, Permission
from apps.core.tests.test_guest_links import admin_client
from apps.core.views.business_settings import ValueForm

pytestmark = pytest.mark.django_db

R = Role.Code
T = Setting.ValueType
DAYS, FEE, LIST = "proves.v_days", "proves.v_fee", "proves.v_list"


@pytest.fixture(autouse=True)
def section(monkeypatch):
    """Secretaria: «Sí» de l'apartat. Tresorer: «Cons.» i editar només DAYS. President:
    «Cons.». Responsable de cursos: res."""
    code = service.section_code("proves")
    edit = service.permission_code(DAYS)
    extra = {
        code: Permission(code, "TEST-S", "Ajustos de prova", allowed_scopes=("all", "read")),
        edit: Permission(edit, "TEST-1", "Dies de prova", requires=(code,)),
    }
    monkeypatch.setattr(permissions, "CATALOG", {**CATALOG, **extra})
    cells = [(R.SECRETARY, code, "all"), (R.TREASURER, code, "read"), (R.TREASURER, edit, "all"),
             (R.PRESIDENT, code, "read")]  # fmt: skip
    for role, perm, scope in cells:
        RolePermission.objects.create(
            role=Role.objects.get(code=role), permission_code=perm, scope=scope
        )
    Setting.objects.create(key=DAYS, module="proves", value_type=T.INTEGER, initial_value=15,
                           min_value=1, max_value=90)  # fmt: skip
    Setting.objects.create(key=FEE, module="proves", value_type=T.CENTS, initial_value=3500,
                           min_value=1, affects_money=True, effective_dated=True)  # fmt: skip
    Setting.objects.create(key=LIST, module="proves", value_type=T.INTEGER_LIST,
                           initial_value=[30, 7], min_value=1, max_value=60)  # fmt: skip


def section_url():
    return reverse("administration:settings_section", args=["proves"])


def detail_url(key):
    return reverse("administration:setting_detail", args=["proves", key])


@pytest.mark.parametrize("role", [R.COURSES_MANAGER, R.MEMBER])
def test_without_the_section_permission_every_screen_is_not_found(make_admin, role):
    client = admin_client(make_admin(role))
    assert client.get(section_url()).status_code == 404
    assert client.get(detail_url(DAYS)).status_code == 404
    assert client.post(detail_url(DAYS), {"value": "10"}).status_code == 404
    assert not SettingVersion.objects.exists()


def test_unknown_section_or_key_of_another_section_is_not_found(make_admin):
    client = admin_client(make_admin(R.SECRETARY))
    assert client.get(reverse("administration:settings_section", args=["nope"])).status_code == 404
    assert client.get(detail_url("proves.no_existeix")).status_code == 404
    Setting.objects.create(key="payments.v_x", module="payments", value_type=T.INTEGER,
                           initial_value=1)  # fmt: skip
    assert client.get(detail_url("payments.v_x")).status_code == 404


def test_rn_aj_05_list_shows_current_scheduled_initial_and_range(make_admin):
    secretary = make_admin(R.SECRETARY)
    service.change(DAYS, 20, secretary)
    service.change(FEE, 4000, secretary, "Puja aprovada per la junta (prova)",
                   timezone.localdate() + datetime.timedelta(days=3))  # fmt: skip
    html = admin_client(secretary).get(section_url()).content.decode()
    assert "Ajustos de prova" in html and "Dies de prova" in html
    assert "<strong>20</strong>" in html and "de 1 a 90" in html
    assert "40,00 € des del" in html and "35,00 €" in html  # programat i vigent
    assert "30, 7" in html


def test_rn_rp_22_read_only_sees_values_but_no_form_and_a_post_is_recorded(make_admin):
    president = make_admin(R.PRESIDENT)
    client = admin_client(president)
    page = client.get(detail_url(DAYS))
    assert page.status_code == 200 and b'<form class="formulari' not in page.content
    assert b"Historial: Dies de prova" in client.get(section_url()).content
    assert client.post(detail_url(DAYS), {"value": "10"}).status_code == 404
    assert not SettingVersion.objects.exists()
    entry = AuditEntry.objects.get(action=service.ACTION_DENIED)
    assert (entry.actor_account, entry.field) == (president, DAYS)


def test_rn_rp_03_edit_permission_covers_only_its_value(make_admin):
    client = admin_client(make_admin(R.TREASURER))
    assert b"Canvia: Dies de prova" in client.get(section_url()).content
    assert client.post(detail_url(DAYS), {"value": "10", "note": ""}).status_code == 302
    assert service.get(DAYS) == 10
    assert client.post(detail_url(LIST), {"value": "10"}).status_code == 404
    assert service.get(LIST) == [30, 7]


def test_ca_aj_01_out_of_range_is_shown_and_nothing_saved(make_admin):
    client = admin_client(make_admin(R.SECRETARY))
    page = client.post(detail_url(DAYS), {"value": "91"})
    assert page.status_code == 200
    assert "No s'ha desat res." in page.content.decode()
    assert "entre 1 i 90" in page.content.decode()
    assert not SettingVersion.objects.exists()


def test_money_value_needs_date_and_note_and_is_typed_in_euros(make_admin):
    client = admin_client(make_admin(R.SECRETARY))
    assert b"Cal la data" in client.post(detail_url(FEE), {"value": "40"}).content
    tomorrow = (timezone.localdate() + datetime.timedelta(days=1)).isoformat()
    response = client.post(
        detail_url(FEE), {"value": "40,50", "effective_from": tomorrow, "note": "Prova"}
    )
    assert response.status_code == 302
    assert SettingVersion.objects.get().value == 4050


def test_ca_aj_05_history_shows_who_previous_new_and_note(make_admin):
    secretary = make_admin(R.SECRETARY, username="secretaria.prova")
    client = admin_client(secretary)
    client.post(detail_url(LIST), {"value": "20; 5", "note": "Menys dies (prova)"})
    assert service.get(LIST) == [20, 5]
    html = client.get(detail_url(LIST)).content.decode()
    assert "secretaria.prova" in html and "30, 7" in html and "20, 5" in html
    assert "Menys dies (prova)" in html


@pytest.mark.parametrize(
    ("kind", "extra", "posted", "expected"),
    [
        (T.BOOLEAN, {}, "0", False),
        (T.CHOICE, {"choices": ["club", "soci"]}, "soci", "soci"),
        (T.DAY_MONTH, {}, "10-01", "10-01"),
        (T.TEXT, {"max_length": 20}, "Hola", "Hola"),
        (T.INTEGER_LIST, {}, "1, x", None),
    ],
)
def test_form_field_follows_the_value_type(kind, extra, posted, expected):
    setting = Setting(key="proves.v", module="proves", value_type=kind, initial_value=1, **extra)
    form = ValueForm(setting, {"value": posted})
    assert form.is_valid() is (expected is not None)
    if expected is not None:
        assert form.cleaned_data["value"] == expected


def test_menu_shows_settings_only_with_a_section_permission(make_admin):
    home = reverse("administration:home")
    # Configuració inicial real: «Cons.» de pagaments per al tresorer i l'administrador.
    assert b"/ajustos/" in admin_client(make_admin(R.ADMINISTRATOR)).get(home).content
    # L'instructor no té cap apartat d'ajustos (el responsable de cursos té el del 02, T-M02-28).
    assert b"/ajustos/" not in admin_client(make_admin(R.INSTRUCTOR)).get(home).content
    index = reverse("administration:settings")
    assert admin_client(make_admin(R.INSTRUCTOR)).get(index).status_code == 404
    assert b"Ajustos de prova" in admin_client(make_admin(R.PRESIDENT)).get(index).content


def test_menu_without_any_settings_section_hides_the_entry_instead_of_failing(
    make_admin, monkeypatch
):
    # Revisió de la PR #48: sense cap apartat al catàleg, la ruta no té cap grup de permisos.
    from apps.accounts import navigation

    monkeypatch.setitem(navigation.BASE_ROUTES, "administration:settings", ())
    home = admin_client(make_admin(R.ADMINISTRATOR)).get(reverse("administration:home"))
    assert home.status_code == 200 and b"/ajustos/" not in home.content
