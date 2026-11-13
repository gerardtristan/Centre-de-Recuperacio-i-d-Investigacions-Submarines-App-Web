"""El compte de trànsit del proveïdor configurat es crea sol en acabar `migrate` (T-M04-17;
T-M05a-16, la part del proveïdor; RN-T08). Només dades inventades."""

import pytest
from django.apps import apps
from django.core.management import call_command

from apps.core.models import AuditEntry
from apps.payments import providers, setup
from apps.treasury import services as treasury
from apps.treasury.models import TreasuryAccount

pytestmark = pytest.mark.django_db


def transits(code):
    return TreasuryAccount.objects.filter(kind="transit", provider_code=code)


def test_the_configured_provider_already_has_its_transit_account(settings):
    """La base de proves surt de `migrate` i ningú no l'ha creat a mà. Com els comptes inicials,
    no deixa cap entrada al registre d'activitat (P-88)."""
    account = transits(settings.PAYMENTS_PROVIDER).get()
    assert account.active
    assert not AuditEntry.objects.filter(action=treasury.TRANSIT_ACCOUNT_CREATED).exists()


def test_migrate_creates_the_transit_account_of_a_newly_configured_provider(settings, monkeypatch):
    monkeypatch.setitem(providers.REGISTRY, "nou_proveidor", providers.REGISTRY["fake"])
    settings.PAYMENTS_PROVIDER = "nou_proveidor"
    call_command("migrate", verbosity=0, skip_checks=True)
    call_command("migrate", verbosity=0, skip_checks=True)
    assert transits("nou_proveidor").get().name == "Trànsit del proveïdor «nou_proveidor»"


@pytest.mark.parametrize("code", ["", "desconegut"])
def test_without_a_known_provider_nothing_is_created(settings, code):
    settings.PAYMENTS_PROVIDER = code
    before = TreasuryAccount.objects.count()
    setup.ensure_transit_account(apps=apps)
    assert TreasuryAccount.objects.count() == before
