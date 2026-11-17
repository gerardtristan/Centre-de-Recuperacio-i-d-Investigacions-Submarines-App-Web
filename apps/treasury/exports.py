"""Exportació CSV dels moviments per a la gestoria (T-M04-16; HU-T15, P-M04-G, CA-T15.1).

Data, compte, concepte, departament, centre de cost, entrada, sortida i referència, en euros amb
dos decimals. Cap dada personal més enllà del concepte, que ja no porta noms (RNF-T4), i cap IBAN:
del compte, només el nom (RN-T03). El format és el de les exportacions del 01 (UTF-8 amb BOM, «;»
i les fórmules amb un apòstrof davant). Un moviment anul·lat i el seu contramoviment hi surten
tots dos: sumen zero, com al saldo (RN-T25)."""

from django.utils.translation import gettext as _

from apps.members.roster import to_csv

from .models import Movement


def amount(cents: int) -> str:
    """«1234,56»: dos decimals amb coma i sense separador de milers, per al full de càlcul."""
    return f"{cents // 100},{cents % 100:02d}"


def reference(movement: Movement) -> str:
    """La del pagament (transferència o proveïdor) o, si no n'hi ha, la de la liquidació (P-241,
    opció per defecte)."""
    payment = movement.payment
    if payment and (payment.transfer_reference or payment.provider_reference):
        return payment.transfer_reference or payment.provider_reference
    return movement.settlement.external_id if movement.settlement else ""


def headers() -> list[str]:
    return [
        _("Data"),
        _("Compte"),
        _("Concepte"),
        _("Departament"),
        _("Centre de cost"),
        _("Entrada"),
        _("Sortida"),
        _("Referència"),
    ]


def row(movement: Movement) -> list[str]:
    value = amount(movement.amount_cents)
    entry = movement.direction == Movement.Direction.IN
    return [
        movement.value_date.strftime("%d/%m/%Y"),
        movement.account.name,
        movement.concept,
        movement.department.name if movement.department else "",
        movement.cost_centre.name if movement.cost_centre else "",
        value if entry else "",
        "" if entry else value,
        reference(movement),
    ]


def movements_csv(movements) -> tuple[bytes, int]:
    """El CSV dels moviments, del més antic al més recent per data de valor, i quantes files."""
    movements = movements.select_related(
        "account", "department", "cost_centre", "payment", "settlement"
    ).order_by("value_date", "recorded_at", "id")
    rows = [row(movement) for movement in movements]
    return to_csv(headers(), rows), len(rows)
