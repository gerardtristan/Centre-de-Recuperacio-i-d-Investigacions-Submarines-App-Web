"""Xifratge de l'IBAN del mandat, amb versions de clau i rotació (T-M05a-07; decisions 044 i 051;
CA-M05a-13; docs/planning.md#M05a-12-seguretat).

- `MANDATE_ENCRYPTION_KEYS`: llista «versió:clau» separada per comes, només a l'entorn (mai al
  repositori, a la base de dades ni als registres). La versió és un enter d'1 a 32767 (cap a
  `key_version`, `PositiveSmallIntegerField`); la clau, una clau Fernet. Xifra la de versió més
  alta; cada xifrat es desxifra **només** amb la clau de la seva versió.
- Fernet (de `cryptography`, la mateixa biblioteca que `apps/core/crypto.py`) és xifratge
  autenticat: un xifrat modificat no es desxifra. Biblioteca: P-120 [A validar: informàtica].
- Rotació: s'afegeix la clau nova amb una versió més alta, `rotate` torna a xifrar cada fila amb la
  versió vella i, quan cap fila no la fa servir, es treu de l'entorn. Cada fila porta la seva
  versió: una rotació interrompuda es pot tornar a executar.
- Restauració: una còpia de la base de dades només es pot llegir amb les claus de les versions que
  hi ha; la còpia fora del servidor de cada clau es conserva mentre hi hagi còpies que la facin
  servir.
- Sense clau no hi ha alternativa: cap clau derivada ni per defecte, tampoc en local.
- Cap missatge d'error porta ni l'IBAN ni la clau.
"""

from functools import cache

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

MAX_VERSION = 32767


@cache
def _parse(raw: tuple[str, ...]) -> dict[int, Fernet]:
    keys = {}
    for item in raw:
        version, _, key = str(item).partition(":")
        if not version.isdigit() or not 1 <= int(version) <= MAX_VERSION:
            raise ImproperlyConfigured(
                f"MANDATE_ENCRYPTION_KEYS: cada clau és «versió:clau», amb una versió d'1 a "
                f"{MAX_VERSION}."
            )
        if int(version) in keys:
            raise ImproperlyConfigured(
                f"MANDATE_ENCRYPTION_KEYS: la versió {int(version)} està repetida."
            )
        try:
            keys[int(version)] = Fernet(key)
        except ValueError:
            # `from None`: la traça no ha de portar la clau.
            raise ImproperlyConfigured(
                f"MANDATE_ENCRYPTION_KEYS: la clau de la versió {int(version)} no és una clau "
                "Fernet."
            ) from None
    return keys


def keys() -> dict[int, Fernet]:
    found = _parse(tuple(settings.MANDATE_ENCRYPTION_KEYS))
    if not found:
        raise ImproperlyConfigured("Falta MANDATE_ENCRYPTION_KEYS.")
    return found


def active_version() -> int:
    return max(keys())


def encrypt(plaintext: str) -> tuple[int, bytes]:
    """La versió de la clau i el xifrat, per a `key_version` i `iban_ciphertext`."""
    version = active_version()
    return version, keys()[version].encrypt(plaintext.encode())


def decrypt(version: int, ciphertext: bytes | memoryview) -> str:
    """Llança `cryptography.fernet.InvalidToken` si el xifrat s'ha modificat."""
    fernet = keys().get(version)
    if fernet is None:
        raise ImproperlyConfigured(f"MANDATE_ENCRYPTION_KEYS no té la clau de la versió {version}.")
    # PostgreSQL torna els `BinaryField` com a `memoryview`.
    return fernet.decrypt(bytes(ciphertext)).decode()


def rotate(rows) -> int:
    """Torna a xifrar amb la clau activa les files d'una versió anterior i en desa els dos camps.

    `rows` són objectes amb `iban_ciphertext`, `key_version` i `save(update_fields=...)` (el
    `MandateBankAccount` de la T-M05a-08). Torna quantes n'ha canviat.
    """
    active = active_version()
    changed = 0
    for row in rows:
        if row.key_version == active:
            continue
        row.key_version, row.iban_ciphertext = encrypt(
            decrypt(row.key_version, row.iban_ciphertext)
        )
        row.save(update_fields=["iban_ciphertext", "key_version"])
        changed += 1
    return changed
