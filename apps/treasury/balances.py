"""Saldos calculats (RN-T02; CA-T02.1 i CA-T02.2; T-M04-04): l'únic lloc on es calculen. El
saldo d'un compte a una data és la suma de les entrades menys la de les sortides amb data de
valor fins a aquella data. No es desa enlloc. Un contramoviment és de sentit contrari, de manera
que un moviment anul·lat ja hi suma zero, i un trànsit liquidat torna a zero pel traspàs del net
i les comissions (CA-T02.2)."""

from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce

from .models import Movement, TreasuryAccount


def _total(direction, on):
    return Coalesce(
        Sum(
            "movements__amount_cents",
            filter=Q(movements__direction=direction, movements__value_date__lte=on),
        ),
        Value(0),
    )


def balances(on):
    """Tots els comptes, actius primer, amb `balance_cents` a la data `on`, en una sola consulta."""
    return TreasuryAccount.objects.annotate(
        balance_cents=_total(Movement.Direction.IN, on) - _total(Movement.Direction.OUT, on)
    ).order_by("-active", "kind", "name")


def balance(account, on) -> int:
    """El saldo d'un compte a la data `on`, en cèntims (RNF-T7: menys d'un segon amb 50.000
    moviments). El mateix càlcul que `balances`, perquè només n'hi hagi un."""
    return balances(on).get(pk=account.pk).balance_cents
