"""Crear i editar activitats (T-M02-03c; P-M02-B, passos 1 i 3; M02-6; RN-M02-05 i RN-M02-06,
precisada per RN-M02-40 i 41 de l'addenda de llocs; CA-M02-01 a 03, CA-M02-26 i la part de dades
de CA-M02-43).

- **Curs** (`create_course`): surt d'una fitxa activa del catàleg (de cursos o d'especialitats).
  Copia les places, si és oberta a no socis, el departament i el **preu vigent el dia que es crea**
  (RN-M02-05) a `price_*` i a la còpia estàndard `standard_price_*` (RN-M02-40). El lloc és
  opcional (és a cada sessió).
- **Sortida** (`create_outing`): amb un tipus i, només si és de medi ambient, subtipus i projecte
  (CA-M02-03), i un lloc actiu. Copia el preu estàndard vigent avui del lloc; si el lloc no en té,
  la còpia queda buida i el responsable escriu el preu sense nota (RN-M02-40).
- **Preu diferent de l'estàndard** (RN-M02-41, CA-M02-02 i 43): si un preu difereix de la còpia
  estàndard de l'activitat, sense motiu es rebutja; amb motiu, es desa i el registre guarda la
  còpia i el preu. Es compara amb la còpia, mai amb el preu vigent avui (RN-M02-42).
- **Lloc** (RN-M02-40): canviar-lo en esborrany torna a copiar el preu estàndard del lloc nou; en
  una activitat oberta o posterior no toca cap preu.
- **Centre de cost**: opcional, actiu i del mateix departament (com el càrrec de la 00).
- **Permís:** AC7 amb edició (`activities.manage`); sense, «no trobat».
- Una activitat neix en esborrany (`draft`). L'estat només el canvia `apps.activities.states`.

Concrecions (diari de la T-M02-03c): una fitxa desactivada no es tria per a un curs nou; la data
límit d'inscripció no passa del dia d'inici; el motiu es demana quan un canvi deixa un preu diferent
de la còpia estàndard; el termini de pagament i el mode de requisits per defecte són ajustos (VC-21
i VC-24), creats a `activities/0004`; la pantalla per editar-los és de la T-M02-28.

**Fora d'aquesta peça:** l'avís al tresorer del preu diferent (plantilla del correu, T-M02-06), els
avisos als inscrits quan canvia el lloc o el programa (T-M02-21), el cost de material previst (AC23
i C7, T-M02-40), no baixar les places per sota de les ocupades (L-M02-03, T-M02-12), duplicar
(T-M02-07), els camps de l'addenda de la 058 (T-M02-29 i T-M02-32) i les pantalles (T-M02-06).
"""

import datetime

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, business_settings
from apps.core.models import Department, Person

from . import catalogue, permissions, states
from .models import (
    Activity,
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    Place,
    RequirementsMode,
)

ACTIVITY_CREATED = "activities.activity.created"
ACTIVITY_UPDATED = "activities.activity.updated"

# Ajustos del 02 (M02-6, «Valors configurables»; claus creades a `activities/0004`).
PAYMENT_WINDOW_KEY = "activities.default_payment_window_hours"  # VC-21
REQUIREMENTS_MODE_KEY = "activities.default_requirements_mode"  # VC-24

PRICE_FIELDS = ("price_member_cents", "price_non_member_cents")
_TEXT_FIELDS = ("title", "description", "meeting_point", "required_level")
STANDARD_FIELDS = ("standard_price_member_cents", "standard_price_non_member_cents")
_COMMON_FIELDS = (
    *_TEXT_FIELDS,
    "starts_on",
    "ends_on",
    "max_places",
    "registration_closes_at",
    "payment_window_hours",
    *PRICE_FIELDS,
    "price_override_note",
    "open_to_non_members",
    "licence_required",
    "requirements_mode",
    "responsible",
    "forecast_url",
    "department",
    "cost_centre",
    "place",
)
# Camps que `update_activity` deixa canviar. La classe, la fitxa del catàleg i l'estat, mai.
EDITABLE_FIELDS = {
    Activity.Kind.COURSE: frozenset(_COMMON_FIELDS),
    Activity.Kind.OUTING: frozenset((*_COMMON_FIELDS, "outing_type", "subtype", "project")),
}
_FOREIGN_KEYS = {
    "department": Department,
    "responsible": Person,
    "outing_type": OutingType,
    "subtype": EnvironmentalSubtype,
    "project": EnvironmentalProject,
    "place": Place,
    "cost_centre": None,  # de la tresoreria: es comprova pels camps, sense importar-la
}
_MAX_LENGTH = {name: Activity._meta.get_field(name).max_length for name in _TEXT_FIELDS}
_https = URLValidator(schemes=["https"])


