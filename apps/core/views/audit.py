"""Consulta del registre d'activitat (T-M01-07b; HU-14, CA-14.3, checklist C8).

- M6 (`core.audit.view`) hi veu totes les entrades; P20 (`members.audit.view`), només les de
  dades de socis: accions «members.*» (decisió del responsable, 05/11/2026). Sense cap dels
  dos, «no trobat». L'abast s'aplica a la consulta abans de cap filtre ni pàgina.
- Només lectura: només GET; l'únic formulari és el dels filtres, amb GET.
- Els valors dels camps amb permís de camp (C1, C2) surten emmascarats si el lector no té
  aquell permís; l'adreça IP només la veu qui té M6 (decisions del 05/11/2026).
"""

from datetime import datetime, time, timedelta

from django import forms
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from ..models import AuditEntry
from ..permissions import has_perm, request_permissions

ALL_ENTRIES = "core.audit.view"  # M6
MEMBER_ENTRIES = "members.audit.view"  # P20
MEMBER_ACTION_PREFIX = "members."
PER_PAGE = 50
HIDDEN = _("ocult")

# Camps amb permís de camp: el valor només el veu qui té el permís (C1, C2).
_FIELD_PERMISSIONS = {
    "birth_date": "members.field.birth_date",
    "address": "members.field.identity",
    "id_document_type": "members.field.identity",
    "id_document_number": "members.field.identity",
}


def _field_permission(field: str) -> str | None:
    if field.startswith("consent:"):  # consentiments d'altres (C2)
        return "members.field.identity"
    return _FIELD_PERMISSIONS.get(field)


class AuditFilterForm(forms.Form):
    date_from = forms.DateField(
        label=_("Des del dia"), required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    date_to = forms.DateField(
        label=_("Fins al dia"), required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    account = forms.CharField(
        label=_("Compte"),
        required=False,
        max_length=254,
        help_text=_("Nom d'usuari o correu d'entrada, complet."),
    )
    action = forms.ChoiceField(label=_("Acció"), required=False)
    target_type = forms.ChoiceField(label=_("Tipus d'objecte"), required=False)
    target_id = forms.CharField(
        label=_("Identificador de l'objecte"), required=False, max_length=64
    )

    def __init__(self, data, *, visible):
        super().__init__(data)
        # Només els valors que el lector ja pot veure: un valor manipulat és «opció no vàlida».
        for name in ("action", "target_type"):
            values = visible.exclude(**{name: ""}).order_by(name).values_list(name, flat=True)
            self.fields[name].choices = [("", _("Totes"))] + [(v, v) for v in values.distinct()]

    def clean(self):
        data = super().clean()
        start, end = data.get("date_from"), data.get("date_to")
        if start and end and start > end:
            self.add_error("date_to", _("Ha de ser igual o posterior a «Des del dia»."))
        return data


def _start_of(day):
    # Dies de calendari a l'hora local, calculats aquí i no a la base de dades.
    return timezone.make_aware(datetime.combine(day, time.min))


def _filter(entries, data):
    if data.get("date_from"):
        entries = entries.filter(created_at__gte=_start_of(data["date_from"]))
    if data.get("date_to"):
        entries = entries.filter(created_at__lt=_start_of(data["date_to"] + timedelta(days=1)))
    if data.get("account"):
        entries = entries.filter(actor_account__login__iexact=data["account"].strip())
    if data.get("action"):
        entries = entries.filter(action=data["action"])
    if data.get("target_type"):
        entries = entries.filter(target_type=data["target_type"])
    if data.get("target_id"):
        entries = entries.filter(target_id=data["target_id"].strip())
    return entries


def _row(entry, *, perms, user, show_ip):
    code = _field_permission(entry.field)
    hidden = code is not None and not has_perm(user, code, permissions=perms)
    return {
        "entry": entry,
        "old": HIDDEN if hidden and entry.old_value is not None else entry.old_value,
        "new": HIDDEN if hidden and entry.new_value is not None else entry.new_value,
        "ip": entry.ip_address if show_ip else None,
    }


@never_cache
@require_GET
def audit_log_view(request):
    perms = request_permissions(request)
    user = request.user
    if has_perm(user, ALL_ENTRIES, permissions=perms):
        visible, show_ip = AuditEntry.objects.all(), True
    elif has_perm(user, MEMBER_ENTRIES, permissions=perms):
        visible = AuditEntry.objects.filter(action__startswith=MEMBER_ACTION_PREFIX)
        show_ip = False
    else:
        raise Http404

    form = AuditFilterForm(request.GET or None, visible=visible)
    data = {}
    if form.is_bound:
        form.is_valid()  # els camps vàlids filtren; els no vàlids surten com a error i no filtren
        data = form.cleaned_data
    entries = _filter(visible, data).select_related("actor_account", "actor_person")
    page = Paginator(entries.order_by("-created_at", "-id"), PER_PAGE).get_page(
        request.GET.get("pagina")
    )
    rows = [_row(e, perms=perms, user=user, show_ip=show_ip) for e in page]
    context = {"form": form, "page": page, "rows": rows, "show_ip": show_ip}
    return render(request, "core/audit_log.html", context)
