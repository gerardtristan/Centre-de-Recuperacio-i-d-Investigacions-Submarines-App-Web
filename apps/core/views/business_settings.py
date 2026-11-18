"""Administració: pantalla base d'ajustos (T-AJ-02; decisió 055, RN-AJ-05; RN-RP-22).

Una sola pantalla per a tots els apartats: l'apartat és el `module` dels ajustos i ha de tenir
`settings.section.<apartat>` al catàleg. Sense aquest permís, «no trobat», també per a un apartat
o una clau que no existeixen. El formulari només surt a qui pot editar el valor, però no és el
control: el servei rebutja l'edició sense permís amb «no trobat» i la deixa al registre, i hi
comprova el tipus, el rang, la data i la nota.
"""

from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from .. import business_settings as service
from .. import permissions, texts
from ..models import Setting
from ..permissions import request_permissions, require_perm

T = Setting.ValueType
PREFIX = service.section_code("")


def _section_or_404(request, section):
    code = service.section_code(section)
    if code not in permissions.CATALOG:
        raise Http404
    require_perm(request, code)
    return permissions.CATALOG[code].description


def _show(setting, value):
    return service.display_value(setting, value)


def _range(setting):
    def bound(n):  # «dia i mes» guarda el rang com a MMDD
        return f"{n % 100}/{n // 100}" if setting.value_type == T.DAY_MONTH else _show(setting, n)

    low, high = setting.min_value, setting.max_value
    if low is not None and high is not None:
        return _("de %(min)s a %(max)s") % {"min": bound(low), "max": bound(high)}
    if low is not None or high is not None:
        return (
            _("com a mínim %s") % bound(low) if high is None else _("com a màxim %s") % bound(high)
        )
    if setting.max_length:
        return _("fins a %s caràcters") % setting.max_length
    return ", ".join(map(str, setting.choices)) or "—"


def _row(setting, user, perms):
    today = timezone.localdate()
    perm = permissions.CATALOG.get(service.permission_code(setting.key))
    scheduled = setting.effective_dated and (
        setting.versions.filter(effective_from__gt=today)
        .order_by("effective_from", "-changed_at", "-id")
        .first()
    )
    return {
        "setting": setting,
        "label": perm.description if perm else setting.key,
        "current": _show(setting, service.get(setting.key, today)),
        "initial": _show(setting, setting.initial_value),
        "scheduled": scheduled and _show(setting, scheduled.value),
        "scheduled_from": scheduled and scheduled.effective_from,
        "range": _range(setting),
        "editable": service.can_edit(user, setting, perms=perms),
    } | (
        # Textos dels correus (T-M00-08): el text sencer només surt al detall.
        {
            "label": texts.EMAILS[setting.key].label,
            "current": texts.status(setting.key),
            "initial": _("Text per defecte"),
        }
        if setting.module == texts.SECTION
        else {}
    )


def _to_list(text):
    try:
        return [int(part) for part in text.replace(";", ",").split(",") if part.strip()]
    except ValueError:
        raise ValidationError(_("Escriu nombres enters separats per comes.")) from None


class ValueForm(forms.Form):
    """El camp del valor segons el tipus; el rang el comprova el servei."""

    def __init__(self, setting, *args, current=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setting, kind = setting, setting.value_type
        field, initial = forms.CharField(), current
        if kind == T.INTEGER:
            field = forms.IntegerField()
        elif kind == T.CENTS:
            field = forms.DecimalField(decimal_places=2, localize=True, help_text=_("En euros."))
            initial = None if current is None else Decimal(current) / 100
        elif kind == T.BOOLEAN:
            field = forms.TypedChoiceField(
                choices=[("1", _("Sí")), ("0", _("No"))], coerce=lambda v: v == "1"
            )
            initial = "1" if current else "0"
        elif kind == T.CHOICE:
            field = forms.ChoiceField(choices=[(c, c) for c in setting.choices])
        elif kind == T.DAY_MONTH:
            field.help_text = _("Mes i dia, MM-DD (per exemple, 10-01).")
        elif kind == T.INTEGER_LIST:
            field.help_text = _("Nombres enters separats per comes.")
            initial = current and ", ".join(map(str, current))
        elif setting.module == texts.SECTION:  # T-M00-08: el text vigent, per editar-lo
            field = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={"rows": 14}),
                help_text=texts.help_text(setting.key),
            )
            initial = texts.current(setting.key)
        else:  # text i URL
            field = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
        field.label, field.initial = _("Valor nou"), initial
        self.fields["value"] = field
        if setting.effective_dated:
            self.fields["effective_from"] = forms.DateField(
                label=_("En vigor des de"),
                required=False,
                widget=forms.DateInput(attrs={"type": "date"}),
            )
        self.fields["note"] = forms.CharField(
            label=_("Nota"),
            required=False,
            max_length=2000,
            widget=forms.Textarea(attrs={"rows": 2}),
            help_text=_("Obligatòria: explica el canvi. Queda a l'historial.")
            if setting.affects_money
            else _("Opcional. Queda a l'historial."),
        )

    def clean_value(self):
        value = self.cleaned_data["value"]
        if self.setting.value_type == T.CENTS:
            return int(value * 100)
        if self.setting.value_type == T.INTEGER_LIST:
            return _to_list(value)
        if self.setting.module == texts.SECTION:  # el navegador envia els salts com a CR LF
            return value.replace("\r\n", "\n")
        return value


@never_cache
@require_GET
def settings_index_view(request):
    perms = request_permissions(request)
    sections = [
        (code.removeprefix(PREFIX), perm.description)
        for code, perm in permissions.CATALOG.items()
        if code.startswith(PREFIX) and permissions.has_perm(request.user, code, permissions=perms)
    ]
    if not sections:
        raise Http404
    return render(request, "core/settings_index.html", {"sections": sections})


@never_cache
@require_GET
def settings_section_view(request, section):
    title = _section_or_404(request, section)
    perms = request_permissions(request)
    rows = [_row(s, request.user, perms) for s in Setting.objects.filter(module=section)]
    context = {"section": section, "title": title, "rows": rows}
    return render(request, "core/settings_section.html", context)


@never_cache
@require_http_methods(["GET", "POST"])
def setting_detail_view(request, section, key):
    title = _section_or_404(request, section)
    setting = get_object_or_404(Setting, module=section, key=key)
    row = _row(setting, request.user, request_permissions(request))
    if request.method == "POST" and not row["editable"]:
        service.deny(request.user, setting, request)
    data = request.POST if request.method == "POST" else None
    form = ValueForm(setting, data, current=service.get(setting.key))
    is_text, preview = setting.module == texts.SECTION, None
    if form.is_bound and form.is_valid():
        clean = form.cleaned_data
        try:
            if is_text and "preview" in request.POST:  # T-M00-08: no desa res
                service.validate_value(setting, clean["value"])
                preview = texts.preview(key, clean["value"])
            else:
                service.change(
                    key, clean["value"], request.user, clean["note"], clean.get("effective_from")
                )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            if preview is None:
                messages.success(request, _("Valor desat. El canvi queda a l'historial."))
                return redirect("administration:setting_detail", section=section, key=key)
    history = [
        (v, _show(setting, v.previous_value), _show(setting, v.value))
        for v in setting.versions.select_related("changed_by").order_by("-changed_at", "-id")
    ]
    context = {"section": section, "title": title, "row": row, "form": form, "history": history}
    context |= {"is_text": is_text, "preview": preview}
    return render(request, "core/setting_detail.html", context)
