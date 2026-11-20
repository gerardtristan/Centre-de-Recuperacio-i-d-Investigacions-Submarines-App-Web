"""Serveis del catàleg del mòdul 02 (T-M02-02; P-M02-A; RN-M02-01 i RN-M02-05; VC-20).

Una activitat nova copiarà el preu vigent el dia que es creï (`price_on`); canviar un preu no toca
cap activitat ja creada. Res no s'esborra: es desactiva. Fora d'aquesta peça: els permisos (AC6,
T-M02-33; cap vista no crida encara aquests serveis), les pantalles, els serveis d'edició i l'avís
del canvi de preu (T-M02-05).

Llocs (T-M02-37; addenda de llocs, RN-M02-38 i 39): crear, editar, desactivar i el preu estàndard
amb versions, que avisa el tresorer i la junta (RN-AJ-04). Els permisos (AC21 i AC22) són de la
T-M02-38 i la pantalla, de la T-M02-39: cap vista no crida encara aquests serveis.
"""

import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.business_settings import notify_money_change
from apps.core.charges import euros

from .models import (
    EnvironmentalSubtype,
    OutingType,
    Place,
    PlacePrice,
    TrainingCatalogueEntry,
    TrainingCataloguePrice,
)

ENTRY_CREATED = "activities.catalogue.entry_created"
PRICE_CHANGED = "activities.catalogue.price_changed"
ACTIVE_CHANGED = "activities.catalogue.active_changed"
PLACE_CREATED = "activities.place.created"
PLACE_UPDATED = "activities.place.updated"
PLACE_PRICE_CHANGED = "activities.place.price_changed"
PLACE_NOTES_MAX = 1000

PRICE_FIELDS = ("price_member_cents", "price_non_member_cents", "reinforcement_price_cents")
INITIAL_PRICE_NOTE = "Preu inicial de la fitxa."


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


def _note_and_date(note, valid_from, today) -> str:
    """Un canvi de preu porta motiu i una data d'entrada en vigor no passada (RN-AJ-03)."""
    note = (note or "").strip()
    if not note:
        raise ValidationError(_("Cal escriure el motiu del canvi de preu."))
    if not isinstance(valid_from, datetime.date) or isinstance(valid_from, datetime.datetime):
        raise ValidationError(_("Escriu la data d'entrada en vigor."))
    if valid_from < (today or timezone.localdate()):
        raise ValidationError(_("La data d'entrada en vigor no pot ser passada."))
    return note


def _places(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(_("Les places han de ser un enter més gran que zero."))
    return value


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
    """Activa o desactiva una fitxa, un tipus, un subtipus o un lloc. Torna si ha canviat."""
    if not isinstance(obj, TrainingCatalogueEntry | OutingType | EnvironmentalSubtype | Place):
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


def price_on(entry, on: datetime.date):
    """Preus vigents de la fitxa en una data (RN-M02-05): la versió més recent que ja ha entrat en
    vigor o, abans de la primera, la fitxa. Tots dos tenen els tres camps de `PRICE_FIELDS`."""
    return (
        TrainingCataloguePrice.objects.filter(entry=entry, valid_from__lte=on)
        .order_by("-valid_from", "-pk")
        .first()
    ) or entry


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
    note = _note_and_date(note, valid_from, today)
    new = {
        "price_member_cents": _cents(price_member_cents),
        "price_non_member_cents": _cents(price_non_member_cents),
        "reinforcement_price_cents": _cents(reinforcement_price_cents, optional=True),
    }
    TrainingCatalogueEntry.objects.select_for_update().get(pk=entry.pk)
    current = price_on(entry, valid_from)
    old = {name: getattr(current, name) for name in PRICE_FIELDS}
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


def check_outing_classification(outing_type, subtype=None, project=None) -> None:
    """CA-M02-03: una sortida de medi ambient ha de tenir subtipus; una altra, ni subtipus ni
    projecte. Un tipus o subtipus desactivat no es pot triar (P-M02-A pas 3); un projecte acabat no
    es comprova (cap regla no ho diu). La cridarà el desat d'una activitat (T-M02-06)."""
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


def _place_fields(name, notes, *, exclude=None) -> dict:
    name = _name(name)
    if Place.objects.filter(name__iexact=name).exclude(pk=exclude).exists():
        raise ValidationError(_("Ja hi ha un lloc amb aquest nom."))
    notes = (notes or "").strip()
    if len(notes) > PLACE_NOTES_MAX:
        raise ValidationError(_("Les notes no poden passar de 1000 caràcters."))
    return {"name": name, "notes": notes}


def create_place(*, by, name, notes="", request=None) -> Place:
    """RN-M02-38: un lloc nou, actiu, sense preu estàndard fins que se n'hi posa un."""
    with transaction.atomic():
        place = Place.objects.create(created_by=by, **_place_fields(name, notes))
        audit.record(PLACE_CREATED, actor=by, target=place, request=request)
    return place


@transaction.atomic
def update_place(place, *, by, name, notes="", request=None) -> list[str]:
    """Canvia el nom o les notes; el registre guarda el valor anterior (RN-M02-38)."""
    locked = Place.objects.select_for_update().get(pk=place.pk)
    new = _place_fields(name, notes, exclude=locked.pk)
    changes = {k: (getattr(locked, k), v) for k, v in new.items() if getattr(locked, k) != v}
    if changes:
        Place.objects.filter(pk=locked.pk).update(**new)
        audit.record_changes(
            PLACE_UPDATED, actor=by, target=locked, changes=changes, request=request
        )
    return sorted(changes)


def place_price_on(place, on: datetime.date) -> PlacePrice | None:
    """Preu estàndard vigent del lloc en una data (RN-M02-39), o `None` si no en té."""
    return (
        PlacePrice.objects.filter(place=place, valid_from__lte=on)
        .order_by("-valid_from", "-pk")
        .first()
    )


def _show(price) -> str:
    if price is None:
        return "—"
    return f"{euros(price['price_member_cents'])} / {euros(price['price_non_member_cents'])}"


@transaction.atomic
def change_place_price(
    place,
    *,
    by,
    price_member_cents,
    price_non_member_cents,
    valid_from,
    note,
    today=None,
    request=None,
) -> PlacePrice:
    """RN-M02-39: una fila nova de preu estàndard, vigent des de `valid_from` (avui o més
    endavant), amb nota. No toca cap activitat ja creada (RN-M02-42). Un sol avís (RN-AJ-04)."""
    note = _note_and_date(note, valid_from, today)
    new = {
        "price_member_cents": _cents(price_member_cents),
        "price_non_member_cents": _cents(price_non_member_cents),
    }
    Place.objects.select_for_update().get(pk=place.pk)
    current = place_price_on(place, valid_from)
    old = {name: getattr(current, name) for name in new} if current else None
    if new == old:
        raise ValidationError(_("El preu és el mateix que ja hi haurà en aquella data."))
    version = PlacePrice.objects.create(
        place=place, valid_from=valid_from, changed_by=by, note=note, **new
    )
    audit.record_changes(
        PLACE_PRICE_CHANGED,
        actor=by,
        target=place,
        changes={name: ((old or {}).get(name), new[name]) for name in new},
        reason=note,
        request=request,
    )
    notify_money_change(
        what=_("Preu estàndard del lloc «%(place)s» (soci / no soci)") % {"place": place.name},
        previous=_show(old),
        new=_show(new),
        changed_by=by,
        note=note,
        effective_from=valid_from,
    )
    return version
