"""Pantalla de remeses de l'administració (C5 de M05b-3; B3 de M05b-4; P-M05b-E, passos 1 a 5).

- Permís B3 (`payments.remittances`) al servidor, a totes les rutes; sense, «no trobat». Rutes
  d'administració, amb TOTP. Confirmar, reenviar avisos i descarregar demanen el permís amb
  edició i són POST amb CSRF.
- Confirmar es fa en dos passos: el primer POST mostra la previsualització i el segon la crea
  (`remittances.build_remittance`, que envia l'avís previ).
- Marcar-la enviada demana la casella «He esborrat el fitxer del dispositiu» (044). Casar
  l'abonament (T-M05b-11b; CA-T16.1): el tresorer escriu la comissió, tria una de les línies
  candidates (`remittances.candidate_lines`, tornades a comprovar al servidor) i ho confirma en
  un segon pas; liquidar també demana T4, que comprova la 04.
- L'IBAN dels deutors, sempre emmascarat a la pantalla (P-121) i sense desxifrar. Només el
  fitxer pain.008 el porta: es genera a cada descàrrega i no es desa (RN-M05b-12).
"""

from datetime import date
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.charges import RETURNS
from apps.core.permissions import has_perm, permission_required, require_perm
from apps.treasury.settlements import SettlementRejected

from . import remittances, sepa_xml
from .models import DirectDebitRemittance
from .providers.base import LiveChargesNotAllowed

MANAGE = "payments.remittances"  # B3
RECONCILE = "treasury.reconcile"  # T4: casar l'abonament és conciliar (M04-4)


class RemittanceForm(forms.Form):
    period = forms.CharField(
        label=gettext_lazy("Període"),
        max_length=20,
        help_text=gettext_lazy("Una etiqueta per trobar-la, per exemple «2026-12» (P-230)."),
    )
    collection_date = forms.DateField(
        label=gettext_lazy("Data de cobrament"),
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )


def _too_late(earliest: date) -> str:
    return _("La data de cobrament ha de ser el %(date)s o més tard (avís previ).") % {
        "date": earliest.strftime("%d/%m/%Y")
    }


def _create(request, form):
    """Torna la remesa creada, o None amb el missatge d'error."""
    data = form.cleaned_data
    try:
        return remittances.build_remittance(data["period"], data["collection_date"], request.user)
    except LiveChargesNotAllowed:
        messages.error(request, _("Amb el nivell 1 no es pot generar cap remesa."))
    except remittances.PrenotificationTooLate:
        messages.error(request, _too_late(remittances.earliest_collection_date()))
    except remittances.EmptyRemittance:
        messages.error(request, _("No hi ha cap quota per cobrar en aquesta data."))
    return None


@never_cache
@permission_required(MANAGE)
@require_http_methods(["GET", "POST"])
def remittances_view(request):
    earliest = remittances.earliest_collection_date()
    preview = None
    if request.method == "POST":
        require_perm(request, MANAGE, write=True)
        form = RemittanceForm(request.POST)
        if form.is_valid() and form.cleaned_data["collection_date"] < earliest:
            form.add_error("collection_date", _too_late(earliest))
        # Només es confirma la data previsualitzada: si l'han canviada, es torna a previsualitzar.
        previewed = form.is_valid() and request.POST.get("previewed") == str(
            form.cleaned_data["collection_date"]
        )
        if previewed and request.POST.get("confirm") == "1":
            remittance = _create(request, form)
            if remittance is not None:
                messages.success(request, _("Remesa creada. Els avisos previs surten per la cua."))
                return redirect("administration:payments_remittance", remittance.pk)
        elif form.is_valid():
            preview = remittances.preview(form.cleaned_data["collection_date"])
    else:
        form = RemittanceForm(initial={"collection_date": earliest})
    context = {
        "form": form,
        "preview": preview,
        "remittances": DirectDebitRemittance.objects.order_by("-collection_date", "-pk"),
        "can_manage": has_perm(request.user, MANAGE, write=True),
        "exhausted": remittances.EXHAUSTED,  # CA-M05b-32: la proposta d'alternativa
        "can_see_returns": has_perm(request.user, RETURNS),
    }
    return render(request, "payments/remittances.html", context)


@never_cache
@permission_required(MANAGE)
@require_http_methods(["GET"])
def remittance_view(request, remittance_id):
    remittance = get_object_or_404(DirectDebitRemittance, pk=remittance_id)
    return _detail(request, remittance, SettleForm(request.GET or None))


def _items(remittance):
    return (
        remittance.items.select_related("attempt__charge", "mandate__member__person")
        .select_related("mandate__bank_account")
        .defer("mandate__bank_account__iban_ciphertext")
        .order_by("mandate__member__member_number", "pk")
    )


class SentForm(forms.Form):
    file_deleted = forms.BooleanField(label=gettext_lazy("He esborrat el fitxer del dispositiu"))


