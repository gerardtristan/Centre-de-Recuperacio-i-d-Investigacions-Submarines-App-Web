"""Peça comuna d'ajustos (decisió 055; planning.md, «peça comuna d'ajustos», RN-AJ-01 a 04).

- `get(key, at)`: el valor vigent a la data `at` (RN-AJ-01). Cap mòdul escriu un valor de
  negoci al codi: el llegeix d'aquí.
- `change(key, value, user, note, effective_from)`: comprova al servidor el permís (RN-RP-22:
  `settings.section.<apartat>` amb «Sí», o `settings.edit.<clau>` amb l'apartat amb «Cons.»;
  sense permís, «no trobat», i amb «Cons.» la petició queda al registre), el tipus i el rang,
  la data i la nota dels valors de diners (RN-AJ-03), i crea la versió i l'entrada del
  registre d'activitat dins la mateixa transacció (RN-AJ-02).
- `notify_money_change(...)`: l'avís per correu dels canvis de diners al tresorer i a la junta
  (RN-AJ-04). El fa servir `change` i el criden els catàlegs i les tarifes dels mòduls.

La pantalla és de la T-AJ-02 (`views/business_settings.py`). L'apartat és el `module` de
l'ajust. Les claus les crea cada mòdul amb una migració; els permisos, el catàleg.
"""

import datetime

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from . import audit, mail, permissions
from .models import Role, Setting, SettingVersion
from .permissions import has_perm

ACTION_CHANGED = "settings.changed"
ACTION_DENIED = "settings.change_denied"
EMAIL_TEMPLATE = "avis-canvi-diners"

T = Setting.ValueType


# Regla d'un sol valor que depèn d'un altre mòdul (P-360): la registra el mòdul al seu `ready`.
EXTRA_CHECKS: dict = {}


def register_check(key: str, check) -> None:
    EXTRA_CHECKS[key] = check


def permission_code(key: str) -> str:
    return f"settings.edit.{key}"


def section_code(section: str) -> str:
    return f"settings.section.{section}"


def can_view(user, section: str, *, perms=None) -> bool:
    """RN-RP-22: «Cons.» o «Sí» de l'apartat. Un apartat que no és al catàleg és un error."""
    return has_perm(user, section_code(section), permissions=perms)


def can_edit(user, setting: Setting, *, perms=None) -> bool:
    """RN-RP-22: «Sí» de l'apartat, o `settings.edit.<clau>` amb l'apartat amb «Cons.»
    (RN-RP-03; el motor no dedueix cap permís, per això es demanen tots dos)."""
    if has_perm(user, section_code(setting.module), write=True, permissions=perms):
        return True
    code = permission_code(setting.key)
    return (
        code in permissions.CATALOG
        and can_view(user, setting.module, perms=perms)
        and has_perm(user, code, write=True, permissions=perms)
    )


def _in_range(setting: Setting, number: int) -> bool:
    return (setting.min_value is None or number >= setting.min_value) and (
        setting.max_value is None or number <= setting.max_value
    )


def _range_error(setting: Setting) -> ValidationError:
    if setting.min_value is not None and setting.max_value is not None:
        message = _("El valor ha d'estar entre %(min)s i %(max)s.")
    elif setting.min_value is not None:
        message = _("El valor ha de ser com a mínim %(min)s.")
    else:
        message = _("El valor ha de ser com a màxim %(max)s.")
    return ValidationError(message % {"min": setting.min_value, "max": setting.max_value})


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _day_month_number(value) -> int | None:
    """ "MM-DD" → MMDD, si és un dia real (el 29 de febrer hi val)."""
    if not isinstance(value, str) or len(value) != 5 or value[2] != "-":
        return None
    try:
        datetime.date(2000, int(value[:2]), int(value[3:]))
    except ValueError:
        return None
    return int(value[:2]) * 100 + int(value[3:])


