"""Xifratge de l'IBAN del mandat, versions de clau i rotació (T-M05a-07; 044; CA-M05a-13).

Només dades inventades: les claus es generen a cada prova i l'IBAN és l'exemple del format.
"""

from dataclasses import dataclass, field

import pytest
from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured

from apps.payments import checks, crypto

IBANS = ["ES9121000418450200051332", "ES0000000000000000000001"]


def new_key(version: int) -> str:
    return f"{version}:{Fernet.generate_key().decode()}"


@dataclass
class Row:
    """El mateix que tindrà `MandateBankAccount` (T-M05a-08): els dos camps i `save`."""

    key_version: int
    iban_ciphertext: bytes
    saves: list = field(default_factory=list)

    def save(self, update_fields):
        self.saves.append(update_fields)


def rows_for(ibans):
    return [Row(*crypto.encrypt(iban)) for iban in ibans]


def test_xifra_amb_la_versio_mes_alta_i_desxifra(settings):
    settings.MANDATE_ENCRYPTION_KEYS = [new_key(1), new_key(3), new_key(2)]
    version, ciphertext = crypto.encrypt(IBANS[0])
    assert version == 3
    assert IBANS[0].encode() not in ciphertext
    assert crypto.decrypt(version, ciphertext) == IBANS[0]
    assert crypto.decrypt(version, memoryview(ciphertext)) == IBANS[0]


def test_un_xifrat_modificat_no_es_desxifra(settings):
    settings.MANDATE_ENCRYPTION_KEYS = [new_key(1)]
    version, ciphertext = crypto.encrypt(IBANS[0])
    tampered = ciphertext[:20] + (b"B" if ciphertext[20:21] == b"A" else b"A") + ciphertext[21:]
    with pytest.raises(InvalidToken):
        crypto.decrypt(version, tampered)


def test_nomes_es_desxifra_amb_la_clau_de_la_seva_versio(settings):
    one, two = new_key(1), new_key(2)
    settings.MANDATE_ENCRYPTION_KEYS = [one]
    version, ciphertext = crypto.encrypt(IBANS[0])
    settings.MANDATE_ENCRYPTION_KEYS = [two, one]
    with pytest.raises(InvalidToken):
        crypto.decrypt(2, ciphertext)
    settings.MANDATE_ENCRYPTION_KEYS = [two]
    with pytest.raises(ImproperlyConfigured, match="versió 1"):
        crypto.decrypt(version, ciphertext)


def test_sense_claus_no_es_xifra_res(settings):
    settings.MANDATE_ENCRYPTION_KEYS = []
    with pytest.raises(ImproperlyConfigured, match="Falta MANDATE_ENCRYPTION_KEYS"):
        crypto.encrypt(IBANS[0])


@pytest.mark.parametrize(
    "raw",
    [
        ["clau-sense-versio"],
        ["0:" + Fernet.generate_key().decode()],
        ["32768:" + Fernet.generate_key().decode()],
        ["x:" + Fernet.generate_key().decode()],
        ["1:no-es-una-clau-fernet"],
        [new_key(1), "1:" + Fernet.generate_key().decode()],
    ],
)
def test_configuracio_incorrecta_sense_revelar_la_clau(settings, raw):
    settings.MANDATE_ENCRYPTION_KEYS = raw
    with pytest.raises(ImproperlyConfigured) as error:
        crypto.keys()
    assert not any(part in str(error.value) for item in raw for part in item.split(":")[1:])
    assert [e.id for e in checks.payments_settings(None)] == ["payments.E005"]


def test_la_configuracio_correcta_passa_la_comprovacio(settings):
    settings.MANDATE_ENCRYPTION_KEYS = [new_key(1), new_key(2)]
    assert checks.payments_settings(None) == []


def test_ca_m05a_13_rotacio(settings):
    """Després de la rotació, tots els IBAN es desxifren amb la clau nova i cap fila té la versió
    vella, també quan la clau vella ja no és a l'entorn."""
    old, new = new_key(1), new_key(2)
    settings.MANDATE_ENCRYPTION_KEYS = [old]
    rows = rows_for(IBANS)
    settings.MANDATE_ENCRYPTION_KEYS = [old, new]
    rows.append(Row(*crypto.encrypt("ES0000000000000000000002")))  # ja amb la nova

    assert crypto.rotate(rows) == 2

    assert {row.key_version for row in rows} == {2}
    assert [row.saves for row in rows] == [[["iban_ciphertext", "key_version"]]] * 2 + [[]]
    settings.MANDATE_ENCRYPTION_KEYS = [new]  # es retira la vella
    assert [crypto.decrypt(r.key_version, r.iban_ciphertext) for r in rows[:2]] == IBANS
    assert crypto.rotate(rows) == 0


def test_rotacio_interrompuda_es_pot_reprendre(settings):
    old, new = new_key(1), new_key(2)
    settings.MANDATE_ENCRYPTION_KEYS = [old]
    rows = rows_for(IBANS)
    settings.MANDATE_ENCRYPTION_KEYS = [old, new]
    rows[1].iban_ciphertext = b"malmes"
    with pytest.raises(InvalidToken):
        crypto.rotate(rows)
    assert [row.key_version for row in rows] == [2, 1]  # la primera ja és rotada i es pot llegir
    assert crypto.decrypt(2, rows[0].iban_ciphertext) == IBANS[0]


def test_ca_m05a_13_restauracio_d_una_copia_amb_la_clau(settings):
    """Una còpia (versió i xifrat de cada fila) es llegeix en un entorn nou configurat només amb
    la còpia de la clau guardada fora del servidor; amb una altra clau, o sense, no."""
    offline_copy = new_key(1)
    settings.MANDATE_ENCRYPTION_KEYS = [offline_copy]
    backup = [(row.key_version, bytes(row.iban_ciphertext)) for row in rows_for(IBANS)]

    settings.MANDATE_ENCRYPTION_KEYS = [str(offline_copy)]  # entorn nou
    assert [crypto.decrypt(v, c) for v, c in backup] == IBANS

    settings.MANDATE_ENCRYPTION_KEYS = [new_key(1)]
    with pytest.raises(InvalidToken):
        crypto.decrypt(*backup[0])


def test_una_copia_d_abans_de_la_rotacio_necessita_la_clau_vella(settings):
    """Per això la còpia de la clau vella es guarda mentre hi hagi còpies que la facin servir."""
    old, new = new_key(1), new_key(2)
    settings.MANDATE_ENCRYPTION_KEYS = [old]
    rows = rows_for(IBANS)
    backup = [(row.key_version, row.iban_ciphertext) for row in rows]
    settings.MANDATE_ENCRYPTION_KEYS = [old, new]
    crypto.rotate(rows)

    settings.MANDATE_ENCRYPTION_KEYS = [new]
    with pytest.raises(ImproperlyConfigured):
        crypto.decrypt(*backup[0])
    settings.MANDATE_ENCRYPTION_KEYS = [old]
    assert crypto.decrypt(*backup[0]) == IBANS[0]
