"""Bloqueig de període tancat (T-M09-02; RN-M09-16; RN-T28, RN-T30 a RN-T33 de la 04).

La 04 crida `closed_until` abans de crear cada moviment: rebutja els del 09 i les anul·lacions
manuals amb data fins a aquell dia (`PeriodClosed`) i porta els d'origen extern al període obert
amb `original_value_date`. El 09 no escriu mai als models de la 04.
"""

from django.db.models import Max

from .models import Period


def closed_until():
    """L'últim dia d'un període tancat, o `None`. Es bloqueja tot fins a aquest dia, també un
    període anterior reobert (la interfície de la 04 és una sola data, RN-T33; P-471)."""
    return Period.objects.filter(status=Period.Status.CLOSED).aggregate(day=Max("ends_on"))["day"]


def is_period_closed(day) -> bool:
    """`margins.is_period_closed(date)` (M09-8): el mateix criteri que aplica la 04."""
    until = closed_until()
    return until is not None and day <= until
