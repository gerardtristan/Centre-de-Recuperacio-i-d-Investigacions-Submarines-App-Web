"""Referència de transferència (T-M04-10; RN-T20; VT-03): `PREFIX-XXXXX-C`, amb cinc caràcters
d'un alfabet sense 0, O, 1 ni I (no es confonen en llegir-los o dictar-los) i un caràcter de
control Luhn mod N, que detecta qualsevol caràcter canviat i gairebé qualsevol parell de veïns
intercanviat. Una per càrrec, única; es genera la primera vegada que es demana i no canvia.
El prefix és `TRANSFER_REFERENCE_PREFIX` (VC-10). El servei és `treasury.transfer_reference`."""

import re
import secrets

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, transaction

from apps.core import audit
from apps.core.models import Charge

from .models import TransferReference

ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # 32 caràcters
CODE_LENGTH = 5
# Amb el guió, el codi i el control, una referència de 20 caràcters com a màxim (M04-6).
PREFIX_PATTERN = re.compile(r"[A-Z0-9]{1,12}")
REFERENCE_CREATED = "treasury.transfer_reference_created"
_ATTEMPTS = 5  # 32^5 codis: una col·lisió ja és rara; cinc seguides, impossible a la pràctica


def check_character(code: str, alphabet: str = ALPHABET) -> str:
    """Caràcter de control Luhn mod N del codi (N = mida de l'alfabet)."""
    n, total, factor = len(alphabet), 0, 2
    for char in reversed(code):
        addend = factor * alphabet.index(char)
        total += addend // n + addend % n
        factor = 3 - factor  # 2, 1, 2, 1…
    return alphabet[-total % n]


def is_valid(reference: str) -> bool:
    """És una referència d'aquesta plataforma: prefix configurat, codi de l'alfabet i control
    correcte. No diu si existeix cap càrrec amb aquesta referència."""
    prefix, _, rest = reference.rpartition("-")
    prefix, _, code = prefix.rpartition("-")
    return (
        prefix == _prefix()
        and len(code) == CODE_LENGTH
        and all(char in ALPHABET for char in code)
        and rest == check_character(code)
    )


def new_reference() -> str:
    code = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
    return f"{_prefix()}-{code}-{check_character(code)}"


def transfer_reference(charge: Charge) -> str:
    """La referència del càrrec; la primera vegada, es crea i queda al registre (RN-T20)."""
    for _ in range(_ATTEMPTS):
        existing = _reference_of(charge)
        if existing:
            return existing
        try:
            # En un punt de desament: si la base de dades rebutja el duplicat, la transacció de
            # qui crida continua. La fila i la seva entrada al registre van juntes.
            with transaction.atomic():
                row = TransferReference.objects.create(charge=charge, reference=new_reference())
                audit.record(
                    REFERENCE_CREATED,
                    actor=audit.system("treasury.transfer_reference"),
                    target=row,
                    details={"charge": charge.pk, "reference": row.reference},
                )
        except IntegrityError:
            continue  # una altra crida l'ha creada per a aquest càrrec, o el codi ja existia
        return row.reference
    raise IntegrityError("No s'ha pogut generar una referència de transferència única.")


def _reference_of(charge: Charge) -> str | None:
    return (
        TransferReference.objects.filter(charge=charge).values_list("reference", flat=True).first()
    )


def _prefix() -> str:
    prefix = settings.TRANSFER_REFERENCE_PREFIX
    if not PREFIX_PATTERN.fullmatch(prefix):
        raise ImproperlyConfigured(
            "TRANSFER_REFERENCE_PREFIX ha de tenir d'1 a 12 lletres majúscules o xifres."
        )
    return prefix
