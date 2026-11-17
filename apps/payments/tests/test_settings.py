"""Ajustos de pagaments (T-M05b-22; addenda de la 055 del 05b: VC-17, RN-M05b-24; RN-RP-22).
Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.http import Http404
from django.urls import reverse

from apps.core import business_settings
from apps.core.models import AuditEntry, Person, Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401
from apps.core.tests.test_guest_links import admin_client
from apps.payments import attempts, checkout, processing, remittances, returns
from apps.payments.models import PaymentAttempt as Attempt
from apps.payments.providers import base, fake
from apps.payments.tests.test_bizum import minutes_pass
from apps.payments.tests.test_checkout import new_charge
from apps.payments.tests.test_processing import (  # noqa: F401
    account,
    fee,
    member,
    state,
    transit,
)
from conftest import CommittedDataTestCase

pytestmark = pytest.mark.django_db

R = Role.Code
BIZUM, AGE = attempts.BIZUM_UI_TIMEOUT, processing.SAFETY_NET_AGE
GIVE_UP = processing.SAFETY_NET_GIVE_UP


@pytest.fixture(autouse=True)
def clean_orders(settings):
    settings.PUBLIC_SITE_URL = "https://cris1954.cat"
    fake.reset()


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR)


def test_vc_17_values_come_from_the_migration_with_their_ranges():
    rows = Setting.objects.filter(module="payments").order_by("key")
    assert [(s.key, s.initial_value, s.min_value, s.max_value) for s in rows] == [
        (BIZUM, 15, 5, 30),
        (returns.MAX_ATTEMPTS, 2, 1, 3),  # VC-16 (T-M05b-12)
        (remittances.PRENOTIFICATION_DAYS, 14, 14, 30),  # VC-16 (T-M05b-09)
        (AGE, 60, 30, 240),
        (GIVE_UP, 24, 24, 168),
    ]
    assert not any(s.affects_money or s.effective_dated for s in rows)


@pytest.mark.parametrize(
    ("key", "low", "high"), [(BIZUM, 5, 30), (AGE, 30, 240), (GIVE_UP, 24, 168)]
)
def test_vc_17_range_is_checked(admin, key, low, high):
    for value in (low - 1, high + 1):
        with pytest.raises(ValidationError):
            business_settings.change(key, value, admin)
    business_settings.change(key, high, admin)
    assert business_settings.get(key) == high


def test_vc_17_only_the_administrator_edits_and_the_treasurer_only_sees(make_admin):  # noqa: F811
    treasurer = make_admin(R.TREASURER)
    with pytest.raises(Http404):
        business_settings.change(BIZUM, 20, treasurer)
    assert AuditEntry.objects.filter(action=business_settings.ACTION_DENIED).count() == 1
    client = admin_client(treasurer)
    page = client.get(reverse("administration:setting_detail", args=["payments", BIZUM]))
    assert page.status_code == 200 and b"Desa el valor" not in page.content
    secretary = admin_client(make_admin(R.SECRETARY))
    assert (
        secretary.get(reverse("administration:settings_section", args=["payments"])).status_code
        == 404
    )


def test_rn_m05b_24_a_bizum_in_progress_keeps_its_timeout(admin, personal_account):
    charge = new_charge(personal_account.person)
    started = Attempt.objects.get(
        pk=checkout.start_payment(charge, "bizum", personal_account).attempt_id
    )
    assert started.ui_timeout_minutes == 15
    business_settings.change(BIZUM, 5, admin)
    minutes_pass(started, 10, provider_closes=False)
    assert checkout.payment_status(charge).state == checkout.IN_PROGRESS  # encara 15
    minutes_pass(started, 6, provider_closes=False)
    assert checkout.payment_status(charge).state == checkout.TIMED_OUT
    other = new_charge(personal_account.person)
    checkout.start_payment(other, "bizum", personal_account)
    assert other.attempts.get().ui_timeout_minutes == 5  # els nous, el valor nou


def test_a_card_attempt_has_no_screen_timeout(personal_account):
    charge = new_charge(personal_account.person)
    checkout.start_payment(charge, "card", personal_account)
    assert charge.attempts.get().ui_timeout_minutes is None


def test_vc_17_the_safety_net_waits_the_configured_minutes(admin, fee, account, transit):  # noqa: F811
    attempt = Attempt.objects.get(pk=checkout.start_payment(fee.charge, "card", account).attempt_id)
    fake.FakeProvider().notification(attempt.provider_order_id, base.PAID)  # mai no arriba
    minutes_pass(attempt, 45, provider_closes=False)
    processing.safety_net()  # 60 minuts: encara espera
    assert state(attempt, fee)[0] == Attempt.Status.IN_PROGRESS
    business_settings.change(AGE, 30, admin)
    processing.safety_net()
    assert state(attempt, fee)[0] == Attempt.Status.PAID


def test_ca_m05b_33_the_safety_net_gives_up_after_the_configured_hours(
    admin,
    fee,  # noqa: F811
    account,  # noqa: F811
    transit,  # noqa: F811
    make_admin,  # noqa: F811
):
    attempt = Attempt.objects.get(pk=checkout.start_payment(fee.charge, "card", account).attempt_id)
    fake.reset()  # el proveïdor ja no coneix l'ordre: la xarxa no la pot consultar
    minutes_pass(attempt, 30 * 60, provider_closes=False)
    business_settings.change(GIVE_UP, 48, admin, note="Prova")
    processing.safety_net()
    assert state(attempt, fee)[0] == Attempt.Status.IN_PROGRESS  # 30 hores < 48: l'endemà
    entry = AuditEntry.objects.get(action=business_settings.ACTION_CHANGED, field=GIVE_UP)
    assert (entry.old_value, entry.new_value) == (24, 48)
    with pytest.raises(Http404):  # el tresorer el veu però no l'edita
        business_settings.change(GIVE_UP, 24, make_admin(R.TREASURER))
    business_settings.change(GIVE_UP, 24, admin)
    processing.safety_net()
    assert state(attempt, fee)[0] == Attempt.Status.TO_REVIEW
    assert "consultar l'ordre" in attempt.review_reason


class TestSettingsMigrationIsReversible(CommittedDataTestCase):
    """Desfer i tornar a aplicar la 0004 i la 0005 funciona i deixa els mateixos ajustos (mateixa
    clau primària): si es recreessin, la neteja d'aquesta classe, que esborra les files noves, els
    faria desaparèixer de la base de proves reutilitzada (revisió de la PR #49)."""

    def test_backwards_and_forwards_keeps_the_same_rows(self):
        person = Person.objects.create(first_name="Prova", origin="in_person")
        bizum = attempts.create_attempt(new_charge(person), "bizum")
        before = dict(Setting.objects.filter(module="payments").values_list("key", "pk"))
        leaves = MigrationExecutor(connection).loader.graph.leaf_nodes()
        try:
            MigrationExecutor(connection).migrate([("payments", "0003_receipt")])
        finally:
            MigrationExecutor(connection).migrate(leaves)
        after = dict(Setting.objects.filter(module="payments").values_list("key", "pk"))
        assert after == before and len(after) == 5
        # RN-M05b-24: un Bizum que ja era en curs en desplegar conserva els 15 minuts.
        assert Attempt.objects.get(pk=bizum.pk).ui_timeout_minutes == 15


@pytest.mark.parametrize(
    ("key", "value"), [(remittances.PRENOTIFICATION_DAYS, 20), (returns.MAX_ATTEMPTS, 3)]
)
def test_vc_16_only_the_treasurer_edits(make_admin, admin, key, value):  # noqa: F811
    for other in (admin, make_admin(R.SECRETARY)):
        with pytest.raises(Http404):
            business_settings.change(key, value, other)
    business_settings.change(key, value, make_admin(R.TREASURER))
    assert business_settings.get(key) == value
