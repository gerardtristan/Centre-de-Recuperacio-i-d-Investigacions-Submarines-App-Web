"""Comptes de tresoreria (T-M04-01; HU-T01; CA-T01.1 a CA-T01.3; RN-T01 a RN-T04)."""

from importlib import import_module

import pytest
from django.db import DataError, IntegrityError, migrations, transaction

from apps.core.models import UndeletableError
from apps.treasury.models import TreasuryAccount

pytestmark = pytest.mark.django_db
K = TreasuryAccount.Kind


def create(**fields):
    """Desa directament, sense `full_clean`: el que es prova és la base de dades."""
    with transaction.atomic():
        return TreasuryAccount.objects.create(**fields)


def rejected(**fields):
    """La base de dades no ho admet: per una restricció o perquè no hi cap."""
    with pytest.raises((IntegrityError, DataError)):
        create(**fields)


class TestInitialAccounts:
    def test_ca_t01_1_cash_and_main_bank_exist_after_the_migrations(self):
        accounts = {a.name: a for a in TreasuryAccount.objects.all()}
        assert set(accounts) == {"Caixa", "Banc principal"}
        assert accounts["Caixa"].kind == K.CASH
        assert accounts["Banc principal"].kind == K.BANK
        assert all(
            a.active and a.last4 is None and a.provider_code is None for a in accounts.values()
        )

    def test_every_data_migration_can_be_undone(self):
        module = import_module("apps.treasury.migrations.0002_initial_accounts")
        operations = module.Migration.operations
        assert operations and all(
            isinstance(op, migrations.RunPython) and op.reverse_code is not None
            for op in operations
        )


class TestNoBankDetails:
    def test_ca_t01_2_no_field_can_hold_a_full_iban_or_a_card(self):
        names = {field.name for field in TreasuryAccount._meta.get_fields()}
        forbidden = {"iban", "pan", "cvv", "cvc", "card_number", "account_number", "bic", "swift"}
        assert not names & forbidden
        # L'únic camp amb xifres del compte en té quatre, i cap camp de text n'admet més de 80.
        assert TreasuryAccount._meta.get_field("last4").max_length == 4

    def test_last_four_digits_only_on_bank_accounts(self):
        assert create(name="Banc secundari", kind=K.BANK, last4="1234").last4 == "1234"
        rejected(name="Caixa petita", kind=K.CASH, last4="1234")
        rejected(name="Trànsit targeta", kind=K.TRANSIT, provider_code="card", last4="1234")

    @pytest.mark.parametrize("value", ["123", "12a4", "ES12", "", " 123", "١٢٣٤"])
    def test_last_four_must_be_exactly_four_digits(self, value):
        rejected(name="Banc secundari", kind=K.BANK, last4=value)


class TestKinds:
    def test_rn_t01_three_kinds_and_no_other(self):
        assert set(K.values) == {"bank", "cash", "transit"}
        rejected(name="Inversions", kind="invest")

    def test_transit_account_needs_its_provider(self):
        assert create(name="Trànsit targeta", kind=K.TRANSIT, provider_code="card_provider")
        rejected(name="Trànsit sense proveïdor", kind=K.TRANSIT)
        rejected(name="Trànsit buit", kind=K.TRANSIT, provider_code="")

    @pytest.mark.parametrize("code", ["Card", "card provider", "card-provider", "ñ", "a" * 31])
    def test_provider_code_is_a_plain_identifier(self, code):
        rejected(name="Trànsit", kind=K.TRANSIT, provider_code=code)

    def test_one_transit_account_per_provider(self):
        create(name="Trànsit targeta", kind=K.TRANSIT, provider_code="card_provider")
        rejected(name="Trànsit targeta 2", kind=K.TRANSIT, provider_code="card_provider")
        assert create(name="Remeses SEPA", kind=K.TRANSIT, provider_code="sepa_remittance")

    @pytest.mark.parametrize("kind", [K.BANK, K.CASH])
    def test_only_transit_accounts_have_a_provider(self, kind):
        rejected(name="Compte amb proveïdor", kind=kind, provider_code="card_provider")

    def test_name_is_unique(self):
        rejected(name="Caixa", kind=K.CASH)


class TestNeverDeleted:
    def test_ca_t01_3_an_account_is_deactivated_not_deleted(self):
        account = TreasuryAccount.objects.get(name="Caixa")
        with pytest.raises(UndeletableError):
            account.delete()
        with pytest.raises(UndeletableError):
            TreasuryAccount.objects.filter(name="Caixa").delete()
        account.active = False
        account.save(update_fields=["active"])
        assert TreasuryAccount.objects.filter(name="Caixa", active=False).exists()

    def test_shows_its_name(self):
        assert str(TreasuryAccount.objects.get(name="Caixa")) == "Caixa"
