"""Lots i línies d'importació (spec 00; contracte compartit de la T-M01-24).

Els altres mòduls hi escriuen només a través d'aquest servei. En el recorregut de Cluber, el lot
només es crea en confirmar i neix confirmat (T-M01-25). Desfer un lot (`mark_undone`) també
passa per aquí (P-445): el mòdul comprova les seves regles i desfà el que ha creat, i el nucli
marca el lot.
"""

from django.utils import timezone

from ..models import ImportBatch, ImportLine


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


def mark_undone(batch: ImportBatch, *, by) -> ImportBatch:
    """Lot confirmat → desfet per `by`, ara (P-445). El cridant l'ha bloquejat dins la seva
    transacció i ja ha comprovat les seves regles; un lot que no és confirmat no es toca."""
    if batch.status != ImportBatch.Status.CONFIRMED:
        raise ValueError(f"Només es desfà un lot confirmat (el {batch.pk} és «{batch.status}»).")
    batch.status, batch.undone_by, batch.undone_at = ImportBatch.Status.UNDONE, by, timezone.now()
    batch.save(update_fields=["status", "undone_by", "undone_at"])
    return batch


def add_lines(batch: ImportBatch, lines: list[dict]) -> None:
    """Línies del lot: `row`, `result`, `codes` (llista tancada) i, opcional, `person`."""
    ImportLine.objects.bulk_create(ImportLine(batch=batch, **line) for line in lines)


def statement_lines(batch: ImportBatch | None = None):
    """Línies de l'extracte que la conciliació (04, T-M04-11) pot casar: les noves dels lots
    confirmats. Les d'un lot desfet hi deixen de sortir (CA-21.4)."""
    lines = ImportLine.objects.filter(
        batch__kind=ImportBatch.Kind.BANK_STATEMENT,
        batch__status=ImportBatch.Status.CONFIRMED,
        result=ImportLine.Result.NEW,
    )
    return lines if batch is None else lines.filter(batch=batch)
