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
- **Permís (T-M02-33):** tot servei que canvia el catàleg demana AC6 amb edició
  (`activities.catalogue.manage`); sense, «no trobat», també cridat fora d'una vista. Llegir el
  catàleg (`entries`, `price_on`) no demana cap permís aquí: ho decideix qui ho mostra.

- **Avís del canvi de preu** (T-M02-05; RN-AJ-04; segona part de CA-M02-26): `change_prices`
  crida `business_settings.notify_money_change`, la peça comuna que envia el correu al tresorer i
  a la junta amb el preu anterior, el nou, qui l'ha canviat, el motiu i la data. Qui el rep ho
  decideix aquella peça (T-AJ-01), no aquest mòdul.

**Fora d'aquesta peça**, i sense cap codi que ho simuli:
- les **pantalles** són a `apps/activities/views/admin_catalogue.py` (T-M02-05);
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

from apps.core import audit, business_settings
from apps.core.charges import euros

from . import permissions
from .models import (
    CertificationLevel,
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    RequirementsMode,
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
    "default_requirements_mode",
    "min_age",
)
MODE_CHANGED = "activities.catalogue.default_mode_changed"
LEVEL_CREATED = "activities.catalogue.level_created"
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


def _mode(value) -> str:
    """Mode de requisits per defecte d'una fitxa o d'un tipus: avís, bloqueig o buit (val
    l'ajust general, RN-M02-29)."""
    value = value or ""
    if value not in ("", *RequirementsMode.values):
        raise ValidationError(_("El mode de requisits ha de ser «avís», «bloqueig» o cap."))
    return value


def _min_age(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 99:
        raise ValidationError(_("L'edat mínima ha de ser un nombre d'anys entre 1 i 99."))
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
    default_requirements_mode="",
    min_age=None,
    today=None,
    request=None,
) -> TrainingCatalogueEntry:
    """Crea una fitxa i la primera versió dels seus preus, vigent des d'avui."""
    permissions.require(by, permissions.CATALOGUE)
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
        default_requirements_mode=_mode(default_requirements_mode),
        min_age=_min_age(min_age),
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
    permissions.require(by, permissions.CATALOGUE)
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
    if "default_requirements_mode" in fields:
        fields["default_requirements_mode"] = _mode(fields["default_requirements_mode"])
    if "min_age" in fields:
        fields["min_age"] = _min_age(fields["min_age"])
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
    """Activa o desactiva una fitxa, un tipus, un subtipus o un nivell. Torna si ha canviat."""
    permissions.require(by, permissions.CATALOGUE)
    kinds = TrainingCatalogueEntry | OutingType | EnvironmentalSubtype | CertificationLevel
    if not isinstance(obj, kinds):
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
    permissions.require(by, permissions.CATALOGUE)
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
    business_settings.notify_money_change(
        what=_("Preu del catàleg: %(name)s") % {"name": entry.name},
        previous=describe_prices(current),
        new=describe_prices(price_on(entry, valid_from)),
        changed_by=by,
        note=note,
        effective_from=valid_from,
    )
    return version


def describe_prices(price: Price) -> str:
    """Els preus en una línia, per al correu de l'avís i per a les pantalles."""
    text = _("soci %(member)s; no soci %(non_member)s") % {
        "member": euros(price.member_cents),
        "non_member": euros(price.non_member_cents),
    }
    if price.reinforcement_cents is not None:
        text += _("; reforç %(amount)s") % {"amount": euros(price.reinforcement_cents)}
    return text


def price_versions(entry):
    """Totes les versions dels preus de la fitxa, de la més recent a la més antiga."""
    return entry.prices.select_related("changed_by__person").order_by("-valid_from", "-pk")


def next_price(entry, today: datetime.date) -> Price | None:
    """El primer canvi de preu que encara ha d'entrar en vigor, o `None`."""
    upcoming = entry.prices.filter(valid_from__gt=today).order_by("valid_from", "pk").first()
    return price_on(entry, upcoming.valid_from) if upcoming else None


# --- Tipus, subtipus i projectes ------------------------------------------------------------------


def _create_named(model, *, by, name, request, **fields):
    permissions.require(by, permissions.CATALOGUE)
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
    *,
    by,
    name,
    default_department,
    is_environmental=False,
    default_requirements_mode="",
    request=None,
) -> OutingType:
    return _create_named(
        OutingType,
        by=by,
        name=name,
        request=request,
        default_department=default_department,
        is_environmental=bool(is_environmental),
        default_requirements_mode=_mode(default_requirements_mode),
    )


@transaction.atomic
def set_outing_type_mode(outing_type, mode, *, by, request=None) -> bool:
    """Canvia el mode de requisits que copien les sortides noves d'aquest tipus (RN-M02-29;
    CA-M02-34). Les sortides ja creades no canvien. Torna si ha canviat."""
    permissions.require(by, permissions.CATALOGUE)
    mode = _mode(mode)
    locked = OutingType.objects.select_for_update().get(pk=outing_type.pk)
    if locked.default_requirements_mode == mode:
        return False
    old = locked.default_requirements_mode
    locked.default_requirements_mode = mode
    locked.save(update_fields=["default_requirements_mode"])
    outing_type.default_requirements_mode = mode
    audit.record(
        MODE_CHANGED,
        actor=by,
        target=locked,
        field="default_requirements_mode",
        old=old,
        new=mode,
        request=request,
    )
    return True


# --- Nivells de titulació (addenda de la 058; RN-M02-27) ------------------------------------------


def levels():
    """Tots els nivells, del més baix al més alt."""
    return CertificationLevel.objects.order_by("rank")


@transaction.atomic
def create_level(*, by, name, rank, agency="", request=None) -> CertificationLevel:
    """Afegeix un nivell a la llista. L'ordre (`rank`) diu quin és més alt: no es pot repetir."""
    permissions.require(by, permissions.CATALOGUE)
    name = _name(name)
    if isinstance(rank, bool) or not isinstance(rank, int) or not 1 <= rank <= 999:
        raise ValidationError(_("L'ordre del nivell ha de ser un nombre entre 1 i 999."))
    if CertificationLevel.objects.filter(name=name).exists():
        raise ValidationError(_("Ja n'hi ha un amb aquest nom."))
    if CertificationLevel.objects.filter(rank=rank).exists():
        raise ValidationError(_("Ja hi ha un nivell amb aquest ordre."))
    level = CertificationLevel.objects.create(
        name=name, rank=rank, agency=(agency or "").strip()[:60]
    )
    audit.record(LEVEL_CREATED, actor=by, target=level, details={"rank": rank}, request=request)
    return level


def create_subtype(*, by, name, request=None) -> EnvironmentalSubtype:
    return _create_named(EnvironmentalSubtype, by=by, name=name, request=request)


def check_outing_classification(outing_type, subtype=None, project=None) -> None:
    """Regla de CA-M02-03 (M02-6, `Activity.subtype` i `Activity.project`): una sortida de medi
    ambient ha de tenir subtipus; una que no ho és no pot tenir ni subtipus ni projecte. El
    projecte és opcional. Un tipus o un subtipus desactivat no es pot triar (és el que vol dir
    desactivar-lo, P-M02-A pas 3); si un projecte acabat es pot fer servir no ho diu cap regla i
    aquí no es comprova. La criden el servei que desa una sortida (`services.create_outing`) i el
    que l'edita (`services.update_activity`)."""
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
