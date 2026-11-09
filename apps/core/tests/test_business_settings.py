"""Peça comuna d'ajustos (T-AJ-01; decisió 055, RN-AJ-01 a 04, CA-AJ-01 a 05). Només dades
inventades. Les claus i els permisos `settings.edit.<clau>` són de prova: cada mòdul declara
els seus quan construeix la seva pantalla d'ajustos."""

import datetime

import pytest
from django.core import mail as django_mail
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail.backends.base import BaseEmailBackend
from django.db import IntegrityError, connection, transaction
from django.http import Http404
from django.test import override_settings
from django.utils import timezone
from procrastinate.contrib.django.models import ProcrastinateJob

from apps.accounts.models import Account
from apps.core import business_settings as settings_service
from apps.core import mail, permissions
from apps.core.models import (
    AccountRole,
    AppendOnlyError,
    AuditEntry,
    OutgoingEmail,
    Role,
    RolePermission,
    Setting,
    SettingVersion,
)
from apps.core.permission_catalog import CATALOG, Permission

pytestmark = pytest.mark.django_db

R = Role.Code
T = Setting.ValueType

DAYS = "members.test_days"
FEE = "members.test_fee"
TEXT = "members.test_text"
UNGRANTED = "members.test_ungranted"


class FailingBackend(BaseEmailBackend):
    def send_messages(self, messages):
        raise ConnectionError("servidor de proves no disponible")


def _today():
    return timezone.localdate()


def _tomorrow():
    return _today() + datetime.timedelta(days=1)


@pytest.fixture(autouse=True)
def test_settings(monkeypatch):
    """Tres ajustos de prova i els seus permisos al catàleg (com farà cada mòdul)."""
    grants = {
        DAYS: [R.TREASURER],
        FEE: [R.TREASURER, R.ADMINISTRATOR],
        TEXT: [R.SECRETARY],
        UNGRANTED: [],
    }
    extra = {
        settings_service.permission_code(key): Permission(
            code=settings_service.permission_code(key), ref="TEST", description=key
        )
        for key in grants
    }
    monkeypatch.setattr(permissions, "CATALOG", {**CATALOG, **extra})
    for key, roles in grants.items():
        for role in roles:
            RolePermission.objects.create(
                role=Role.objects.get(code=role),
                permission_code=settings_service.permission_code(key),
                scope="all",
            )
    Setting.objects.create(
        key=DAYS, module="members", value_type=T.INTEGER, initial_value=15, min_value=1,
        max_value=90,
    )  # fmt: skip
    Setting.objects.create(
        key=FEE, module="members", value_type=T.CENTS, initial_value=3500, min_value=1,
        affects_money=True, effective_dated=True,
    )  # fmt: skip
    Setting.objects.create(
        key=TEXT, module="members", value_type=T.TEXT, initial_value="Hola", max_length=300
    )
    Setting.objects.create(
        key=UNGRANTED, module="members", value_type=T.BOOLEAN, initial_value=False
    )


@pytest.fixture
def treasurer(make_admin):
    account = make_admin(R.TREASURER)
    account.notification_email = "tresorer@example.org"
    account.save()
    return account


@pytest.fixture
def board(make_admin):
    account = make_admin(R.BOARD)
    account.notification_email = "junta@example.org"
    account.save()
    return account


# --- RN-AJ-01: lectura -------------------------------------------------------------------------


def test_without_versions_get_returns_initial_value():
    assert settings_service.get(DAYS) == 15
    assert settings_service.get(FEE, _tomorrow()) == 3500


def test_unknown_key_is_a_programming_error():
    with pytest.raises(Setting.DoesNotExist):
        settings_service.get("members.no_existeix")


def test_setting_without_effective_date_returns_latest_value(treasurer):
    settings_service.change(DAYS, 10, treasurer)
    settings_service.change(DAYS, 20, treasurer)
    assert settings_service.get(DAYS) == 20
    assert SettingVersion.objects.filter(setting__key=DAYS).first().effective_from is None


# --- CA-AJ-01: tipus i rang --------------------------------------------------------------------


@pytest.mark.parametrize("value", [0, 91])
def test_ca_aj_01_out_of_range_is_rejected_and_nothing_saved(treasurer, value):
    with pytest.raises(ValidationError) as error:
        settings_service.change(DAYS, value, treasurer)
    assert "entre 1 i 90" in error.value.messages[0]
    assert not SettingVersion.objects.exists()
    assert not AuditEntry.objects.filter(action=settings_service.ACTION_CHANGED).exists()


