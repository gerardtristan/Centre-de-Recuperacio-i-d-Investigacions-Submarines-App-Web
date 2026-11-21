"""Administració del 06: llistat de llicències, tramitació i exportació (T-M06-09 i T-M06-10,
vistes v1; LC4, LC5 i C6). Sense permís, «no trobat»: ho comproven els serveis i, abans, el
decorador. Sense wireframe propi: segueix les pantalles de la tresoreria."""

from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.charges import euros
from apps.core.permissions import has_perm, request_permissions, require_perm

from . import filing, listing, prices, types
from .models import Licence, LicencePrice, LicenceType, ValidityRule
from .services import LicenceRequestError

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


# --- Tipus i preus (vistes v2; LC8) -----------------------------------------------------------

PRICES_URL = "administration:licences_prices"


def _euros(label, minimum):
    return forms.DecimalField(
        label=label, min_value=Decimal(minimum), max_digits=9, decimal_places=2, localize=True
    )


class TypeForm(forms.Form):
    nom = forms.CharField(label=gettext_lazy("Nom"), max_length=80)
    categoria = forms.ChoiceField(
        label=gettext_lazy("Categoria"), choices=LicenceType.Category.choices
    )
    durada = forms.ChoiceField(label=gettext_lazy("Durada"), choices=ValidityRule.choices)


class PriceForm(forms.Form):
    tipus = forms.ModelChoiceField(
        label=gettext_lazy("Tipus"),
        queryset=LicenceType.objects.order_by("name"),
        empty_label=gettext_lazy("Tria un tipus"),
    )
    federacio = _euros(gettext_lazy("Preu de la federació (preu de soci), en euros"), "0.01")
    recarrec = _euros(gettext_lazy("Recàrrec de no soci, en euros"), "0")
    des_de = forms.DateField(
        label=gettext_lazy("Per a llicències que comencin des del"),
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    fins_a = forms.DateField(
        label=gettext_lazy("Fins al (opcional, per als trams)"), required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )  # fmt: skip
    nota = forms.CharField(label=gettext_lazy("Nota"), widget=forms.Textarea(attrs={"rows": 2}))


def _type_rows(today):
    rows = []
    for licence_type in LicenceType.objects.order_by("name"):
        price = prices.applicable(licence_type, today)
        rows.append({
            "type": licence_type,
            "member": price and euros(price.amount_cents(LicencePrice.Kind.MEMBER)),
            "non_member": price and euros(price.amount_cents(LicencePrice.Kind.NON_MEMBER)),
        })  # fmt: skip
    return rows


@never_cache
@require_http_methods(["GET", "POST"])
def prices_view(request):
    """GET: tipus, preu vigent avui i historial de versions. POST (només «Sí»): un tipus nou,
    activar-lo o desactivar-lo, o una versió de preu nova (nota obligatòria, avís)."""
    scope = require_perm(request, types.PERMISSION)
    can_edit = scope == "all"
    type_form = TypeForm(request.POST if "nou_tipus" in request.POST else None, prefix="t")
    price_form = PriceForm(request.POST if "nou_preu" in request.POST else None, prefix="p")
    if request.method == "POST":
        if not can_edit:
            raise Http404
        try:
            if "nou_tipus" in request.POST and type_form.is_valid():
                data = type_form.cleaned_data
                types.create_type(name=data["nom"], category=data["categoria"],
                                  validity_rule=data["durada"], actor=request.user)  # fmt: skip
                messages.success(request, _("Tipus de llicència creat."))
                return redirect(PRICES_URL)
            if "actiu" in request.POST:
                licence_type = get_object_or_404(LicenceType, pk=request.POST.get("tipus"))
                types.set_active(licence_type, request.POST["actiu"] == "1", actor=request.user)
                messages.success(request, _("Tipus de llicència actualitzat."))
                return redirect(PRICES_URL)
            if "nou_preu" in request.POST and price_form.is_valid():
                data = price_form.cleaned_data
                prices.add_price(
                    data["tipus"], federation_cost_cents=int(data["federacio"] * 100),
                    non_member_surcharge_cents=int(data["recarrec"] * 100),
                    valid_from=data["des_de"], valid_to=data["fins_a"], note=data["nota"],
                    actor=request.user,
                )  # fmt: skip
                messages.success(
                    request, _("Preu desat. S'ha avisat el tresorer, la junta i la secretaria.")
                )
                return redirect(PRICES_URL)
        except ValidationError as error:
            form = type_form if "nou_tipus" in request.POST else price_form
            form.add_error(None, error.messages)
    context = {
        "rows": _type_rows(timezone.localdate()),
        # shortcut: les 50 versions més recents; si en calen més, paginar-les
        "history": [
            {
                "price": p,
                "cost": euros(p.federation_cost_cents),
                "surcharge": euros(p.non_member_surcharge_cents),
            }
            for p in LicencePrice.objects.select_related("licence_type").order_by("-pk")[:50]
        ],  # fmt: skip
        "can_edit": can_edit,
        "type_form": type_form,
        "price_form": price_form,
    }
    return render(request, "licences/prices.html", context)
