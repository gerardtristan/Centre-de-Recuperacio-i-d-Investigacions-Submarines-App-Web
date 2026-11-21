"""Llista de lloguer per centre (T-M03-10; P-M03-D pas 5; RN-M03-18; CA-M03-07; MT9).

- `generate(activity, centre, by=…)`: les línies dels lloguers vius de l'activitat en el centre,
  agrupades per tipus i talla, amb una referència per participant (número d'inscripció i
  inicials; mai el nom complet ni el contacte [A validar: junta, S-M03-04]). El contingut **no es
  desa**: queda una `RentalList` amb l'empremta, qui i quan, i una entrada al registre.
- `to_csv(content)`: CSV per enviar pel canal del club, protegit contra fórmules.
- `mark_sent(rental_list, by=…)`: «enviada», una sola vegada.
"""

import csv
import hashlib
import io
import json
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit

from .access import require
from .costs import rentals_for
from .models import EquipmentNeed, RentalList

MANAGE = "equipment.rental_lists.manage"  # MT9
GENERATED = "equipment.rental_list_generated"
SENT = "equipment.rental_list_sent"


@dataclass(frozen=True)
class RentalContent:
    rental_list: RentalList
    # (tipus, talla, quantitat, referències ordenades)
    lines: tuple[tuple[str, str, int, tuple[str, ...]], ...]


def reference(enrolment) -> str:
    """Número d'inscripció i inicials (RN-M03-18)."""
    person = enrolment.person
    initials = "".join(part[:1].upper() for part in (person.first_name, person.last_name) if part)
    return f"{enrolment.pk}-{initials}"


def _lines(activity, centre):
    groups: dict[tuple[str, str], list[str]] = {}
    rows = rentals_for(activity, centre).select_related("enrolment__person", "item")
    sizes = _sizes(activity)
    for row in rows:
        size = sizes.get((row.enrolment_id, row.equipment_type_id), "")
        groups.setdefault((row.equipment_type.name, size), []).append(reference(row.enrolment))
    return tuple(
        (name, size, len(refs), tuple(sorted(refs)))
        for (name, size), refs in sorted(groups.items())
    )


def _sizes(activity) -> dict:
    """La talla (o els litres) que el participant va dir que necessitava (T-M03-07)."""
    return {
        (n.enrolment_id, n.equipment_type_id): n.size or (str(n.litres) if n.litres else "")
        for n in EquipmentNeed.objects.filter(enrolment__activity=activity)
    }


def generate(activity, centre, *, by, now=None) -> RentalContent:
    require(by, MANAGE, activity)
    lines = _lines(activity, centre)
    fingerprint = hashlib.sha256(json.dumps(lines, ensure_ascii=False).encode()).hexdigest()
    with transaction.atomic():
        rental_list = RentalList.objects.create(
            activity=activity, centre=centre, generated_by=by,
            generated_at=now or timezone.now(), fingerprint=fingerprint,
        )  # fmt: skip
        audit.record(
            GENERATED, actor=by, target=rental_list,
            details={"activity": activity.pk, "centre": centre.pk, "fingerprint": fingerprint},
        )  # fmt: skip
    return RentalContent(rental_list, lines)


def _safe(text: str) -> str:
    # Un text que comença com una fórmula no s'ha d'executar en obrir el CSV.
    return f"'{text}" if text[:1] in ("=", "+", "-", "@") else text


def to_csv(content: RentalContent) -> str:
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";", lineterminator="\n")
    writer.writerow([_("Material"), _("Talla"), _("Quantitat"), _("Referències")])
    for name, size, quantity, refs in content.lines:
        writer.writerow([_safe(name), _safe(size), quantity, " ".join(refs)])
    return out.getvalue()


def mark_sent(rental_list, *, by, now=None) -> RentalList:
    require(by, MANAGE, rental_list.activity)
    with transaction.atomic():
        row = RentalList.objects.select_for_update().get(pk=rental_list.pk)
        if row.sent_at is not None:
            raise ValidationError(_("Aquesta llista ja és enviada."))
        row.sent_at, row.sent_by = now or timezone.now(), by
        row.save(update_fields=["sent_at", "sent_by"])
        audit.record(SENT, actor=by, target=row, details={"fingerprint": row.fingerprint})
    return row


def unsent(activity) -> list[RentalList]:
    """La darrera llista de cada centre, si no s'ha enviat (motiu de «material pendent»,
    RN-M03-13). Tornar-la a generar no deixa enrere les anteriors com a pendents."""
    latest: dict[int, RentalList] = {}
    for row in RentalList.objects.filter(activity=activity).order_by("generated_at", "pk"):
        latest[row.centre_id] = row
    return [row for row in latest.values() if row.sent_at is None]