@pytest.mark.parametrize("value", [1, 90])
def test_ca_aj_01_range_limits_are_accepted(treasurer, value):
    settings_service.change(DAYS, value, treasurer)
    assert settings_service.get(DAYS) == value


@pytest.mark.parametrize(
    ("definition", "valid", "invalid"),
    [
        ({"value_type": T.INTEGER, "min_value": 0}, [0, 7], ["7", 7.5, True, -1]),
        ({"value_type": T.CENTS}, [-500, 0, 2000], ["20,00", 20.0, None]),
        ({"value_type": T.BOOLEAN}, [True, False], [0, 1, "sí", None]),
        ({"value_type": T.TEXT, "max_length": 5}, ["", "abcde"], ["abcdef", 5, None]),
        (
            {"value_type": T.CHOICE, "choices": ["club", "member"]},
            ["club", "member"],
            ["altre", "", None],
        ),
        (
            {"value_type": T.URL},
            ["https://www.meteo.cat/prediccio/costa"],
            ["http://www.meteo.cat", "javascript:alert(1)", "no és una url", 3],
        ),
        (
            {"value_type": T.DAY_MONTH, "min_value": 1001, "max_value": 1231},
            ["10-01", "12-01", "12-31"],
            ["09-30", "02-30", "1-12", "12/01", 1201],
        ),
        (
            {"value_type": T.INTEGER_LIST, "min_value": 1, "max_value": 120},
            [[60, 30, 7], [1]],
            [[], [0, 30], [121], ["60"], 60, [True]],
        ),
    ],
)
def test_every_value_type_checks_type_and_range(definition, valid, invalid):
    setting = Setting(key="members.x", module="members", initial_value=None, **definition)
    for value in valid:
        settings_service.validate_value(setting, value)
    for value in invalid:
        with pytest.raises(ValidationError):
            settings_service.validate_value(setting, value)


def test_setting_definition_is_checked():
    setting = Setting(
        key="members.x", module="members", value_type=T.INTEGER, initial_value=0, min_value=1
    )
    with pytest.raises(ValidationError):
        setting.clean()
    setting.key = "payments.x"
    setting.initial_value = 5
    with pytest.raises(ValidationError):
        setting.clean()  # la clau no porta el prefix del mòdul


def test_money_setting_must_be_effective_dated():
    with pytest.raises(IntegrityError), transaction.atomic():
        Setting.objects.create(
            key="members.y", module="members", value_type=T.CENTS, initial_value=1,
            affects_money=True, effective_dated=False,
        )  # fmt: skip


# --- CA-AJ-02: permís del catàleg (RN-RP-17; sense `editor_roles`) -----------------------------


def test_setting_model_has_no_editor_roles():
    assert "editor_roles" not in {f.name for f in Setting._meta.get_fields()}


@pytest.mark.parametrize(
    ("key", "value", "role"),
    [(DAYS, 10, R.SECRETARY), (TEXT, "Adeu", R.TREASURER), (UNGRANTED, True, R.ADMINISTRATOR)],
)
def test_ca_aj_02_role_without_permission_gets_not_found(make_admin, key, value, role):
    with pytest.raises(Http404):
        settings_service.change(key, value, make_admin(role))
    assert not SettingVersion.objects.exists()


def test_ca_aj_02_permission_is_per_key(make_admin):
    secretary = make_admin(R.SECRETARY)
    settings_service.change(TEXT, "Text nou", secretary)
    with pytest.raises(Http404):
        settings_service.change(DAYS, 10, secretary)
    assert settings_service.get(TEXT) == "Text nou"
    assert settings_service.get(DAYS) == 15


def test_ca_aj_02_personal_and_inactive_accounts_get_not_found(personal_account, treasurer):
    with pytest.raises(Http404):
        settings_service.change(DAYS, 10, personal_account)
    treasurer.status = Account.Status.DISABLED
    treasurer.save()
    with pytest.raises(Http404):
        settings_service.change(DAYS, 10, treasurer)
    assert not SettingVersion.objects.exists()


def test_ca_aj_02_removed_role_loses_permission_at_next_call(treasurer):
    settings_service.change(DAYS, 10, treasurer)
    AccountRole.objects.filter(admin_account=treasurer).update(removed_at=timezone.now())
    with pytest.raises(Http404):
        settings_service.change(DAYS, 20, treasurer)
    assert settings_service.get(DAYS) == 10


