"""Crear i editar activitats (T-M02-03; P-M02-B, passos 1 i 3; M02-6; RN-M02-05 i RN-M02-06;
CA-M02-01 a CA-M02-03 i CA-M02-26, la part de les dades).

- **Curs** (`create_course`): surt d'una fitxa activa del catàleg (de cursos o d'especialitats).
  Copia les places, si és oberta a no socis, el departament i el **preu vigent el dia que es crea**
  (RN-M02-05). Un canvi posterior del catàleg no toca mai l'activitat (CA-M02-01).
- **Sortida** (`create_outing`): amb un tipus i, només si és de medi ambient, subtipus i projecte
  (CA-M02-03, `catalogue.check_outing_classification`). Els preus els escriu el responsable.
- **Preu diferent del catàleg** (RN-M02-06, CA-M02-02): sense el motiu es rebutja; amb el motiu, es
  desa i el registre guarda el preu del catàleg i el de l'activitat.
- **Permís:** AC7 amb edició (`activities.manage`); sense, «no trobat».
- Una activitat neix en esborrany (`draft`). L'estat només el canvia `apps.activities.states`.

**Concrecions d'implementació** (dins de les regles; al diari de la T-M02-03)

- Una fitxa desactivada no es pot triar per a un curs nou, com un tipus o un subtipus desactivat.
- La data límit d'inscripció no pot passar del dia d'inici (M02-6, «≤ inici»).
- En editar, el motiu del preu només es demana si en aquell canvi el preu passa a ser diferent del
  que el catàleg té avui: el preu copiat en crear-la no demana motiu encara que el catàleg canviï.
- Els valors per defecte del termini de pagament (72 hores, VC-21) i del mode de requisits (avís,
  VC-24) es llegeixen de la peça d'ajustos si la clau ja hi és declarada (T-M02-28); si no, val el
  valor inicial del pla.

- **Avís del preu diferent** (RN-M02-06; segona part de CA-M02-02): quan un curs es desa amb un
  preu diferent del catàleg, `_notify_price_override` posa a la cua un correu per a cada compte que
  fa les devolucions de les activitats (AC18 amb edició: el tresorer, a la configuració inicial),
  dins la mateixa transacció. La llista surt de la matriu vigent, com a RN-M01-89. El correu no
  porta cap dada personal més que el nom de qui ho ha desat.

**Fora d'aquesta peça:** el centre de cost (04), l'**avís a l'app** del preu diferent (la safata
d'avisos de la 00, `notices.post`, encara no existeix), els avisos als inscrits quan canvia el
programa (T-M02-21), no baixar les places per sota de les ocupades (L-M02-03, T-M02-12), duplicar
(T-M02-07) i els camps de l'addenda de la 058 (T-M02-29 i T-M02-32). Les pantalles són a
`apps/activities/views/admin_activities.py` (T-M02-06).
"""

import datetime

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, business_settings, mail
from apps.core.charges import euros
from apps.core.models import Department, Person, Setting
from apps.core.permissions import accounts_with_perm

from . import catalogue, permissions, states
from .models import Activity, EnvironmentalProject, EnvironmentalSubtype, OutingType

ACTIVITY_CREATED = "activities.activity.created"
ACTIVITY_UPDATED = "activities.activity.updated"
PRICE_NOTICE_TEMPLATE = "avis-preu-activitat"
PRICE_NOTICE_SENT = "activities.activity.price_notice_sent"

# Valors inicials del pla (M02-6, «Valors configurables») mentre la clau no sigui a la peça
# d'ajustos; quan la T-M02-28 les declari, `_setting` llegirà el valor vigent.
PAYMENT_WINDOW_KEY = "activities.default_payment_window_hours"  # VC-21
REQUIREMENTS_MODE_KEY = "activities.default_requirements_mode"  # VC-24
_INITIAL_SETTINGS = {
    PAYMENT_WINDOW_KEY: 72,
    REQUIREMENTS_MODE_KEY: Activity.RequirementsMode.WARN.value,
}

PRICE_FIELDS = ("price_member_cents", "price_non_member_cents")
_TEXT_FIELDS = ("title", "description", "location", "meeting_point", "required_level")
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
}
_MAX_LENGTH = {name: Activity._meta.get_field(name).max_length for name in _TEXT_FIELDS}
_https = URLValidator(schemes=["https"])


def _setting(key):
    try:
        return business_settings.get(key)
    except Setting.DoesNotExist:
        return _INITIAL_SETTINGS[key]


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
            limit = _MAX_LENGTH[name]  # la descripció no en té
            if limit is not None and len(out[name]) > limit:
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
    if "requirements_mode" in out and out["requirements_mode"] not in (
        Activity.RequirementsMode.values
    ):
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


def _check_dates(starts_on, ends_on, registration_closes_at) -> None:
    if ends_on < starts_on:
        raise ValidationError(_("La data de final no pot ser anterior a la d'inici."))
    if timezone.localdate(registration_closes_at) > starts_on:
        raise ValidationError(_("La data límit d'inscripció no pot passar del dia d'inici."))


