"""Serveis del catàleg del mòdul 02 (T-M02-02; P-M02-A; RN-M02-01 i RN-M02-05; VC-20).

- **Preu vigent:** `price_on(entry, on)`. Una activitat nova copiarà el preu vigent el dia que es
  creï (RN-M02-05); canviar un preu no toca mai cap activitat ja creada.
- **Canviar un preu** (`change_prices`): amb motiu i amb una data d'entrada en vigor no passada
  (RN-AJ-03). El registre guarda el valor anterior de cada preu que canvia (CA-M02-01).
- **Res no s'esborra:** fitxes, tipus i subtipus es desactiven (`set_active`).

Fora d'aquesta peça: els permisos (AC6, T-M02-33; cap vista no crida encara aquests serveis), les
pantalles, els serveis d'edició de fitxes, tipus, subtipus i projectes i l'avís del canvi de preu
(T-M02-05). Els camps de preu de la fitxa guarden el preu inicial; el vigent surt de les versions.
"""

import datetime
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit

from .models import (
    EnvironmentalSubtype,
    OutingType,
    TrainingCatalogueEntry,
    TrainingCataloguePrice,
)

ENTRY_CREATED = "activities.catalogue.entry_created"
PRICE_CHANGED = "activities.catalogue.price_changed"
ACTIVE_CHANGED = "activities.catalogue.active_changed"

PRICE_FIELDS = ("price_member_cents", "price_non_member_cents", "reinforcement_price_cents")
INITIAL_PRICE_NOTE = "Preu inicial de la fitxa."


@dataclass(frozen=True)
class Price:
    member_cents: int
    non_member_cents: int
    reinforcement_cents: int | None
    valid_from: datetime.date


def _cents(value, *, optional=False) -> int | None:
    """Enter de cèntims ≥ 0. `bool` és un `int` a Python: es rebutja a part."""
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(_("L'import ha de ser un enter de cèntims, zero o més."))
    return value


def _name(value) -> str:
    name = (value or "").strip()
    if not name:
        raise ValidationError(_("Cal un nom."))
    return name


