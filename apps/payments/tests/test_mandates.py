"""Models del mandat i IBAN xifrat (T-M05a-08, primera part; CA-M05a-03, 05 i 07; i
CA-M05a-13 sobre la taula real). Decisió 044: l'IBAN només és xifrat al mandat i no surt a cap
`__str__`, administrador, registre, registre d'activitat ni error.

Només dades inventades: els IBAN són de format vàlid amb un compte de zeros, i les claus es
generen a cada prova."""

import io
import logging

import pytest
from cryptography.fernet import Fernet, InvalidToken
from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, models, transaction
from django.utils import timezone

from apps.accounts.models import Account
from apps.core.models import AuditEntry, LegalText
from apps.members.tests.test_cards import make_member
from apps.payments import checks, crypto, mandates
from apps.payments.models import MandateBankAccount, SepaMandate
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

IBAN = "ES5500000000000000000001"
OTHER_IBAN = "ES2800000000000000000002"
ACTIVE = SepaMandate.Status.ACTIVE


def key(version):
    return f"{version}:{Fernet.generate_key().decode()}"


@pytest.fixture
def member():
    return make_member()


@pytest.fixture
def account(member):
    return Account.objects.create_personal(member.person, "anna.prova@example.org", PASSWORD)


@pytest.fixture
def text():
    return LegalText.objects.create(kind="sepa_mandate", version=1, content="Text de prova.")


@pytest.fixture
def sign(member, account, text):
    def sign(iban=IBAN, who=member):
        return mandates.create_mandate(
            who,
            iban=iban,
            holder_name="Anna Prova",
            holder_is_member=True,
            legal_text=text,
            account=account,
            creditor_identifier="ES00ZZZ00000000",
            evidence={"channel": "web", "text_version": text.version},
        )

    return sign


def iban_of(mandate):
    bank = MandateBankAccount.objects.get(mandate=mandate)
    return crypto.decrypt(bank.key_version, bank.iban_ciphertext)


def test_ca_m05a_03_mandat_desat_amb_referencia_text_data_compte_i_iban_xifrat(sign, account, text):
    mandate = sign("es55 0000 0000 0000 0000 0001")

    mandate.refresh_from_db()
    assert mandate.reference == "CRIS001287M01"
    assert (mandate.legal_text, mandate.signed_by_account, mandate.status) == (
        text,
        account,
        ACTIVE,
    )
    assert mandate.signed_at <= timezone.now()
    bank = mandate.bank_account
    assert IBAN.encode() not in bytes(bank.iban_ciphertext)
    assert (bank.iban_country, bank.iban_last4) == ("ES", "0001")
    assert iban_of(mandate) == IBAN
    assert AuditEntry.objects.filter(action="payments.mandate.created").count() == 1


def test_ca_m05a_05_un_mandat_nou_substitueix_l_actiu(sign, member, account):
    first = sign()
    second = sign(OTHER_IBAN)

    first.refresh_from_db()
    assert first.status == SepaMandate.Status.REVOKED
    assert (first.revoked_reason, first.revoked_by) == (SepaMandate.REPLACED, account)
    assert second.reference == "CRIS001287M02"
    assert list(SepaMandate.objects.filter(member=member, status=ACTIVE)) == [second]
    assert (iban_of(first), iban_of(second)) == (IBAN, OTHER_IBAN)
    revoked = AuditEntry.objects.get(action="payments.mandate.revoked")
    assert revoked.reason == SepaMandate.REPLACED
    # L'índex únic parcial ho garanteix també fora del servei.
    with pytest.raises(IntegrityError), transaction.atomic():
        SepaMandate.objects.filter(pk=first.pk).update(
            status=ACTIVE, revoked_at=None, revoked_reason=""
        )


def test_dos_socis_amb_el_mateix_iban_tenen_mandats_diferents(sign):
    """L-M05a-02."""
    other = make_member(first="Bru", number=7, document="00000000T")
    assert {sign().reference, sign(who=other).reference} == {"CRIS001287M01", "CRIS000007M01"}


@pytest.mark.parametrize(
    "changes",
    [
        {"reference": "CRIS1287M1"},
        {"status": "revoked"},  # sense data ni motiu
        {"revoked_at": timezone.now()},  # actiu amb data de revocació
        {"sequence_type": "one_off"},
        {"status": "esborrat"},
    ],
)
def test_restriccions_del_mandat(sign, changes):
    mandate = sign()
    with pytest.raises(IntegrityError), transaction.atomic():
        SepaMandate.objects.filter(pk=mandate.pk).update(**changes)


@pytest.mark.parametrize("value", ["ES5500000000000000000002", "ES55", "", "XX" + IBAN[2:]])
def test_un_iban_invalid_no_es_desa_ni_es_registra(sign, value):
    with pytest.raises(ValidationError) as error:
        sign(value)
    assert not value or value not in str(error.value)
    assert not SepaMandate.objects.exists() and not MandateBankAccount.objects.exists()
    assert not AuditEntry.objects.filter(action__startswith="payments.mandate").exists()