def test_unknown_key_gets_not_found_without_revealing_it(treasurer):
    with pytest.raises(Http404):
        settings_service.change("members.no_existeix", 1, treasurer)


def test_setting_without_catalog_permission_is_a_programming_error(treasurer):
    Setting.objects.create(key="members.sense_permis", module="members", value_type=T.INTEGER,
                           initial_value=1)  # fmt: skip
    with pytest.raises(ImproperlyConfigured):
        settings_service.change("members.sense_permis", 2, treasurer)


# --- CA-AJ-03: data d'entrada en vigor ---------------------------------------------------------


def test_ca_aj_03_money_change_applies_from_its_date(treasurer):
    settings_service.change(FEE, 4000, treasurer, note="Pujada", effective_from=_tomorrow())
    assert settings_service.get(FEE) == 3500
    assert settings_service.get(FEE, _today()) == 3500
    assert settings_service.get(FEE, _tomorrow()) == 4000


@pytest.mark.parametrize(
    ("note", "days"),
    [("Pujada", -1), ("", 1), ("   ", 1), ("Pujada", None)],
    ids=["data-passada", "sense-nota", "nota-en-blanc", "sense-data"],
)
def test_ca_aj_03_past_date_missing_date_or_note_is_rejected(treasurer, note, days):
    effective = None if days is None else _today() + datetime.timedelta(days=days)
    with pytest.raises(ValidationError):
        settings_service.change(FEE, 4000, treasurer, note=note, effective_from=effective)
    assert not SettingVersion.objects.exists()
    assert not OutgoingEmail.objects.exists()


def test_ca_aj_03_change_from_today_is_accepted(treasurer):
    settings_service.change(FEE, 4000, treasurer, note="Ja", effective_from=_today())
    assert settings_service.get(FEE) == 4000


def test_same_date_latest_wins_and_undoes_a_scheduled_change(treasurer):
    settings_service.change(FEE, 4000, treasurer, note="Pujada", effective_from=_tomorrow())
    settings_service.change(FEE, 3500, treasurer, note="Desfet", effective_from=_tomorrow())
    assert settings_service.get(FEE, _tomorrow()) == 3500
    later = _tomorrow() + datetime.timedelta(days=30)
    settings_service.change(FEE, 4500, treasurer, note="Més endavant", effective_from=later)
    assert settings_service.get(FEE, _tomorrow()) == 3500
    assert settings_service.get(FEE, later) == 4500


def test_setting_without_effective_date_rejects_a_date(treasurer):
    with pytest.raises(ValidationError):
        settings_service.change(DAYS, 10, treasurer, effective_from=_tomorrow())
    assert not SettingVersion.objects.exists()


def test_back_to_initial_value_is_one_more_change(treasurer):
    settings_service.change(DAYS, 30, treasurer)
    settings_service.change(DAYS, 15, treasurer)
    assert settings_service.get(DAYS) == 15
    assert list(SettingVersion.objects.values_list("value", "previous_value")) == [
        (30, 15),
        (15, 30),
    ]


def test_previous_value_is_the_value_in_force_at_the_effective_date(treasurer):
    later = _today() + datetime.timedelta(days=10)
    settings_service.change(FEE, 4000, treasurer, note="Primer", effective_from=later)
    version = settings_service.change(FEE, 4200, treasurer, note="Avui", effective_from=_today())
    assert version.previous_value == 3500  # el de demà passat encara no és vigent avui


# --- CA-AJ-04: correu dels canvis de diners ----------------------------------------------------


def _money_emails():
    return OutgoingEmail.objects.filter(template=settings_service.EMAIL_TEMPLATE)


def test_ca_aj_04_money_change_emails_treasurer_and_board_once(treasurer, board, make_admin):
    secretary = make_admin(R.SECRETARY)  # cap correu a qui no és tresorer ni junta
    secretary.notification_email = "secretaria@example.org"
    secretary.save()
    settings_service.change(FEE, 4000, treasurer, note="Pujada", effective_from=_tomorrow())
    emails = _money_emails()
    assert sorted(emails.values_list("to_address", flat=True)) == [
        "junta@example.org",
        "tresorer@example.org",
    ]
    body = emails.first().body_text
    assert "35,00 €" in body and "40,00 €" in body
    assert FEE in body and "Pujada" in body and str(treasurer.person) in body
    assert _tomorrow().strftime("%d/%m/%Y") in body
    assert ProcrastinateJob.objects.filter(task_name="core.send_email").count() == 2
    assert django_mail.outbox == []  # va per la cua


