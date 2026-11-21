"""«La meva llicència» a l'àrea del soci (T-M06-06 i T-M06-08, vistes v3; LC1 i el «Propi» de
LC3; HU-M06-01 i 03). L'objecte surt sempre de la sessió (la persona del compte): cap
identificador d'un altre a la URL. Demanar-la porta a la pantalla de pagament del 05b."""

import datetime

from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core import business_settings
from apps.core.charges import euros
from apps.members.services import is_member

from . import prices, services
from .listing import TO_RENEW_DAYS
from .models import Licence, LicencePrice, LicenceType, ValidityRule


def _types(today):
    found = LicenceType.objects.filter(active=True).order_by("name")
    if not business_settings.get(services.DAY_ENABLED):
        found = found.exclude(validity_rule=ValidityRule.SINGLE_DAY)
    return found


class RequestForm(forms.Form):
    tipus = forms.ModelChoiceField(label=gettext_lazy("Tipus"), queryset=LicenceType.objects.none(),
                                   empty_label=gettext_lazy("Tria un tipus"))  # fmt: skip
    any_vinent = forms.BooleanField(
        label=gettext_lazy("De l'any vinent (comença l'1 de gener)"), required=False
    )

    def __init__(self, *args, types, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipus"].queryset = types


class DeclareForm(forms.Form):
    tipus = forms.ModelChoiceField(label=gettext_lazy("Tipus"), queryset=LicenceType.objects.none(),
                                   empty_label=gettext_lazy("Tria un tipus"))  # fmt: skip
    numero = forms.CharField(label=gettext_lazy("Número de la llicència"), max_length=30)
    venciment = forms.DateField(
        label=gettext_lazy("Caduca el"),
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    def __init__(self, *args, types, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipus"].queryset = types


def _offer(types, person, today):
    """El preu que pagaria, per tipus: el de soci o, si l'opció és activada, el de no soci."""
    if is_member(person, on=today):
        kind = LicencePrice.Kind.MEMBER
    elif business_settings.get(services.NON_MEMBERS_ENABLED):
        kind = LicencePrice.Kind.NON_MEMBER
    else:
        return []
    rows = []
    for licence_type in types:
        price = prices.applicable(licence_type, today)
        if price is not None:
            rows.append({"type": licence_type, "amount": euros(price.amount_cents(kind))})
    return rows


@never_cache
@require_http_methods(["GET", "POST"])
def mine_view(request):
    person, today = request.user.person, timezone.localdate()
    types = _types(today)
    request_form = RequestForm(request.POST if "demana" in request.POST else None, types=types,
                               prefix="d")  # fmt: skip
    declare_form = DeclareForm(request.POST if "declara" in request.POST else None, types=types,
                               prefix="j")  # fmt: skip
    try:
        if "demana" in request.POST and request_form.is_valid():
            data = request_form.cleaned_data
            starts_on = datetime.date(today.year + 1, 1, 1) if data["any_vinent"] else None
            licence = services.request(person, data["tipus"], starts_on, actor=request.user)
            return redirect("payments:charge", licence.charge_id)
        if "declara" in request.POST and declare_form.is_valid():
            data = declare_form.cleaned_data
            services.declare_existing(person, data["tipus"], federation_number=data["numero"],
                                      expires_on=data["venciment"], actor=request.user)  # fmt: skip
            messages.success(request, _("Llicència registrada. No cal tramitar-ne cap."))
            return redirect("licences:mine")
    except services.LicenceRequestError as error:
        (request_form if "demana" in request.POST else declare_form).add_error(None, str(error))
    to_renew_days = business_settings.get(TO_RENEW_DAYS, today)
    licences = [
        {"licence": licence, "status": licence.display_status(today, to_renew_days)}
        for licence in Licence.objects.filter(person=person)
        .select_related("licence_type")
        .order_by("-expires_on", "-pk")
    ]
    context = {
        "licences": licences,
        "offer": _offer(types, person, today),
        "request_form": request_form,
        "declare_form": declare_form,
    }
    return render(request, "licences/mine.html", context)
