"""Contractes dels serveis que la 04 ofereix als altres mòduls (M04-8; T-M04-17): nom, entrada,
sortida i errors com diu la taula, i `create_transit_account`, que el 05a crida en configurar el
proveïdor. Els serveis de la taula que encara no existeixen s'hi afegeixen amb la seva tasca.
Només dades inventades."""

import inspect

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.core import audit
from apps.core.models import AuditEntry, Payment
from apps.treasury import services
from apps.treasury.models import TreasuryAccount
from apps.treasury.tests.test_record_income import paid, record

pytestmark = pytest.mark.django_db

CREATED = services.TRANSIT_ACCOUNT_CREATED
SYSTEM = audit.system("proves-t-m04-17")


def params(service):
    return list(inspect.signature(service).parameters)


def created_entries(account):
    return AuditEntry.objects.filter(action=CREATED, target_id=str(account.pk))


class TestSignatures:
    def test_create_transit_account_takes_the_provider_and_the_name(self):
        assert params(services.create_transit_account) == ["provider_code", "name", "by"]

    def test_record_income_takes_the_payment_and_says_who_and_from_where(self):
        assert params(services.record_income) == ["payment", "origin", "by"]

    @pytest.mark.parametrize("error", ["ChargeNotPaid", "BrowserOriginRejected"])
    def test_record_income_raises_the_errors_of_the_table(self, error):
        assert issubclass(getattr(services, error), ValidationError)


class TestCreateTransitAccount:
    def test_a_new_provider_gets_an_active_transit_account_and_it_is_logged(self):
        account = services.create_transit_account("card_provider", "Trànsit targeta", by=SYSTEM)
        assert (account.kind, account.provider_code) == ("transit", "card_provider")
        assert (account.name, account.active, account.last4) == ("Trànsit targeta", True, None)
        entry = created_entries(account).get()
        assert entry.actor_kind == AuditEntry.ActorKind.SYSTEM
        assert entry.details == {"provider_code": "card_provider", "name": "Trànsit targeta"}

    def test_calling_it_again_returns_the_existing_one_without_touching_it(self):
        first = services.create_transit_account("card_provider", "Trànsit targeta", by=SYSTEM)
        TreasuryAccount.objects.filter(pk=first.pk).update(active=False)
        again = services.create_transit_account("card_provider", "Un altre nom", by=SYSTEM)
        assert again == first
        assert (again.name, again.active) == ("Trànsit targeta", False)  # el tresorer el desactiva
        assert TreasuryAccount.objects.filter(provider_code="card_provider").count() == 1
        assert created_entries(first).count() == 1

    def test_p_88_without_who_it_is_the_installation_and_it_is_not_logged(self):
        account = services.create_transit_account("card_provider", "Trànsit targeta")
        assert not created_entries(account).exists()

    def test_each_provider_has_its_own(self):
        card = services.create_transit_account("card_provider", "Trànsit targeta")
        sepa = services.create_transit_account(services.SEPA_REMITTANCE, "Remeses SEPA")
        assert card != sepa

    def test_a_name_already_taken_by_another_account_is_not_hidden(self):
        with pytest.raises(IntegrityError):
            services.create_transit_account("card_provider", "Caixa")
        assert not TreasuryAccount.objects.filter(provider_code="card_provider").exists()

    def test_rn_t08_the_card_income_goes_to_the_transit_account_of_the_configured_provider(
        self, settings, make_person
    ):
        settings.PAYMENTS_PROVIDER = "card_provider"
        account = services.create_transit_account("card_provider", "Trànsit targeta")
        movement = record(paid(make_person("Núria", "Coll"), method=Payment.Method.CARD))
        assert movement.account == account