def validate_value(setting: Setting, value) -> None:
    """Tipus i rang (RN-AJ-02). Aixeca `ValidationError` amb un missatge per a la persona."""
    kind = setting.value_type
    if kind in (T.INTEGER, T.CENTS):
        if not _is_int(value):
            raise ValidationError(_("El valor ha de ser un nombre enter."))
        if not _in_range(setting, value):
            raise _range_error(setting)
    elif kind == T.BOOLEAN:
        if not isinstance(value, bool):
            raise ValidationError(_("El valor ha de ser sí o no."))
    elif kind in (T.TEXT, T.URL):
        if not isinstance(value, str):
            raise ValidationError(_("El valor ha de ser un text."))
        if setting.max_length is not None and len(value) > setting.max_length:
            raise ValidationError(
                _("El text pot tenir com a màxim %(max)s caràcters.") % {"max": setting.max_length}
            )
        if kind == T.URL:
            try:
                URLValidator(schemes=["https"])(value)
            except ValidationError:
                raise ValidationError(
                    _("Ha de ser una adreça web que comenci per https://.")
                ) from None
    elif kind == T.CHOICE:
        if value not in setting.choices:
            raise ValidationError(_("El valor no és cap de les opcions permeses."))
    elif kind == T.DAY_MONTH:
        number = _day_month_number(value)
        if number is None:
            raise ValidationError(_("El valor ha de ser un dia i un mes vàlids (MM-DD)."))
        if not _in_range(setting, number):
            raise _range_error(setting)
    elif kind == T.INTEGER_LIST:
        if not isinstance(value, list) or not value or not all(_is_int(v) for v in value):
            raise ValidationError(_("El valor ha de ser una llista d'enters."))
        if not all(_in_range(setting, v) for v in value):
            raise _range_error(setting)
        if len(set(value)) != len(value):
            raise ValidationError(_("La llista no pot tenir valors repetits."))
        # A la llista, `max_length` és el nombre màxim de valors (091, VC-02: d'1 a 10).
        if setting.max_length is not None and len(value) > setting.max_length:
            raise ValidationError(
                _("La llista pot tenir com a màxim %(max)s valors.") % {"max": setting.max_length}
            )
    else:  # pragma: no cover - el tipus és una llista tancada
        raise ValidationError(_("Tipus d'ajust desconegut."))
    if check := EXTRA_CHECKS.get(setting.key):
        check(value)


def _value_at(setting: Setting, at: datetime.date):
    versions = setting.versions.all()
    if setting.effective_dated:
        versions = versions.filter(effective_from__lte=at).order_by(
            "-effective_from", "-changed_at", "-id"
        )
    else:
        versions = versions.order_by("-changed_at", "-id")
    latest = versions.values_list("value", flat=True).first()
    # `values_list` torna None també quan no hi ha cap versió; cap valor desat és null.
    return setting.initial_value if latest is None else latest


def get(key: str, at: datetime.date | None = None):
    """RN-AJ-01: la versió amb la `effective_from` més gran que no passa de `at` (avui, si no
    se'n dona cap); amb la mateixa data, la creada més tard. Sense versions, el valor inicial.
    Un ajust sense data d'entrada en vigor torna l'últim valor desat."""
    return _value_at(Setting.objects.get(key=key), at or timezone.localdate())


def _check_dates_and_note(setting: Setting, note: str, effective_from):
    """RN-AJ-03. Torna la data d'entrada en vigor que es desa (o `None`)."""
    if not setting.effective_dated:
        if effective_from is not None:
            raise ValidationError(_("Aquest valor no té data d'entrada en vigor."))
        return None
    if setting.affects_money:
        if effective_from is None:
            raise ValidationError(_("Cal la data d'entrada en vigor."))
        if not note:
            raise ValidationError(_("Cal una nota que expliqui el canvi."))
    today = timezone.localdate()
    effective_from = effective_from or today
    if effective_from < today:
        raise ValidationError(_("La data d'entrada en vigor no pot ser anterior a avui."))
    return effective_from


