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
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.permissions import READ_ONLY_SCOPES, has_perm, permission_required, require_perm
from apps.members.models import Member

from . import campaigns, tasks
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


# --- Campanya de mandats (T-M05a-13; C5 de M05a-3; A5; P-M05a-E; wireframe
# `admin.html#vista-pagaments-campanya`). Veure els recomptes demana A4; obrir, enviar i tancar,
# A5 (`payments.campaign.send`), comprovat al servidor. Enviar i tancar es confirmen: el primer
# POST només mostra la confirmació. Les invitacions surten per la cua. Cap nom ni dada bancària.

SEND = "payments.campaign.send"  # A5
CAMPAIGN_ERRORS = {
    campaigns.SigningDisabled: _("La signatura del mandat no està activada: no s'envia res."),
    campaigns.NotReady: _("Falta l'identificador de creditor o el text de la invitació publicat."),
    campaigns.AlreadyOpen: _("Ja hi ha una campanya oberta."),
    campaigns.Closed: _("La campanya ja és tancada."),
}


class OpenCampaignForm(forms.Form):
    name = forms.CharField(label=_("Nom de la campanya"), max_length=120)


def _campaign_action(request, campaign):
    """Torna el pas a confirmar ("send" o "close") o None si l'acció s'ha fet."""
    action = request.POST.get("action")
    if action == "open":
        form = OpenCampaignForm(request.POST)
        if form.is_valid():
            campaigns.open_campaign(form.cleaned_data["name"], by=request.user)
            messages.success(request, _("Campanya oberta. Revisa-la i envia les invitacions."))
        else:
            messages.error(request, _("Escriu el nom de la campanya."))
    elif action in ("send", "close") and campaign is None:
        raise campaigns.Closed
    elif action in ("send", "close") and request.POST.get("confirm") != "1":
        return action
    elif action == "send":
        campaigns.check_can_send(campaign)
        # Dins de la transacció de la petició, com `mail.queue_email`: si falla, no queda cap feina.
        tasks.send_campaign_invitations.defer(campaign_id=campaign.pk, account_id=request.user.pk)
        messages.success(request, _("Les invitacions s'estan enviant per la cua de correu."))
    elif action == "close":
        campaigns.close_campaign(campaign, by=request.user)
        messages.success(request, _("Campanya tancada: no s'enviarà cap recordatori més."))
    return None


@never_cache
@permission_required(VIEW)
@require_http_methods(["GET", "POST"])
def campaign_view(request):
    campaign = campaigns.open_campaign_now()
    can_send = has_perm(request.user, SEND, write=True)
    confirm = None
    if request.method == "POST":
        require_perm(request, SEND, write=True)
        try:
            confirm = _campaign_action(request, campaign)
        except tuple(CAMPAIGN_ERRORS) as error:
            messages.error(request, CAMPAIGN_ERRORS[type(error)])
        if confirm is None:
            return redirect("administration:payments_campaign")
    pending = campaigns.to_invite(campaign)
    without_email = sum(1 for _member, address in pending if not address)
    context = {
        "campaign": campaign,
        "status": campaigns.campaign_status(campaign),
        "answered": campaign is not None
        and campaign.recipients.filter(answered_at__isnull=False).exists(),
        "to_invite": len(pending) - without_email,
        "without_email": without_email,
        "reminder_days": campaigns.REMINDER_DAYS,
        "blocked": campaigns.blocking_reason(),
        "can_send": can_send,
        "confirm": confirm,
        "form": OpenCampaignForm(),
    }
    return render(request, "payments/campaign.html", context)
