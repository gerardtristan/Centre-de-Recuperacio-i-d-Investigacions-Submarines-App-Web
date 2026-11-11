"""Serveis del catàleg del mòdul 02 (T-M02-02; P-M02-A; RN-M02-01 i RN-M02-05; VC-20).

Capa de dades del catàleg: fitxes de cursos i d'especialitats (dos catàlegs separats), preus amb
versions i data d'entrada en vigor, tipus de sortida, subtipus de medi ambient i projectes.

- **Preu vigent:** `price_on(entry, on)` torna la versió més recent amb `valid_from` ≤ la data. Una
  activitat nova copiarà aquest preu el dia que es creï (RN-M02-05, T-M02-06); canviar un preu no
  toca mai cap activitat ja creada.
- **Canviar un preu** (`change_prices`): sempre amb motiu (resposta del 22/10/2026) i amb una data
  d'entrada en vigor que no pot ser passada (com la peça d'ajustos, RN-AJ-03). El registre
  d'activitat guarda el valor anterior de cada preu que canvia (CA-M02-01).
- **Res no s'esborra:** fitxes, tipus i subtipus es desactiven (`set_active`).

**Fora d'aquesta peça**, i sense cap codi que ho simuli:
- els **permisos** (AC6: qui manté el catàleg) són de la T-M02-33; cap vista no crida encara
  aquests serveis, i quan n'hi hagi una haurà de comprovar el permís abans;
- les **pantalles** i l'**avís del canvi de preu** al tresorer i a la junta (segona part de
  CA-M02-26) són de la T-M02-05;
- la llista de nivells, el mode de requisits per defecte i l'edat mínima són de les T-M02-29 i
  T-M02-32.

Supòsit d'implementació, per revisar: els camps de preu de la fitxa guarden el preu inicial i no
es toquen en canviar-lo; el vigent surt sempre de les versions.
"""

import datetime
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit

from .models import (
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    TrainingCatalogueEntry,
    TrainingCataloguePrice,
)

ENTRY_CREATED = "activities.catalogue.entry_created"
ENTRY_UPDATED = "activities.catalogue.entry_updated"
PRICE_CHANGED = "activities.catalogue.price_changed"
ACTIVE_CHANGED = "activities.catalogue.active_changed"
TYPE_CREATED = "activities.catalogue.type_created"

PRICE_FIELDS = ("price_member_cents", "price_non_member_cents", "reinforcement_price_cents")
# Camps de la fitxa que `update_entry` deixa canviar. Els preus, mai: tenen el seu servei.
EDITABLE_FIELDS = (
    "name",
    "level",
    "description",
    "requirements",
    "default_places",
    "open_to_non_members",
    "department",
)
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


@transaction.atomic
def update_entry(entry, *, by, request=None, **fields) -> list[str]:
    """Canvia dades de la fitxa que no són preus. Torna els camps que han canviat; el registre
    en guarda el valor anterior (P-M02-A, pas 2)."""
    unknown = set(fields) - set(EDITABLE_FIELDS)
    if unknown:
        raise ValidationError(
            _("Aquests camps no es canvien aquí: %(fields)s.")
            % {"fields": ", ".join(sorted(unknown))}
        )
    locked = TrainingCatalogueEntry.objects.select_for_update().get(pk=entry.pk)
    if "name" in fields:
        fields["name"] = _name(fields["name"])
        clash = TrainingCatalogueEntry.objects.filter(kind=locked.kind, name=fields["name"])
        if clash.exclude(pk=locked.pk).exists():
            raise ValidationError(_("Ja hi ha una fitxa amb aquest nom en aquest catàleg."))
    if "default_places" in fields:
        fields["default_places"] = _places(fields["default_places"])
    changes = {}
    for name, value in fields.items():
        old = getattr(locked, name)
        if old != value:
            changes[name] = (
                old.pk if name == "department" else old,
                value.pk if name == "department" else value,
            )
            setattr(locked, name, value)
    if changes:
        locked.save(update_fields=[*changes, "updated_at"])
        audit.record_changes(
            ENTRY_UPDATED, actor=by, target=locked, changes=changes, request=request
        )
    return sorted(changes)


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


# --- Tipus, subtipus i projectes ------------------------------------------------------------------


def _create_named(model, *, by, name, request, **fields):
    name = _name(name)
    if model.objects.filter(name=name).exists():
        raise ValidationError(_("Ja n'hi ha un amb aquest nom."))
    try:
        with transaction.atomic():
            obj = model.objects.create(name=name, **fields)
    except IntegrityError as error:  # dues peticions alhora amb el mateix nom
        raise ValidationError(_("Ja n'hi ha un amb aquest nom.")) from error
    audit.record(TYPE_CREATED, actor=by, target=obj, request=request)
    return obj


def create_outing_type(
    *, by, name, default_department, is_environmental=False, request=None
) -> OutingType:
    return _create_named(
        OutingType,
        by=by,
        name=name,
        request=request,
        default_department=default_department,
        is_environmental=bool(is_environmental),
    )


def create_subtype(*, by, name, request=None) -> EnvironmentalSubtype:
    return _create_named(EnvironmentalSubtype, by=by, name=name, request=request)


def create_project(*, by, name, objective, department, request=None) -> EnvironmentalProject:
    objective = (objective or "").strip()
    if not objective:
        raise ValidationError(_("Cal escriure l'objectiu del projecte."))
    return _create_named(
        EnvironmentalProject,
        by=by,
        name=name,
        request=request,
        objective=objective,
        department=department,
    )