def _positive(value, message) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(message)
    return value


def _clean(data: dict) -> dict:
    """Valida i normalitza els camps comuns que hi hagi a `data` (crear i editar)."""
    out = dict(data)
    for name in _TEXT_FIELDS:
        if name in out:
            out[name] = (out[name] or "").strip()
            if _MAX_LENGTH[name] is not None and len(out[name]) > _MAX_LENGTH[name]:
                raise ValidationError(
                    _("El text és massa llarg (màxim, %(max)s caràcters).")
                    % {"max": _MAX_LENGTH[name]}
                )
    if "title" in out and not out["title"]:
        raise ValidationError(_("Cal un títol."))
    for name in ("starts_on", "ends_on"):
        if name in out and (
            not isinstance(out[name], datetime.date) or isinstance(out[name], datetime.datetime)
        ):
            raise ValidationError(_("Escriu la data d'inici i la de final."))
    if "registration_closes_at" in out:
        closes = out["registration_closes_at"]
        if not isinstance(closes, datetime.datetime) or timezone.is_naive(closes):
            raise ValidationError(_("Escriu la data límit d'inscripció, amb dia i hora."))
    if "max_places" in out:
        _positive(out["max_places"], _("Les places han de ser un enter més gran que zero."))
    if "payment_window_hours" in out:
        _positive(
            out["payment_window_hours"],
            _("El termini de pagament ha de ser un nombre d'hores més gran que zero."),
        )
    for name in PRICE_FIELDS:
        if name in out:
            out[name] = catalogue._cents(out[name])
    if "price_override_note" in out:
        out["price_override_note"] = (out["price_override_note"] or "").strip()
    for name in ("open_to_non_members", "licence_required"):
        if name in out:
            out[name] = bool(out[name])
    if "requirements_mode" in out and out["requirements_mode"] not in RequirementsMode.values:
        raise ValidationError(_("El mode de requisits ha de ser «avís» o «bloqueig»."))
    if "responsible" in out:
        person = out["responsible"]
        if not isinstance(person, Person) or person.status != Person.Status.ACTIVE:
            raise ValidationError(_("Cal triar la persona responsable de l'activitat."))
    if "department" in out:
        department = out["department"]
        if not isinstance(department, Department) or not department.active:
            raise ValidationError(_("Cal triar un departament actiu."))
    if "forecast_url" in out:
        out["forecast_url"] = (out["forecast_url"] or "").strip()
        if out["forecast_url"]:
            try:
                _https(out["forecast_url"])
            except ValidationError:
                raise ValidationError(
                    _("L'enllaç a la previsió ha de ser una adreça que comenci per https://.")
                ) from None
    return out


def _check_place(place, *, required) -> None:
    if place is None:
        if required:
            raise ValidationError(_("Cal triar el lloc de la sortida."))
        return
    if not isinstance(place, Place):
        raise ValidationError(_("El lloc no és vàlid."))
    if not place.active:  # RN-M02-38: un lloc desactivat no es tria per a res nou
        raise ValidationError(_("Aquest lloc està desactivat."))


def _check_cost_centre(centre, department) -> None:
    if centre is None:
        return
    if getattr(centre, "department_id", None) != department.pk or not centre.active:
        raise ValidationError(_("El centre de cost ha de ser actiu i del departament triat."))


def _standard(price) -> dict:
    """La còpia estàndard d'un preu del catàleg o d'un lloc (RN-M02-40); buida si no n'hi ha."""
    if price is None:
        return dict.fromkeys(STANDARD_FIELDS)
    return {
        "standard_price_member_cents": price.price_member_cents,
        "standard_price_non_member_cents": price.price_non_member_cents,
    }