def _places(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(_("Les places han de ser un enter més gran que zero."))
    return value


def entries(kind: str):
    """Les fitxes d'un dels dos catàlegs (RN-M02-01), per nom."""
    return TrainingCatalogueEntry.objects.filter(kind=kind).order_by("name")


# --- Fitxes ---------------------------------------------------------------------------------------


@transaction.atomic
def create_entry(
    *,
    by,
    kind,
    name,
    default_places,
    price_member_cents,
    price_non_member_cents,
    department,
    reinforcement_price_cents=None,
    level="",
    description="",
    requirements="",
    open_to_non_members=False,
    today=None,
    request=None,
) -> TrainingCatalogueEntry:
    """Crea una fitxa i la primera versió dels seus preus, vigent des d'avui."""
    if kind not in TrainingCatalogueEntry.Kind.values:
        raise ValidationError(_("El catàleg ha de ser el de cursos o el d'especialitats."))
    name = _name(name)
    if TrainingCatalogueEntry.objects.filter(kind=kind, name=name).exists():
        raise ValidationError(_("Ja hi ha una fitxa amb aquest nom en aquest catàleg."))
    entry = TrainingCatalogueEntry.objects.create(
        kind=kind,
        name=name,
        level=(level or "").strip(),
        description=description or "",
        requirements=requirements or "",
        default_places=_places(default_places),
        price_member_cents=_cents(price_member_cents),
        price_non_member_cents=_cents(price_non_member_cents),
        reinforcement_price_cents=_cents(reinforcement_price_cents, optional=True),
        open_to_non_members=bool(open_to_non_members),
        department=department,
    )
    TrainingCataloguePrice.objects.create(
        entry=entry,
        price_member_cents=entry.price_member_cents,
        price_non_member_cents=entry.price_non_member_cents,
        reinforcement_price_cents=entry.reinforcement_price_cents,
        valid_from=today or timezone.localdate(),
        changed_by=by,
        note=INITIAL_PRICE_NOTE,
    )
    audit.record(
        ENTRY_CREATED,
        actor=by,
        target=entry,
        details={
            "kind": entry.kind,
            "price_member_cents": entry.price_member_cents,
            "price_non_member_cents": entry.price_non_member_cents,
        },
        request=request,
    )
    return entry


def set_active(obj, active: bool, *, by, request=None) -> bool:
    """Activa o desactiva una fitxa, un tipus o un subtipus. Torna si ha canviat."""
    if not isinstance(obj, TrainingCatalogueEntry | OutingType | EnvironmentalSubtype):
        raise ValidationError(_("Això no es pot activar ni desactivar."))
    with transaction.atomic():
        locked = type(obj).objects.select_for_update().get(pk=obj.pk)
        if locked.active == bool(active):
            return False
        locked.active = bool(active)
        locked.save(update_fields=["active"])
        audit.record(
            ACTIVE_CHANGED,
            actor=by,
            target=locked,
            field="active",
            old=not locked.active,
            new=locked.active,
            request=request,
        )
    obj.active = locked.active
    return True


# --- Preus amb versions ---------------------------------------------------------------------------


def price_on(entry, on: datetime.date) -> Price:
    """Preu vigent de la fitxa en una data (RN-M02-05). Si la data és anterior a la primera
    versió, val el preu inicial de la fitxa."""
    version = (
        TrainingCataloguePrice.objects.filter(entry=entry, valid_from__lte=on)
        .order_by("-valid_from", "-pk")
        .first()
    )
    source = version or entry
    return Price(
        member_cents=source.price_member_cents,
        non_member_cents=source.price_non_member_cents,
        reinforcement_cents=source.reinforcement_price_cents,
        valid_from=version.valid_from if version else on,
    )


@transaction.atomic
def change_prices(
    entry,
    *,
    by,
    price_member_cents,
    price_non_member_cents,
    valid_from,
    note,
    reinforcement_price_cents=None,
    today=None,
    request=None,
) -> TrainingCataloguePrice:
    """Afegeix una versió dels preus, vigent des de `valid_from` (avui o més endavant). El motiu
    és obligatori. No toca cap activitat ja creada (RN-M02-05)."""
    today = today or timezone.localdate()
    note = (note or "").strip()
    if not note:
        raise ValidationError(_("Cal escriure el motiu del canvi de preu."))
    if not isinstance(valid_from, datetime.date) or isinstance(valid_from, datetime.datetime):
        raise ValidationError(_("Escriu la data d'entrada en vigor."))
    if valid_from < today:
        raise ValidationError(_("La data d'entrada en vigor no pot ser passada."))
    new = {
        "price_member_cents": _cents(price_member_cents),
        "price_non_member_cents": _cents(price_non_member_cents),
        "reinforcement_price_cents": _cents(reinforcement_price_cents, optional=True),
    }
    TrainingCatalogueEntry.objects.select_for_update().get(pk=entry.pk)
    current = price_on(entry, valid_from)
    old = {
        "price_member_cents": current.member_cents,
        "price_non_member_cents": current.non_member_cents,
        "reinforcement_price_cents": current.reinforcement_cents,
    }
    if new == old:
        raise ValidationError(_("El preu és el mateix que ja hi haurà en aquella data."))
    version = TrainingCataloguePrice.objects.create(
        entry=entry, valid_from=valid_from, changed_by=by, note=note, **new
    )
    audit.record_changes(
        PRICE_CHANGED,
        actor=by,
        target=entry,
        changes={name: (old[name], new[name]) for name in PRICE_FIELDS},
        reason=note,
        request=request,
    )
    return version


# --- Tipus i subtipus de sortida ------------------------------------------------------------------


def check_outing_classification(outing_type, subtype=None, project=None) -> None:
    """Regla de CA-M02-03 (M02-6, `Activity.subtype` i `Activity.project`): una sortida de medi
    ambient ha de tenir subtipus; una que no ho és no pot tenir ni subtipus ni projecte. El
    projecte és opcional. Un tipus o un subtipus desactivat no es pot triar (és el que vol dir
    desactivar-lo, P-M02-A pas 3); si un projecte acabat es pot fer servir no ho diu cap regla i
    aquí no es comprova. La cridarà el servei que desa una activitat (T-M02-06)."""
    if outing_type is None:
        raise ValidationError(_("Cal triar el tipus de sortida."))
    if not outing_type.active:
        raise ValidationError(_("Aquest tipus de sortida està desactivat."))
    if outing_type.is_environmental:
        if subtype is None:
            raise ValidationError(_("Una sortida de medi ambient ha de tenir subtipus."))
        if not subtype.active:
            raise ValidationError(_("Aquest subtipus està desactivat."))
        return
    if subtype is not None or project is not None:
        raise ValidationError(_("Només les sortides de medi ambient tenen subtipus i projecte."))
