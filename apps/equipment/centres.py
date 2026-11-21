"""Centres de busseig i tarifes en qualsevol moment (T-M03-05 i T-M03-25; RN-M03-06 i 26;
CA-M03-05 i 25). Cap altra app escriu aquests models.

El permís és MT8 («Centres i tarifes», `equipment.centres.manage`), que entra al catàleg del
nucli amb la T-M03-18. Fins llavors no és al catàleg i aquests serveis no deixen fer res a ningú
(«no trobat»): la postura conservadora, sense cap vista que els cridi."""

import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit, business_settings
from apps.core.charges import euros
from apps.core.permission_catalog import CATALOG
from apps.core.permissions import has_perm

from .models import CentreRate, DiveCentre

CENTRES = "equipment.centres.manage"  # MT8 (T-M03-18)
CENTRE_CREATED = "equipment.centre_created"
CENTRE_CHANGED = "equipment.centre_changed"
RATE_CREATED = "equipment.rate_created"
RATE_RETIRED = "equipment.rate_retired"
CENTRE_FIELDS = ("name", "address", "contact_email", "contact_phone")


def allowed(by) -> bool:
    return CENTRES in CATALOG and has_perm(by, CENTRES, write=True)


def _require(by) -> None:
    if not allowed(by):
        raise Http404


def _clean_centre(fields: dict) -> dict:
    unknown = set(fields) - set(CENTRE_FIELDS)
    if unknown:
        raise TypeError(f"Camps desconeguts: {sorted(unknown)}")
    clean = {name: (value or "").strip() for name, value in fields.items()}
    if "name" in clean and (not clean["name"] or len(clean["name"]) > 120):
        raise ValidationError(_("Cal el nom del centre (120 caràcters com a màxim)."))
    return clean


@transaction.atomic
def create_centre(*, by, **fields) -> DiveCentre:
    _require(by)
    centre = DiveCentre(**_clean_centre(fields))
    centre.full_clean()
    centre.save()
    audit.record(CENTRE_CREATED, actor=by, target=centre, details={"name": centre.name})
    return centre


@transaction.atomic
def update_centre(centre, *, by, active=None, **fields) -> DiveCentre:
    """Edita les dades del centre o el desactiva (RN-M03-26 a): un centre no s'esborra mai, i un
    de desactivat no surt en assignacions noves; les antigues el conserven."""
    _require(by)
    centre = DiveCentre.objects.select_for_update().get(pk=centre.pk)
    changes = _clean_centre(fields)
    if active is not None:
        changes["active"] = bool(active)
    before = {name: getattr(centre, name) for name in changes}
    for name, value in changes.items():
        setattr(centre, name, value)
    centre.full_clean()
    centre.save()
    audit.record_changes(
        CENTRE_CHANGED,
        actor=by,
        target=centre,
        changes={name: (before[name], getattr(centre, name)) for name in changes},
    )
    return centre


def _cents(value, *, optional=False):
    if optional and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(_("Els imports són enters de cèntims, zero o més."))
    return value


def _check_version(valid_from, note, today) -> str:
    """RN-M03-26 c: una versió té data no anterior a avui i nota obligatòria."""
    note = (note or "").strip()
    if not isinstance(valid_from, datetime.date) or valid_from < today:
        raise ValidationError(_("La data d'entrada en vigor no pot ser anterior a avui."))
    if not note:
        raise ValidationError(_("Un canvi de tarifa porta una nota."))
    return note


def _show(rate) -> str:
    return f"{euros(rate.cost_cents)} / {euros(rate.member_price_cents)}"


@transaction.atomic
def add_rate(
    centre,
    *,
    label,
    cost_cents,
    member_price_cents,
    valid_from,
    note,
    by,
    equipment_type=None,
    non_member_price_cents=None,
    replaces=None,
    today=None,
) -> CentreRate:
    """Una línia nova o, amb `replaces`, la versió nova d'una línia (RN-M03-06, CA-M03-05): la
    vella no es toca i les assignacions que la fan servir conserven els imports. Va al registre i
    avisa el tresorer i la junta (RN-AJ-04)."""
    _require(by)
    today = today or timezone.localdate()
    note = _check_version(valid_from, note, today)
    centre = DiveCentre.objects.get(pk=centre.pk)
    if not centre.active:
        raise ValidationError(_("El centre està desactivat."))
    label = (label or "").strip()
    if not label or len(label) > 80:
        raise ValidationError(_("Cal l'equip o el servei (80 caràcters com a màxim)."))
    if replaces is not None:
        replaces = CentreRate.objects.select_for_update().get(pk=replaces.pk)
        if replaces.centre_id != centre.pk or replaces.superseded_by_id or replaces.retired_on:
            raise ValidationError(
                _("Només es canvia la versió vigent d'una línia d'aquest centre.")
            )
    rate = CentreRate.objects.create(
        centre=centre,
        label=label,
        equipment_type=equipment_type,
        cost_cents=_cents(cost_cents),
        member_price_cents=_cents(member_price_cents),
        non_member_price_cents=_cents(non_member_price_cents, optional=True),
        valid_from=valid_from,
        note=note,
        created_by=by,
    )
    if replaces is not None:
        replaces.superseded_by = rate
        replaces.save(update_fields=["superseded_by"])
    audit.record(
        RATE_CREATED,
        actor=by,
        target=rate,
        reason=note,
        details={"replaces": replaces.pk if replaces else None, "valid_from": str(valid_from)},
    )
    business_settings.notify_money_change(
        what=f"{centre.name}: {label}",
        previous=_show(replaces) if replaces else "—",
        new=_show(rate),
        changed_by=by,
        note=note,
        effective_from=valid_from,
    )
    return rate


@transaction.atomic
def retire_rate(rate, *, retired_on, note, by, today=None) -> CentreRate:
    """RN-M03-26 b: retira la línia vigent des d'una data, sense cap versió nova."""
    _require(by)
    note = _check_version(retired_on, note, today or timezone.localdate())
    rate = CentreRate.objects.select_for_update().get(pk=rate.pk)
    if rate.superseded_by_id or rate.retired_on:
        raise ValidationError(_("Només es retira la versió vigent d'una línia."))
    if retired_on < rate.valid_from:
        raise ValidationError(_("No es pot retirar abans que comenci."))
    rate.retired_on = retired_on
    rate.save(update_fields=["retired_on"])
    audit.record(RATE_RETIRED, actor=by, target=rate, reason=note, details={"on": str(retired_on)})
    return rate


def rate_on(centre, equipment_type, on) -> CentreRate | None:
    """La tarifa vigent d'un tipus de material en un centre actiu en una data (RN-M03-06): la
    versió amb la data d'inici més recent que no passa de `on`, si no és retirada aquell dia."""
    if not centre.active:
        return None
    rate = (
        CentreRate.objects.filter(centre=centre, equipment_type=equipment_type, valid_from__lte=on)
        .order_by("-valid_from", "-pk")
        .first()
    )
    if rate is None or (rate.retired_on is not None and rate.retired_on <= on):
        return None
    return rate