def _check_dates(starts_on, ends_on, registration_closes_at) -> None:
    if ends_on < starts_on:
        raise ValidationError(_("La data de final no pot ser anterior a la d'inici."))
    if timezone.localdate(registration_closes_at) > starts_on:
        raise ValidationError(_("La data límit d'inscripció no pot passar del dia d'inici."))


def _differs(data: dict) -> bool:
    """RN-M02-41: algun preu difereix de la seva còpia estàndard (sense còpia, no hi ha res a
    comparar)."""
    return any(
        data[standard] is not None and data[price] != data[standard]
        for price, standard in zip(PRICE_FIELDS, STANDARD_FIELDS, strict=True)
    )


def _require_note(data: dict) -> None:
    if _differs(data) and not data.get("price_override_note"):
        raise ValidationError(_("El preu és diferent de l'estàndard: cal escriure'n el motiu."))


def _create(*, by, request, details: bool, **fields) -> Activity:
    activity = Activity.objects.create(**fields)
    audit.record(
        ACTIVITY_CREATED,
        actor=by,
        target=activity,
        reason=activity.price_override_note,
        details={
            "kind": activity.kind,
            "price_member_cents": activity.price_member_cents,
            "price_non_member_cents": activity.price_non_member_cents,
            **({name: getattr(activity, name) for name in STANDARD_FIELDS} if details else {}),
        },
        request=request,
    )
    return activity


def _defaults(data: dict) -> dict:
    data.setdefault("payment_window_hours", business_settings.get(PAYMENT_WINDOW_KEY))
    data.setdefault("requirements_mode", business_settings.get(REQUIREMENTS_MODE_KEY))
    return data


_REQUIRED = ("title", "starts_on", "ends_on", "registration_closes_at", "responsible")


def _require_fields(data: dict, names) -> None:
    missing = [name for name in names if data.get(name) is None]
    if missing:
        raise ValidationError(
            _("Falten dades obligatòries: %(fields)s.") % {"fields": ", ".join(missing)}
        )


def _reject_unknown(data: dict, allowed) -> None:
    unknown = set(data) - set(allowed)
    if unknown:
        raise ValidationError(
            _("Aquests camps no es canvien aquí: %(fields)s.")
            % {"fields": ", ".join(sorted(unknown))}
        )


@transaction.atomic
def create_course(*, by, catalogue_entry, today=None, request=None, **data) -> Activity:
    """Crea un curs en esborrany a partir d'una fitxa del catàleg. El que no es doni es copia de
    la fitxa: places, preus vigents avui, si és oberta a no socis i departament."""
    permissions.require(by, permissions.MANAGE)
    _reject_unknown(data, EDITABLE_FIELDS[Activity.Kind.COURSE])
    if catalogue_entry is None:
        raise ValidationError(_("Cal triar la fitxa del catàleg."))
    if not catalogue_entry.active:
        raise ValidationError(_("Aquesta fitxa del catàleg està desactivada."))
    today = today or timezone.localdate()
    standard = _standard(catalogue.price_on(catalogue_entry, today))
    data.setdefault("max_places", catalogue_entry.default_places)
    data.setdefault("price_member_cents", standard["standard_price_member_cents"])
    data.setdefault("price_non_member_cents", standard["standard_price_non_member_cents"])
    data.setdefault("open_to_non_members", catalogue_entry.open_to_non_members)
    data.setdefault("department", catalogue_entry.department)
    _require_fields(data, _REQUIRED)
    data = _clean(_defaults(data)) | standard
    _check_dates(data["starts_on"], data["ends_on"], data["registration_closes_at"])
    _check_place(data.get("place"), required=False)
    _check_cost_centre(data.get("cost_centre"), data["department"])
    _require_note(data)
    return _create(
        by=by,
        request=request,
        details=_differs(data),
        kind=Activity.Kind.COURSE,
        catalogue_entry=catalogue_entry,
        **data,
    )