class SettleForm(forms.Form):
    fee = forms.DecimalField(
        label=gettext_lazy("Comissió del banc (€)"),
        required=False,
        min_value=Decimal("0"),
        max_digits=9,
        decimal_places=2,
        localize=True,  # «2,60»: la coma del català, també en tornar-la a enviar
        help_text=gettext_lazy(
            "La que el banc descompta de l'abonament; 0 si no en descompta cap."
        ),
    )

    def fee_cents(self) -> int:
        return int((self.cleaned_data.get("fee") or 0) * 100)


def _detail(request, remittance, settle_form, confirm_line=None):
    items = _items(remittance)
    can_manage = has_perm(request.user, MANAGE, write=True)
    can_settle = can_manage and has_perm(request.user, RECONCILE, write=True)
    searching = can_settle and settle_form.is_bound and settle_form.is_valid()
    context = {
        "remittance": remittance,
        "items": items,
        "without_notice": sum(1 for item in items if item.prenotified_at is None),
        "can_manage": can_manage,
        "can_settle": can_settle,
        "sent_form": SentForm(),
        "settle_form": settle_form,
        "net_cents": remittance.total_cents - (settle_form.fee_cents() if searching else 0),
        "candidates": (
            remittances.candidate_lines(remittance, settle_form.fee_cents()) if searching else None
        ),
        "confirm_line": confirm_line,
    }
    return render(request, "payments/remittance.html", context)


@never_cache
@permission_required(MANAGE, write=True)
@require_POST
def remittance_sent_view(request, remittance_id):
    remittance = get_object_or_404(DirectDebitRemittance, pk=remittance_id)
    form = SentForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Cal confirmar que has esborrat el fitxer del dispositiu."))
    else:
        try:
            remittances.mark_remittance_sent(remittance, file_deleted=True, by=request.user)
        except remittances.WrongStatus:
            messages.error(request, _("Només es marca enviada una remesa avisada amb el fitxer."))
        else:
            messages.success(request, _("Remesa marcada com a enviada al banc."))
    return redirect("administration:payments_remittance", remittance.pk)


@never_cache
@permission_required(MANAGE, write=True)
@require_POST
def remittance_settle_view(request, remittance_id):
    require_perm(request, RECONCILE, write=True)
    remittance = get_object_or_404(DirectDebitRemittance, pk=remittance_id)
    form = SettleForm(request.POST)
    fee = form.fee_cents() if form.is_valid() else 0
    # La línia ha de ser una de les candidates ara mateix, no qualsevol id que arribi.
    line = remittances.candidate_lines(remittance, fee).filter(pk=request.POST.get("line")).first()
    if not form.is_valid() or line is None:
        messages.error(request, _("Aquesta línia ja no es pot casar amb la remesa."))
        return redirect("administration:payments_remittance", remittance.pk)
    if request.POST.get("confirm") != "1":
        return _detail(request, remittance, form, confirm_line=line)
    try:
        remittances.settle_remittance(remittance, line, fees_cents=fee, by=request.user)
    except (remittances.WrongStatus, SettlementRejected, LiveChargesNotAllowed):
        messages.error(request, _("No s'ha pogut casar l'abonament: no ha canviat res."))
    else:
        messages.success(request, _("Abonament casat: les quotes de la remesa són pagades."))
    return redirect("administration:payments_remittance", remittance.pk)


@never_cache
@permission_required(MANAGE, write=True)
@require_POST
def remittance_notices_view(request, remittance_id):
    remittance = get_object_or_404(DirectDebitRemittance, pk=remittance_id)
    pending = remittances.send_prenotifications(remittance)
    if pending:
        messages.error(request, _("Hi ha deutors sense adreça: cal avisar-los per una altra via."))
    else:
        messages.success(request, _("Tots els deutors tenen l'avís previ."))
    return redirect("administration:payments_remittance", remittance.pk)


FILE_ERRORS = {
    LiveChargesNotAllowed: gettext_lazy("Amb el nivell 1 no es genera cap fitxer."),
    sepa_xml.RemittanceNotReady: gettext_lazy("Només una remesa avisada té fitxer."),
    sepa_xml.NotConfigured: gettext_lazy("Falta l'identificador de creditor o el compte del club."),
    sepa_xml.InvalidFile: gettext_lazy("El fitxer no ha passat la validació: no es descarrega."),
}


@never_cache
@permission_required(MANAGE, write=True)
@require_POST
def remittance_file_view(request, remittance_id):
    remittance = get_object_or_404(DirectDebitRemittance, pk=remittance_id)
    try:
        content = sepa_xml.remittance_file(remittance, request.user)
    except sepa_xml.MandateNoLongerActive as error:
        references = ", ".join(error.args[0])
        messages.error(request, _("Hi ha mandats que ja no són actius: %s.") % references)
    except tuple(FILE_ERRORS) as error:
        messages.error(request, FILE_ERRORS[type(error)])
    else:
        response = HttpResponse(content, content_type="application/xml")
        name = f"remesa-{remittance.pk:06d}-{sepa_xml.FILE_FORMAT}.xml"
        response["Content-Disposition"] = f'attachment; filename="{name}"'
        return response
    return redirect("administration:payments_remittance", remittance.pk)
