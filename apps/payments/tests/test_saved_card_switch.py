"""P-403 (opció B, propietari, 19/11/2026): amb la targeta guardada aturada al club
(`payments.provider.saved_card_enabled`), les quotes amb una targeta ja guardada no es cobren i el
soci rep l'alternativa de pagament (T-M05b-15b). Proveïdor fals; només dades inventades."""

# ruff: noqa: F811

import pytest

from apps.core import business_settings
from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.payments import checkout, processing
from apps.payments.models import PaymentAttempt
from apps.payments.providers import fake, switch_key
from apps.payments.tests.test_saved_card_charge import (  # noqa: F401 (fixtures)
    clean_orders,
    fee,
    make_admin,
    member,
    review_emails,
    saved,
    treasurer,
)

pytestmark = pytest.mark.django_db
SWITCH = switch_key("tokenization")


@pytest.fixture
def switched_off(make_admin):
    admin = make_admin(Role.Code.ADMINISTRATOR, username="anna.admin")
    business_settings.change(SWITCH, False, admin, "Targeta guardada aturada (prova)")
    return admin


def alternatives():
    return OutgoingEmail.objects.filter(template="alternativa-pagament")


def test_switched_off_nothing_reaches_the_provider_and_the_member_is_told_once(
    saved, fee, switched_off, treasurer
):
    assert checkout.charge_due_saved_cards() == 0
    assert checkout.charge_due_saved_cards() == 0  # l'endemà: cap avís més

    assert not PaymentAttempt.objects.filter(charge=fee.charge).exists()
    assert not fake._orders
    assert alternatives().count() == 1
    assert "ja no es pot fer servir" in alternatives().get().subject  # cap cobrament intentat
    entry = AuditEntry.objects.get(action=processing.OUTCOME)
    assert entry.details["case"] == checkout.SAVED_CARD_OFF
    assert review_emails().count() == 1  # el tresorer (P-406, opció per defecte A)
    assert not AuditEntry.objects.filter(action=processing.TO_REVIEW).exists()  # cap «a revisar»


def test_switched_off_a_direct_charge_is_refused(saved, fee, switched_off):
    with pytest.raises(checkout.CardNotUsable) as error:
        checkout.charge_saved_card(fee.charge, saved)
    assert error.value.case == checkout.SAVED_CARD_OFF
    assert not fake._orders


def test_switched_on_again_the_fee_is_charged(saved, fee, switched_off):
    checkout.charge_due_saved_cards()
    business_settings.change(SWITCH, True, switched_off, "Torna la targeta guardada (prova)")
    assert checkout.charge_due_saved_cards() == 1


def test_switched_on_the_saved_card_is_charged(saved, fee):
    assert checkout.charge_due_saved_cards() == 1
    assert not alternatives().exists()