def test_un_soci_sense_numero_no_signa(sign):
    with pytest.raises(ValueError):
        sign(who=make_member(first="Cesc", number=None, status="pending", document="00000001R"))
    assert not SepaMandate.objects.exists()


def test_ca_m05a_07_l_unic_camp_que_pot_tenir_un_iban_es_iban_ciphertext():
    fields = {
        f"{model._meta.label}.{field.name}": field
        for model in apps.get_models()
        if model.__module__.startswith("apps.")
        for field in model._meta.get_fields()
        if "iban" in field.name.lower()
    }
    assert sorted(fields) == [
        "payments.MandateBankAccount.iban_ciphertext",
        "payments.MandateBankAccount.iban_country",
        "payments.MandateBankAccount.iban_last4",
    ]
    assert isinstance(fields["payments.MandateBankAccount.iban_ciphertext"], models.BinaryField)
    # L'IBAN més curt té 15 caràcters: ni el país ni els quatre darrers dígits el poden contenir.
    assert fields["payments.MandateBankAccount.iban_country"].max_length == 2
    assert fields["payments.MandateBankAccount.iban_last4"].max_length == 4


def test_044_l_iban_no_surt_enlloc(sign, settings, caplog):
    caplog.set_level(logging.DEBUG)
    first = sign()
    second = sign(OTHER_IBAN)
    settings.MANDATE_ENCRYPTION_KEYS = [*settings.MANDATE_ENCRYPTION_KEYS, key(9)]
    call_command("rota_clau_mandats", stdout=io.StringIO())

    outputs = [caplog.text]
    for mandate in (first, second):
        outputs += [
            str(mandate),
            repr(mandate),
            str(mandate.bank_account),
            repr(mandate.bank_account),
        ]
    outputs += [str(entry.__dict__) for entry in AuditEntry.objects.all()]
    # Cap columna de text de cap taula (també l'historial i el registre d'activitat).
    for model in apps.get_models():
        for field in model._meta.concrete_fields:
            if isinstance(field, models.CharField | models.TextField | models.JSONField):
                values = model.objects.values_list(field.name, flat=True)
                outputs += [str(value) for value in values if value]
    for iban in (IBAN, OTHER_IBAN):
        assert not [text for text in outputs if iban in text]
    # L'administrador de Django no és instal·lat; si mai s'hi posa, el mandat no hi pot ser.
    if apps.is_installed("django.contrib.admin"):
        from django.contrib import admin

        assert not admin.site.is_registered(MandateBankAccount)
        assert not admin.site.is_registered(SepaMandate)


def test_ca_m05a_13_rotacio_sobre_la_taula_real(sign, settings, capsys):
    old = settings.MANDATE_ENCRYPTION_KEYS[0]
    first, second = sign(), sign(OTHER_IBAN)
    new = key(int(old.partition(":")[0]) + 1)
    settings.MANDATE_ENCRYPTION_KEYS = [old, new]

    call_command("rota_clau_mandats")
    out = capsys.readouterr().out

    assert "2." in out and "ja es pot treure la vella" in out
    version = crypto.active_version()
    assert set(MandateBankAccount.objects.values_list("key_version", flat=True)) == {version}
    settings.MANDATE_ENCRYPTION_KEYS = [new]  # es retira la vella
    assert (iban_of(first), iban_of(second)) == (IBAN, OTHER_IBAN)
    entry = AuditEntry.objects.get(action="payments.mandate_key.rotated")
    assert entry.details == {"version": version, "rows": 2}
    call_command("rota_clau_mandats")
    assert ": 0." in capsys.readouterr().out


def test_ca_m05a_13_restauracio_d_una_copia_amb_la_clau(sign, settings, tmp_path):
    offline_copy = settings.MANDATE_ENCRYPTION_KEYS[0]
    mandate = sign()
    backup = tmp_path / "copia.json"
    call_command("dumpdata", "payments.mandatebankaccount", output=str(backup))
    assert IBAN not in backup.read_text(encoding="utf-8")
    MandateBankAccount.objects.update(iban_ciphertext=b"perdut")  # la base de dades es perd

    call_command("loaddata", str(backup), verbosity=0)

    settings.MANDATE_ENCRYPTION_KEYS = [str(offline_copy)]  # entorn nou, amb la còpia de la clau
    assert iban_of(mandate) == IBAN
    settings.MANDATE_ENCRYPTION_KEYS = [f"{offline_copy.partition(':')[0]}:{key(1)[2:]}"]
    with pytest.raises(InvalidToken):
        iban_of(mandate)


def test_produccio_exigeix_la_clau(settings):
    settings.MANDATE_ENCRYPTION_KEYS_REQUIRED = True
    settings.MANDATE_ENCRYPTION_KEYS = []
    assert [e.id for e in checks.payments_settings(None)] == ["payments.E006"]
    settings.MANDATE_ENCRYPTION_KEYS = [key(1)]
    assert checks.payments_settings(None) == []
