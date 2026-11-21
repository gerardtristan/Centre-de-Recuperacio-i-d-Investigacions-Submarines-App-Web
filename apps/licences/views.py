"""Administració del 06: llistat de llicències, tramitació i exportació (T-M06-09 i T-M06-10,
vistes v1; LC4, LC5 i C6). Sense permís, «no trobat»: ho comproven els serveis i, abans, el
decorador. Sense wireframe propi: segueix les pantalles de la tresoreria."""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from apps.core import business_settings
from apps.core.charges import euros
from apps.core.permissions import has_perm, request_permissions, require_perm
from apps.members.services import membership_fees

from . import filing, listing, prices
from .models import Licence, LicenceType
from .services import NON_MEMBERS_ENABLED, LicenceRequestError

LIST_URL = "administration:licences"


class ListFilterForm(forms.Form):
    tipus = forms.ModelChoiceField(
        label=gettext_lazy("Tipus"), required=False, queryset=LicenceType.objects.order_by("name"),
        empty_label=gettext_lazy("Tots"),
    )  # fmt: skip
    estat = forms.ChoiceField(
        label=gettext_lazy("Estat"), required=False,
        choices=[("", gettext_lazy("Tots")), *Licence.Display.choices],
    )  # fmt: skip
    categoria = forms.ChoiceField(
        label=gettext_lazy("Categoria"), required=False,
        choices=[("", gettext_lazy("Totes")), *LicenceType.Category.choices],
    )  # fmt: skip
    venciment = forms.TypedChoiceField(
        label=gettext_lazy("Caduca d'aquí a"), required=False, coerce=int, empty_value=None,
        choices=[("", gettext_lazy("Qualsevol data")), ("60", gettext_lazy("60 dies o menys")),
                 ("30", gettext_lazy("30 dies o menys")), ("7", gettext_lazy("7 dies o menys"))],
    )  # fmt: skip

    def __init__(self, *args, details: bool, **kwargs):
        super().__init__(*args, **kwargs)
        if not details:  # sense C6 no es filtra per categoria ni per venciment (CA-M06-33)
            del self.fields["categoria"], self.fields["venciment"]


class ActivateForm(forms.Form):
    numero = forms.CharField(label=gettext_lazy("Número federatiu"), max_length=30)


@never_cache
@require_http_methods(["GET"])
def list_view(request):
    perms = request_permissions(request)
    require_perm(request, listing.LIST_PERMISSION)
    details = has_perm(request.user, listing.DETAILS_FIELD, permissions=perms)
    form = ListFilterForm(request.GET or None, details=details)
    data = form.cleaned_data if form.is_valid() else {}
    rows = listing.licence_list(
        request.user,
        licence_type=data.get("tipus"),
        status=data.get("estat") or None,
        category=data.get("categoria") or None,
        expiring_within=data.get("venciment"),
    )
    context = {
        "form": form,
        "rows": rows,
        "details": details,
        "can_file": has_perm(request.user, filing.FILE_PERMISSION, write=True, permissions=perms),
        "paid_count": Licence.objects.filter(status=Licence.Status.PAID).count(),
    }
    return render(request, "licences/list.html", context)


@never_cache
@require_POST
def file_view(request, licence_id):
    require_perm(request, filing.FILE_PERMISSION, write=True)
    licence = get_object_or_404(Licence, pk=licence_id)
    try:
        filing.mark_filed(licence, actor=request.user)
    except LicenceRequestError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, _("Llicència marcada com a tramitada."))
    return redirect(LIST_URL)


@never_cache
@require_http_methods(["GET", "POST"])
def activate_view(request, licence_id):
    require_perm(request, filing.FILE_PERMISSION, write=True)
    licence = get_object_or_404(
        Licence.objects.select_related("person", "licence_type"), pk=licence_id
    )
    form = ActivateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            filing.mark_active(licence, form.cleaned_data["numero"], actor=request.user)
        except LicenceRequestError as error:
            form.add_error(None, str(error))
        else:
            messages.success(request, _("Llicència vigent."))
            return redirect(LIST_URL)
    return render(request, "licences/activate.html", {"licence": licence, "form": form})


@never_cache
@require_POST
def export_view(request):
    require_perm(request, filing.FILE_PERMISSION, write=True)
    name, content = filing.export(request.user)
    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{name}"'
    return response


# --- Pàgina pública per a no socis (T-M06-07) ----------------------------------------------------


@login_not_required  # ruta pública declarada (RN-40): cap dada personal, només tipus i preus
@never_cache
@require_http_methods(["GET"])
def public_view(request):
    """CA-M06-06 (RN-M06-03 i 07): «no trobat» si la junta no ha activat l'opció de no socis;
    si l'ha activada, la comparació de preus de cada tipus i la quota anual de soci."""
    if not business_settings.get(NON_MEMBERS_ENABLED):
        raise Http404
    today = timezone.localdate()
    rows = [
        {"name": row.name, "description": row.description, "validity": row.validity,
         "member": euros(row.member_cents), "non_member": euros(row.non_member_cents),
         "saving": euros(row.saving_cents)}
        for row in prices.comparison(today)
    ]  # fmt: skip
    fees = [{"name": name, "amount": euros(cents)} for name, cents in membership_fees(today)]
    return render(request, "licences/public.html", {"rows": rows, "fees": fees})
