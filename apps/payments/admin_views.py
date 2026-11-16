"""Pantalles de pagaments de l'administració (05a). «Mètodes i mandats» (T-M05a-14; C6 de
M05a-3; A4 i A9 de M05a-4; RN-M05a-06; wireframe `admin.html#vista-pagaments-mandats`).

- Permís A4 (`payments.mandates.view`) al servidor; sense, «no trobat». Ruta d'administració, amb
  TOTP. Només lectura: només GET, i l'únic formulari és el filtre.
- El servidor tria les columnes per l'abast: amb «Cons.» només surt «té mètode: sí/no» i no es
  consulta cap mandat ni targeta. Amagar columnes a la plantilla no és el control.
- L'IBAN, emmascarat (país i quatre darrers, P-121: «…»). No es desxifra mai: el text xifrat ni
  tan sols es llegeix de la base de dades (A9, 044). Revocar (A6, C8) és d'una altra tasca.
"""

from django import forms
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.core.permissions import READ_ONLY_SCOPES, permission_required, require_perm
from apps.members.models import Member

from .models import FeeMethod, FeePaymentPreference, SepaMandate

VIEW = "payments.mandates.view"  # A4
NO_ANSWER = "none"


class MethodFilterForm(forms.Form):
    metode = forms.ChoiceField(
        label=_("Mètode"),
        required=False,
        choices=[("", _("Tots")), *FeeMethod.choices, (NO_ANSWER, _("Sense resposta"))],
    )


@never_cache
@permission_required(VIEW)
@require_GET
def mandates_view(request):
    full = require_perm(request, VIEW) not in READ_ONLY_SCOPES
    members = (
        Member.objects.filter(status=Member.Status.ACTIVE)
        .select_related("person")
        .order_by("member_number", "pk")
    )
    preferences = {
        p.member_id: p
        for p in FeePaymentPreference.objects.filter(member__in=members).select_related(
            "saved_card"
        )
    }
    form = MethodFilterForm(request.GET or None) if full else None
    chosen = form.cleaned_data["metode"] if form and form.is_valid() else ""
    mandates = {}
    if full:
        mandates = {
            m.member_id: m
            for m in SepaMandate.objects.filter(
                member__in=members, status=SepaMandate.Status.ACTIVE
            )
            .select_related("bank_account")
            .defer("bank_account__iban_ciphertext")
        }
    rows = []
    for member in members:
        preference = preferences.get(member.pk)
        method = preference.method if preference else NO_ANSWER
        if chosen and method != chosen:
            continue
        row = {"member": member, "has_method": preference is not None}
        if full:
            card = preference.saved_card if method == FeeMethod.SAVED_CARD else None
            row.update(preference=preference, mandate=mandates.get(member.pk), card=card)
        rows.append(row)
    context = {"rows": rows, "full": full, "form": form, "total": members.count()}
    return render(request, "payments/mandates.html", context)
