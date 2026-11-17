"""Salvaguarda del nivell 1 (T-M05a-06; RN-M05a-11; CA-M05a-09; decisions 025 i 042): amb l'entorn
real i sense `PAYMENTS_LIVE_CHARGES_ALLOWED`, cap camí que pot moure diners de debò no arriba al
proveïdor ni al banc, i cada negativa queda al registre d'activitat. Una sola salvaguarda
(`apps/payments/guards.py`). Només dades inventades."""

import pathlib
from uuid import uuid4

import pytest
from django.conf import settings as django_settings
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.core.models import AuditEntry
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import checkout, guards, remittances, sepa_xml
from apps.payments.models import DirectDebitRemittance
from apps.payments.models import PaymentAttempt as Attempt
from apps.payments.providers import base, fake, get_provider
from apps.payments.tests.test_checkout import charge, nothing_started, orders  # noqa: F401
from apps.payments.tests.test_sepa_xml import (  # noqa: F401 (fixtures)
    club,
    collection_date,
    new_member,
    remittance,
    signer,
    text,
    treasurer,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def level_1(settings):
    """Nivell 1 de producció: claus reals, cap cobrament autoritzat."""

    def switch():
        settings.PAYMENTS_ENVIRONMENT = base.LIVE
        settings.PAYMENTS_LIVE_CHARGES_ALLOWED = False

    return switch


def refusals(operation):
    return AuditEntry.objects.filter(
        action=guards.REFUSED, details__operation=operation, actor_kind="system"
    )


class TestEveryChargingPathRefuses:
    @pytest.mark.parametrize("method", ["card", "bizum", "transfer"])
    def test_start_payment(self, level_1, charge, personal_account, orders, method):  # noqa: F811
        level_1()
        with pytest.raises(base.LiveChargesNotAllowed):
            checkout.start_payment(charge, method, personal_account)
        assert nothing_started(charge, orders)
        assert refusals("start_payment").count() == 1

    def test_the_payment_screen_says_no_and_the_refusal_stays_in_the_log(
        self,
        level_1,
        charge,  # noqa: F811
        personal_account,
        login_as,
        orders,  # noqa: F811
    ):
        client = login_as(personal_account, AREA_PERSONAL)
        level_1()
        response = client.post(reverse("payments:pay_card", args=[charge.pk]))
        assert response["Location"] == reverse("payments:charge", args=[charge.pk])
        assert nothing_started(charge, orders)
        assert refusals("start_payment").exists()

    def test_build_remittance(self, level_1, signer, text, treasurer):  # noqa: F811
        new_member(1, signer=signer, text=text)
        level_1()
        with pytest.raises(base.LiveChargesNotAllowed):
            remittances.build_remittance("2026-12", collection_date(), treasurer)
        assert not DirectDebitRemittance.objects.exists() and not Attempt.objects.exists()
        assert refusals("build_remittance").count() == 1

    def test_remittance_file(self, level_1, remittance, treasurer):  # noqa: F811
        level_1()
        with pytest.raises(base.LiveChargesNotAllowed):
            sepa_xml.remittance_file(remittance, treasurer)
        remittance.refresh_from_db()
        assert remittance.file_hash == ""
        assert refusals("remittance_file").count() == 1

    def test_the_adapter_itself_refuses_orders_and_saved_cards(self, level_1, charge):  # noqa: F811
        provider = get_provider()
        level_1()
        urls = base.OrderUrls(
            "https://a.example.org", "https://b.example.org", "https://c.example.org"
        )
        with pytest.raises(base.LiveChargesNotAllowed):
            provider.create_order(charge, base.CARD, urls, uuid4())
        with pytest.raises(base.LiveChargesNotAllowed):
            provider.charge_saved_card(charge, object(), uuid4())
        assert not fake._orders
        assert refusals("create_order").exists() and refusals("charge_saved_card").exists()


class TestTheGuard:
    def test_level_2_and_the_test_environment_let_charges_through(self, settings):
        guards.ensure_charges_allowed("proves")  # entorn de proves
        settings.PAYMENTS_ENVIRONMENT = base.LIVE
        settings.PAYMENTS_LIVE_CHARGES_ALLOWED = True
        guards.ensure_charges_allowed("proves")  # nivell 2, amb l'autorització de la junta
        assert not AuditEntry.objects.filter(action=guards.REFUSED).exists()

    @pytest.mark.parametrize("environment", ["LIVE", "produccio", "", None])
    def test_an_unknown_environment_is_the_real_one(self, settings, environment):
        settings.PAYMENTS_ENVIRONMENT = environment
        settings.PAYMENTS_LIVE_CHARGES_ALLOWED = True
        with pytest.raises(base.LiveChargesNotAllowed):
            guards.ensure_charges_allowed("proves")

    def test_the_refusal_names_no_secret_and_no_person(self, level_1):
        level_1()
        with pytest.raises(base.LiveChargesNotAllowed):
            guards.ensure_charges_allowed("proves")
        entry = AuditEntry.objects.get(action=guards.REFUSED)
        assert entry.details == {"operation": "proves", "environment": base.LIVE}
        assert entry.actor_person is None

    def test_one_central_guard(self):
        """Cap altre mòdul no llegeix l'autorització del nivell 2: només la salvaguarda i les
        comprovacions d'arrencada."""
        root = pathlib.Path(django_settings.BASE_DIR) / "apps"
        readers = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*.py")
            if "tests" not in path.parts
            and "PAYMENTS_LIVE_CHARGES_ALLOWED" in path.read_text("utf-8")
        }
        assert readers == {"payments/guards.py", "payments/checks.py"}
