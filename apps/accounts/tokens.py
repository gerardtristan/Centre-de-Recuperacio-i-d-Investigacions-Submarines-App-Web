"""Enllaços d'un sol ús del compte personal (spec 00, RN-18; CA-04.2 a CA-04.4; V-01).

No es desa cap testimoni. Cada testimoni porta el número del compte, una empremta de l'estat
del compte i l'hora, signats amb la clau de Django i amb una sal pròpia de cada finalitat:

- un testimoni de verificació no serveix per recuperar la contrasenya, i a l'inrevés, perquè
  la sal i els camps de l'empremta són diferents;
- deixa de valer quan l'estat que en forma l'empremta canvia (un sol ús) o quan passa el
  termini de V-01.

Què l'invalida:
- verificació (48 hores): el compte deixa d'estar pendent (verificat o desactivat) o canvia
  el correu d'entrada;
- recuperació (1 hora): canvia la contrasenya, el compte entra (data d'última entrada), canvia
  l'estat o el correu;
- canvi del correu d'entrada (48 hores, com la verificació: RN-M01-79): canvia el correu (és a
  dir, se n'ha confirmat un), la contrasenya o l'estat. L'adreça nova va xifrada dins del
  testimoni (`apps.core.crypto`), perquè no quedi llegible a l'adreça de l'enllaç.

Demanar-ne un de nou no invalida els anteriors encara vigents: tots deixen de valer alhora
quan se'n fa servir un.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.core import signing
from django.utils.crypto import constant_time_compare, salted_hmac

from .models import Account


@dataclass(frozen=True)
class Purpose:
    salt: str
    max_age: timedelta
    fields: tuple[str, ...]


# V-01
VERIFY_EMAIL = Purpose(
    salt="apps.accounts.tokens.verify_email",
    max_age=timedelta(hours=48),
    fields=("login", "status"),
)
RESET_PASSWORD = Purpose(
    salt="apps.accounts.tokens.reset_password",
    max_age=timedelta(hours=1),
    fields=("login", "status", "password", "last_login"),
)
CHANGE_EMAIL = Purpose(
    salt="apps.accounts.tokens.change_email",
    max_age=timedelta(hours=48),
    fields=("login", "status", "password"),
)


# T-M01-56 (108, D.3): entrar sense contrasenya. Caducitat curta i un sol ús: entrar canvia la
# data d'última entrada, i la contrasenya o l'estat també l'invaliden.
EMAIL_LOGIN = Purpose(
    salt="apps.accounts.tokens.email_login",
    max_age=timedelta(minutes=15),
    fields=("login", "status", "password", "last_login"),
)


def _fingerprint(account: Account, purpose: Purpose) -> str:
    state = ":".join(str(getattr(account, name) or "") for name in purpose.fields)
    return salted_hmac(purpose.salt, f"{account.pk}:{state}", algorithm="sha256").hexdigest()


def make_token(account: Account, purpose: Purpose, **extra) -> str:
    """`extra`: dades més que porta el testimoni (signades, no xifrades)."""
    return signing.dumps(
        {**extra, "a": account.pk, "f": _fingerprint(account, purpose)}, salt=purpose.salt
    )


def read_token(token: str, purpose: Purpose, *, lock: bool = False) -> tuple[Account | None, dict]:
    """El compte personal del testimoni, si encara és vàlid, i les dades que porta. Amb `lock`,
    en bloqueja la fila fins al final de la transacció i hi torna a comparar l'empremta: dues
    peticions alhora amb el mateix testimoni no poden completar dues vegades la mateixa
    operació."""
    try:
        data = signing.loads(token or "", salt=purpose.salt, max_age=purpose.max_age)
        pk, fingerprint = int(data["a"]), str(data["f"])
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        return None, {}
    accounts = Account.objects.filter(pk=pk, kind=Account.Kind.PERSONAL)
    if lock:
        accounts = accounts.select_for_update()
    account = accounts.first()
    if account is None or not constant_time_compare(_fingerprint(account, purpose), fingerprint):
        return None, {}
    return account, data


def account_for_token(token: str, purpose: Purpose, *, lock: bool = False) -> Account | None:
    return read_token(token, purpose, lock=lock)[0]
