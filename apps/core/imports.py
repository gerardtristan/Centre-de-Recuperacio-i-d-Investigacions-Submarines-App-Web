"""Lots i línies d'importació (spec 00; contracte compartit de la T-M01-24).

Els altres mòduls hi escriuen només a través d'aquest servei. En el recorregut de Cluber, el lot
només es crea en confirmar i neix confirmat (T-M01-25); les transicions (desfer) no hi són.
"""

from django.utils import timezone

from .models import ImportBatch, ImportLine


def open_confirmed(kind: str, *, file_sha256: str, by, counts: dict) -> ImportBatch:
    """Lot confirmat per `by`. L'índex únic parcial en deixa un sol de Cluber confirmat: un
    segon xoca amb `IntegrityError`, i la transacció del cridant no escriu res."""
    now = timezone.now()  # un sol instant: confirmed_at ≥ created_at
    return ImportBatch.objects.create(
        kind=kind,
        status=ImportBatch.Status.CONFIRMED,
        file_sha256=file_sha256,
        created_by=by,
        created_at=now,
        confirmed_by=by,
        confirmed_at=now,
        **counts,
    )


def add_lines(batch: ImportBatch, lines: list[dict]) -> None:
    """Línies del lot: `row`, `result`, `codes` (llista tancada) i, opcional, `person`."""
    ImportLine.objects.bulk_create(ImportLine(batch=batch, **line) for line in lines)