def test_ca_aj_04_one_email_per_address(treasurer, make_admin):
    both = make_admin(R.TREASURER, R.BOARD)
    both.notification_email = "tresorer@example.org"
    both.save()
    settings_service.change(FEE, 4000, treasurer, note="Pujada", effective_from=_tomorrow())
    assert _money_emails().count() == 1


def test_ca_aj_04_non_money_change_sends_no_email(treasurer, board):
    settings_service.change(DAYS, 10, treasurer)
    assert not _money_emails().exists()


def test_ca_aj_04_inactive_or_removed_recipients_get_no_email(treasurer, board):
    board.status = Account.Status.DISABLED
    board.save()
    AccountRole.objects.filter(admin_account=treasurer).update(removed_at=timezone.now())
    AccountRole.objects.create(admin_account=treasurer, role=Role.objects.get(code=R.ADMINISTRATOR))
    settings_service.change(FEE, 4000, treasurer, note="Pujada", effective_from=_tomorrow())
    assert not _money_emails().exists()


@override_settings(EMAIL_BACKEND="apps.core.tests.test_business_settings.FailingBackend")
def test_ca_aj_04_failed_email_keeps_the_change_and_is_retried(treasurer):
    settings_service.change(FEE, 4000, treasurer, note="Pujada", effective_from=_tomorrow())
    email = _money_emails().get()
    with pytest.raises(mail.EmailDeliveryError):
        mail.deliver(email.pk)
    email.refresh_from_db()
    assert email.status == OutgoingEmail.Status.QUEUED and email.attempts == 1
    assert settings_service.get(FEE, _tomorrow()) == 4000


def test_ca_aj_04_catalog_rows_notify_with_the_same_service(treasurer, board):
    emails = settings_service.notify_money_change(
        what="Curs Open Water: preu de soci",
        previous="250,00 €",
        new="270,00 €",
        changed_by=treasurer,
        note="Tarifa nova",
        effective_from=_tomorrow(),
    )
    assert len(emails) == 2
    assert "250,00 €" in emails[0].body_text and "270,00 €" in emails[0].body_text


def test_display_value():
    fee = Setting(value_type=T.CENTS)
    assert settings_service.display_value(fee, 3500) == "35,00 €"
    assert settings_service.display_value(fee, -5) == "-0,05 €"
    assert settings_service.display_value(Setting(value_type=T.DAY_MONTH), "12-01") == "1/12"
    assert settings_service.display_value(Setting(value_type=T.INTEGER_LIST), [60, 7]) == "60, 7"
    assert settings_service.display_value(Setting(value_type=T.BOOLEAN), True) == "sí"


# --- CA-AJ-05: registre d'activitat i historial ------------------------------------------------


def test_ca_aj_05_change_is_recorded_with_who_when_account_and_previous_value(treasurer):
    before = timezone.now()
    version = settings_service.change(
        FEE, 4000, treasurer, note="Pujada", effective_from=_tomorrow()
    )
    entry = AuditEntry.objects.get(action=settings_service.ACTION_CHANGED)
    assert entry.actor_account == treasurer
    assert entry.actor_person_id == treasurer.person_id
    assert entry.actor_roles == [R.TREASURER]
    assert entry.created_at >= before
    assert (entry.field, entry.old_value, entry.new_value) == (FEE, 3500, 4000)
    assert entry.reason == "Pujada"
    assert entry.target_type == "core.setting"
    assert entry.details == {"effective_from": _tomorrow().isoformat(), "version_id": version.pk}
    # L'historial (la pantalla és de la T-AJ-02) surt de les versions.
    history = Setting.objects.get(key=FEE).versions.get()
    assert (history.changed_by, history.previous_value, history.value) == (treasurer, 3500, 4000)
    assert history.note == "Pujada"


def test_versions_are_append_only(treasurer):
    version = settings_service.change(DAYS, 10, treasurer)
    version.value = 11
    with pytest.raises(AppendOnlyError):
        version.save()
    with pytest.raises(AppendOnlyError):
        version.delete()
    with pytest.raises(AppendOnlyError):
        SettingVersion.objects.update(value=12)


def test_versions_cannot_be_changed_with_raw_sql(treasurer):
    version = settings_service.change(DAYS, 10, treasurer)
    for sql in (
        "UPDATE core_settingversion SET value = '12' WHERE id = %s",
        "DELETE FROM core_settingversion WHERE id = %s",
    ):
        with pytest.raises(Exception, match="no es poden modificar"), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(sql, [version.pk])
    assert settings_service.get(DAYS) == 10
