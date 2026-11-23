"""Ajustos del 06 a la pantalla comuna (T-M06-20; M06-6, «Valors configurables»; VC-39 a 42;
CA-M06-26; RN-RP-22). Per valor: fora de rang es rebutja, el canvi queda al registre i un rol
sense permís rep «no trobat». Cap valor del 06 és de diners. Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse

from apps.core import business_settings
from apps.core.models import AuditEntry, Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.licences import reminders
from apps.licences.tests.test_reminders import EXT, at

pytestmark = pytest.mark.django_db
R = Role.Code

# Clau: (rol que la canvia, valor vàlid, valors fora de rang o de tipus).
VALUES = {
    "licences.non_members_enabled": (R.ADMINISTRATOR, True, ["potser"]),
    "licences.day_enabled": (R.ADMINISTRATOR, True, ["potser"]),
    "licences.reminder_days": (R.SECRETARY, [45, 15, 3], [[0], [121], [60, 0]]),
    "licences.to_renew_days": (R.SECRETARY, 45, [0, 121]),
    "licences.next_year_opens_on": (R.SECRETARY, "11-15", ["09-30", "02-01"]),
}


def test_the_section_has_the_five_values_with_their_initial_value():
    settings = Setting.objects.filter(module="licences")
    assert {s.key: s.initial_value for s in settings} == {
        "licences.non_members_enabled": False,
        "licences.day_enabled": False,
        "licences.reminder_days": [60, 30, 7],
        "licences.to_renew_days": 60,
        "licences.next_year_opens_on": "12-01",
    }
    assert not any(s.affects_money for s in settings)  # cap data d'entrada en vigor


@pytest.mark.parametrize("key", VALUES)
def test_out_of_range_is_rejected_and_nothing_is_saved(make_admin, key):  # noqa: F811
    role, _valid, wrong = VALUES[key]
    account = make_admin(role)
    for value in wrong:
        with pytest.raises(ValidationError):
            business_settings.change(key, value, account, "Prova")
    assert not Setting.objects.get(key=key).versions.exists()


@pytest.mark.parametrize("key", VALUES)
def test_a_valid_change_is_recorded_with_the_previous_value(make_admin, key):  # noqa: F811
    role, valid, _wrong = VALUES[key]
    account = make_admin(role)
    previous = business_settings.get(key)
    business_settings.change(key, valid, account, "Prova")
    assert business_settings.get(key) == valid
    entry = AuditEntry.objects.filter(action=business_settings.ACTION_CHANGED, field=key).get()
    assert (entry.actor_account_id, entry.old_value, entry.new_value) == (
        account.pk, previous, valid,
    )  # fmt: skip


@pytest.mark.parametrize("key", VALUES)
def test_the_other_role_that_sees_the_section_gets_not_found(make_admin, key):  # noqa: F811
    role, valid, _wrong = VALUES[key]
    other = make_admin(R.SECRETARY if role == R.ADMINISTRATOR else R.ADMINISTRATOR)
    with pytest.raises(Http404):
        business_settings.change(key, valid, other, "Prova")
    assert AuditEntry.objects.filter(action=business_settings.ACTION_DENIED, field=key).exists()


@pytest.mark.parametrize("role", [R.TREASURER, R.COURSES_MANAGER, R.PRESIDENT, R.BOARD])
def test_a_role_without_the_section_gets_not_found_on_the_screen(make_admin, role):  # noqa: F811
    client = admin_client(make_admin(role))
    url = reverse("administration:settings_section", args=["licences"])
    assert client.get(url).status_code == 404
    detail = reverse("administration:setting_detail", args=["licences", reminders.REMINDER_DAYS])
    assert client.post(detail, {"value": "45, 15, 3", "note": "Prova"}).status_code == 404
    assert business_settings.get(reminders.REMINDER_DAYS) == [60, 30, 7]


def test_each_role_can_edit_only_its_values_on_the_screen(make_admin):  # noqa: F811
    url = reverse("administration:settings_section", args=["licences"])
    for role, mine in (
        (R.SECRETARY, {"licences.reminder_days", "licences.to_renew_days",
                       "licences.next_year_opens_on"}),
        (R.ADMINISTRATOR, {"licences.non_members_enabled", "licences.day_enabled"}),
    ):  # fmt: skip
        rows = admin_client(make_admin(role)).get(url).context["rows"]
        assert len(rows) == 5
        assert {row["setting"].key for row in rows if row["editable"]} == mine


def test_ca_m06_26_the_secretary_changes_the_trams_on_the_screen(make_admin, make_licence):  # noqa: F811
    holder = make_licence(**EXT)
    client = admin_client(make_admin(R.SECRETARY))
    detail = reverse("administration:setting_detail", args=["licences", reminders.REMINDER_DAYS])
    for wrong in ("0, 15, 3", "121"):
        client.post(detail, {"value": wrong, "note": "Prova"})
        assert business_settings.get(reminders.REMINDER_DAYS) == [60, 30, 7]
    response = client.post(detail, {"value": "45, 15, 3", "note": "Ho demana la secretaria"})
    assert response.status_code == 302
    assert business_settings.get(reminders.REMINDER_DAYS) == [45, 15, 3]
    assert AuditEntry.objects.filter(
        action=business_settings.ACTION_CHANGED, field=reminders.REMINDER_DAYS
    ).exists()
    assert reminders.due(at(45)) == {45: [holder], 15: [], 3: []}
    assert reminders.due(at(60)) == {45: [], 15: [], 3: []}


def test_the_list_filter_follows_the_trams(make_admin):  # noqa: F811
    secretary = make_admin(R.SECRETARY)
    business_settings.change(reminders.REMINDER_DAYS, [45, 15, 3], secretary, "Prova")
    response = admin_client(secretary).get(reverse("administration:licences"))
    choices = [value for value, _label in response.context["form"].fields["venciment"].choices]
    assert choices == ["", "45", "15", "3"]
    assert "45 dies o menys" in response.content.decode()