def _differs(prices: dict, reference) -> bool:
    return (prices["price_member_cents"], prices["price_non_member_cents"]) != (
        reference.member_cents,
        reference.non_member_cents,
    )


def _prices_line(member_cents, non_member_cents) -> str:
    return _("soci %(member)s; no soci %(non_member)s") % {
        "member": euros(member_cents),
        "non_member": euros(non_member_cents),
    }


def _notify_price_override(activity, *, by, catalogue_price) -> int:
    """RN-M02-06: avisa per correu qui fa les devolucions de les activitats (el tresorer) que
    l'activitat té un preu diferent del catàleg. Una adreça rep un sol correu. Torna quants n'ha
    posat a la cua; queda al registre d'activitat."""
    context = {
        "title": activity.title,
        "starts_on": activity.starts_on,
        "catalogue_prices": _prices_line(
            catalogue_price.member_cents, catalogue_price.non_member_cents
        ),
        "activity_prices": _prices_line(
            activity.price_member_cents, activity.price_non_member_cents
        ),
        "changed_by": str(by.person),
        "note": activity.price_override_note,
    }
    sent = set()
    for account in accounts_with_perm(permissions.REFUND_EXECUTE, write=True):
        address = account.notification_email
        if not address or address in sent:
            continue
        if mail.queue_email(
            PRICE_NOTICE_TEMPLATE, to=address, person=account.person, context=context
        ):
            sent.add(address)
    audit.record(
        PRICE_NOTICE_SENT,
        actor=audit.system("activities.notify_price_override"),
        target=activity,
        details={"recipients": len(sent)},
    )
    return len(sent)


def _create(*, by, request, details, **fields) -> Activity:
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
            **details,
        },
        request=request,
    )
    return activity


def _defaults(data: dict) -> dict:
    data.setdefault("payment_window_hours", _setting(PAYMENT_WINDOW_KEY))
    data.setdefault("requirements_mode", _setting(REQUIREMENTS_MODE_KEY))
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
    current = catalogue.price_on(catalogue_entry, today)
    data.setdefault("max_places", catalogue_entry.default_places)
    data.setdefault("price_member_cents", current.member_cents)
    data.setdefault("price_non_member_cents", current.non_member_cents)
    data.setdefault("open_to_non_members", catalogue_entry.open_to_non_members)
    data.setdefault("department", catalogue_entry.department)
    _require_fields(data, _REQUIRED)
    data = _clean(_defaults(data))
    _check_dates(data["starts_on"], data["ends_on"], data["registration_closes_at"])
    differs = _differs(data, current)
    if differs and not data.get("price_override_note"):
        raise ValidationError(_("El preu és diferent del del catàleg: cal escriure'n el motiu."))
    details = {}
    if differs:
        details = {
            "catalogue_price_member_cents": current.member_cents,
            "catalogue_price_non_member_cents": current.non_member_cents,
        }
    activity = _create(
        by=by,
        request=request,
        details=details,
        kind=Activity.Kind.COURSE,
        catalogue_entry=catalogue_entry,
        **data,
    )
    if differs:
        _notify_price_override(activity, by=by, catalogue_price=current)
    return activity


@transaction.atomic
def create_outing(
    *, by, outing_type, subtype=None, project=None, today=None, request=None, **data
) -> Activity:
    """Crea una sortida en esborrany. El subtipus i el projecte, només si el tipus és de medi
    ambient (CA-M02-03). El departament, si no es dona, és el del tipus."""
    permissions.require(by, permissions.MANAGE)
    _reject_unknown(data, _COMMON_FIELDS)
    catalogue.check_outing_classification(outing_type, subtype, project)
    data.setdefault("department", outing_type.default_department)
    _require_fields(data, (*_REQUIRED, "max_places", *PRICE_FIELDS))
    data = _clean(_defaults(data))
    _check_dates(data["starts_on"], data["ends_on"], data["registration_closes_at"])
    return _create(
        by=by,
        request=request,
        details={},
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
    merged = {
        name: fields.get(name, getattr(locked, name)) for name in EDITABLE_FIELDS[locked.kind]
    }
    _check_dates(merged["starts_on"], merged["ends_on"], merged["registration_closes_at"])
    if locked.kind == Activity.Kind.OUTING and {"outing_type", "subtype", "project"} & set(fields):
        catalogue.check_outing_classification(
            merged["outing_type"], merged["subtype"], merged["project"]
        )
    changes = {
        name: (_logged(name, getattr(locked, name)), _logged(name, value))
        for name, value in fields.items()
        if getattr(locked, name) != value
    }
    price_changed = any(name in changes for name in PRICE_FIELDS)
    notify = None
    if price_changed and locked.kind == Activity.Kind.COURSE:
        current = catalogue.price_on(locked.catalogue_entry, today or timezone.localdate())
        if _differs(merged, current):
            if not merged["price_override_note"]:
                raise ValidationError(
                    _("El preu és diferent del del catàleg: cal escriure'n el motiu.")
                )
            notify = current
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
    if notify is not None:
        _notify_price_override(locked, by=by, catalogue_price=notify)
    return sorted(changes)