def change(key: str, value, user, note: str = "", effective_from=None) -> SettingVersion:
    """RN-AJ-02 i 03. Sense permís o amb una clau que no existeix, «no trobat» (Http404); qui
    veu l'apartat però no pot editar el valor també rep «no trobat», i la petició queda al
    registre (RN-RP-22; fora de la transacció, perquè no es desfaci). Fora de tipus o de rang,
    `ValidationError` i no es desa res. Tornar al valor inicial és un canvi més. El correu dels
    canvis de diners va per la cua: si falla, el canvi es manté."""
    setting = Setting.objects.filter(key=key).first()
    perms = permissions.effective_permissions(user)
    if setting is None or not can_view(user, setting.module, perms=perms):
        raise Http404
    if not can_edit(user, setting, perms=perms):
        deny(user, setting)
    return _save(setting.pk, value, user, note, effective_from)


def deny(user, setting: Setting, request=None):
    """RN-RP-22: una edició de qui només veu l'apartat queda al registre i és «no trobat»."""
    audit.record(ACTION_DENIED, actor=user, target=setting, field=setting.key, request=request)
    raise Http404


@transaction.atomic
def _save(pk, value, user, note, effective_from) -> SettingVersion:
    setting = Setting.objects.select_for_update().get(pk=pk)
    note = (note or "").strip()
    validate_value(setting, value)
    effective_from = _check_dates_and_note(setting, note, effective_from)

    previous = _value_at(setting, effective_from or timezone.localdate())
    version = SettingVersion.objects.create(
        setting=setting,
        value=value,
        effective_from=effective_from,
        changed_by=user,
        previous_value=previous,
        note=note,
    )
    audit.record(
        ACTION_CHANGED,
        actor=user,
        target=setting,
        field=setting.key,
        old=previous,
        new=value,
        reason=note,
        details={"effective_from": effective_from, "version_id": version.pk},
    )
    if setting.affects_money:
        notify_money_change(
            what=setting.key,
            previous=display_value(setting, previous),
            new=display_value(setting, value),
            changed_by=user,
            note=note,
            effective_from=effective_from,
        )
    return version


def display_value(setting: Setting, value) -> str:
    """Valor llegible per al correu i la pantalla."""
    if setting.value_type == T.CENTS and _is_int(value):
        sign = "-" if value < 0 else ""
        euros, cents = divmod(abs(value), 100)
        return f"{sign}{euros},{cents:02d} €"
    if setting.value_type == T.BOOLEAN:
        return _("sí") if value else _("no")
    if setting.value_type == T.DAY_MONTH and _day_month_number(value):
        return f"{int(value[3:])}/{int(value[:2])}"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def money_change_recipients():
    """Comptes que reben l'avís com a tresorer o com a junta: comptes d'administrador actius
    amb el rol Tresorer o Junta i amb correu de notificació. Una adreça rep un sol correu.
    Qui forma la llista de la junta és S-AJ-02 [A validar: junta]."""
    from apps.accounts.models import Account

    accounts = (
        Account.objects.filter(
            kind=Account.Kind.ADMIN,
            status=Account.Status.ACTIVE,
            role_assignments__role__code__in=[Role.Code.TREASURER, Role.Code.BOARD],
            role_assignments__removed_at__isnull=True,
        )
        .exclude(notification_email="")
        .select_related("person")
        .distinct()
        .order_by("pk")
    )
    by_address = {}
    for account in accounts:
        by_address.setdefault(account.notification_email, account)
    return list(by_address.values())


def notify_money_change(
    *, what: str, previous: str, new: str, changed_by, note: str, effective_from
) -> list:
    """RN-AJ-04: un correu al tresorer i a la junta amb el valor, l'anterior, el nou, qui l'ha
    canviat, la nota i la data d'entrada en vigor. Els catàlegs i les tarifes el criden en desar
    una fila que afecta diners, dins la mateixa transacció. És un avís: no demana cap
    aprovació. Torna els correus posats a la cua."""
    context = {
        "what": what,
        "previous": previous,
        "new": new,
        "changed_by": str(changed_by.person),
        "note": note,
        "effective_from": effective_from,
    }
    emails = []
    for account in money_change_recipients():
        email = mail.queue_email(
            EMAIL_TEMPLATE, to=account.notification_email, person=account.person, context=context
        )
        if email is not None:
            emails.append(email)
    return emails