@transaction.atomic
def create_outing(
    *, by, outing_type, subtype=None, project=None, today=None, request=None, **data
) -> Activity:
    """Crea una sortida en esborrany. El subtipus i el projecte, només si el tipus és de medi
    ambient (CA-M02-03). El departament, si no es dona, és el del tipus."""
    permissions.require(by, permissions.MANAGE)
    _reject_unknown(data, _COMMON_FIELDS)
    catalogue.check_outing_classification(outing_type, subtype, project)
    place = data.get("place")
    _check_place(place, required=True)
    standard = _standard(catalogue.place_price_on(place, today or timezone.localdate()))
    data.setdefault("department", outing_type.default_department)
    data.setdefault("price_member_cents", standard["standard_price_member_cents"])
    data.setdefault("price_non_member_cents", standard["standard_price_non_member_cents"])
    _require_fields(data, (*_REQUIRED, "max_places", *PRICE_FIELDS))
    data = _clean(_defaults(data)) | standard
    _check_dates(data["starts_on"], data["ends_on"], data["registration_closes_at"])
    _check_cost_centre(data.get("cost_centre"), data["department"])
    _require_note(data)
    return _create(
        by=by,
        request=request,
        details=_differs(data),
        kind=Activity.Kind.OUTING,
        outing_type=outing_type,
        subtype=subtype,
        project=project,
        **data,
    )


def _logged(name, value):
    return value.pk if name in _FOREIGN_KEYS and value is not None else value


@transaction.atomic
def update_activity(activity, *, by, today=None, request=None, **fields) -> list[str]:
    """Canvia dades d'una activitat que encara no s'ha fet ni cancel·lat. Torna els camps que han
    canviat; el registre en guarda el valor anterior."""
    permissions.require(by, permissions.MANAGE)
    _reject_unknown(fields, EDITABLE_FIELDS[activity.kind])
    locked = Activity.objects.select_for_update().get(pk=activity.pk)
    if not states.is_editable(locked):
        raise ValidationError(
            _("Una activitat «%(status)s» ja no es pot editar.")
            % {"status": locked.get_status_display()}
        )
    for name in ("subtype", "project"):
        value = fields.get(name)
        if value is not None and not isinstance(value, _FOREIGN_KEYS[name]):
            raise ValidationError(_("El subtipus o el projecte no és vàlid."))
    fields = _clean(fields)
    if "place" in fields and fields["place"] != locked.place:
        _check_place(fields["place"], required=locked.kind == Activity.Kind.OUTING)
        if locked.kind == Activity.Kind.OUTING and locked.status == Activity.Status.DRAFT:
            # RN-M02-40: en esborrany, el lloc nou porta el seu preu estàndard.
            on = today or timezone.localdate()
            standard = _standard(catalogue.place_price_on(fields["place"], on))
            fields |= standard
            if standard["standard_price_member_cents"] is not None:
                fields.setdefault("price_member_cents", standard["standard_price_member_cents"])
                fields.setdefault(
                    "price_non_member_cents", standard["standard_price_non_member_cents"]
                )
    merged = {
        name: fields.get(name, getattr(locked, name))
        for name in (*EDITABLE_FIELDS[locked.kind], *STANDARD_FIELDS)
    }
    _check_dates(merged["starts_on"], merged["ends_on"], merged["registration_closes_at"])
    if {"cost_centre", "department"} & set(fields):
        _check_cost_centre(merged["cost_centre"], merged["department"])
    if locked.kind == Activity.Kind.OUTING and {"outing_type", "subtype", "project"} & set(fields):
        catalogue.check_outing_classification(
            merged["outing_type"], merged["subtype"], merged["project"]
        )
    changes = {
        name: (_logged(name, getattr(locked, name)), _logged(name, value))
        for name, value in fields.items()
        if getattr(locked, name) != value
    }
    price_changed = any(name in changes for name in (*PRICE_FIELDS, *STANDARD_FIELDS))
    if price_changed:
        _require_note(merged)
    if not changes:
        return []
    for name in changes:
        setattr(locked, name, fields[name])
        setattr(activity, name, fields[name])
    locked.save(update_fields=[*changes, "updated_at"])
    audit.record_changes(
        ACTIVITY_UPDATED,
        actor=by,
        target=locked,
        changes=changes,
        reason=merged["price_override_note"] if price_changed else "",
        request=request,
    )
    return sorted(changes)
