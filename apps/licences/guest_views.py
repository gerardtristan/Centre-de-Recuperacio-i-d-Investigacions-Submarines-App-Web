"""Formulari públic per demanar una llicència sense ser soci (T-M06-07b; P-M06-C, passos 3 i 4;
CA-M06-06). Ruta pública declarada (RN-40), amb CSRF; «no trobat» mentre
`licences.non_members_enabled` és desactivada. POST, 303 i GET: recarregar no torna a enviar res.
La resposta és la mateixa tant si el correu ja era d'algú com si no."""

from django import forms
from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.accounts import limits
from apps.accounts.security import client_ip
from apps.core import business_settings, consents

from . import guests, services
from .models import LicenceType, ValidityRule

SENT_KEY = "licences_guest_sent"
DATE = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class GuestForm(forms.Form):
    tipus = forms.ModelChoiceField(
        label=gettext_lazy("Tipus de llicència"),
        queryset=LicenceType.objects.none(),
        empty_label=gettext_lazy("Tria un tipus"),
    )
    dia = forms.DateField(
        label=gettext_lazy("Dia (només per a la llicència d'un dia)"), required=False, widget=DATE
    )
    first_name = forms.CharField(label=gettext_lazy("Nom"), max_length=100)
    last_name = forms.CharField(label=gettext_lazy("Cognoms"), max_length=150)
    contact_email = forms.EmailField(label=gettext_lazy("Correu electrònic"), max_length=254)
    phone = forms.CharField(label=gettext_lazy("Telèfon (opcional)"), max_length=30, required=False)
    birth_date = forms.DateField(label=gettext_lazy("Data de naixement"), widget=DATE)
    accept_privacy = forms.BooleanField(
        label=gettext_lazy("Política de privacitat"),
        error_messages={"required": gettext_lazy("Cal acceptar la política de privacitat.")},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        types = LicenceType.objects.filter(active=True).order_by("name")
        if not business_settings.get(services.DAY_ENABLED):
            types = types.exclude(validity_rule=ValidityRule.SINGLE_DAY)
            del self.fields["dia"]
        self.fields["tipus"].queryset = types


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def guest_request_view(request):
    if not business_settings.get(services.NON_MEMBERS_ENABLED):
        raise Http404
    text = consents.current_text(guests.PRIVACY)
    if request.method == "GET" and SENT_KEY in request.session:
        sent_to = request.session.pop(SENT_KEY)
        return render(request, "licences/guest_request.html", {"sent_to": sent_to})
    form = GuestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            with transaction.atomic():
                # P-450: el límit propi, no el del «Fer-se soci».
                accepted = limits.start_join(client_ip(request), limits.GUEST_LICENCE)
                if accepted is None:
                    form.add_error(
                        None,
                        _("S'han enviat massa sol·licituds seguides. Torna-ho a provar més tard."),
                    )
                    raise ValidationError("limited")
                guests.request_as_guest(
                    data["tipus"],
                    data,
                    data.get("dia"),
                    request=request,
                    today=timezone.localdate(),
                    send_link=limits.join_receipt_allowed(accepted, data["contact_email"]),
                )
        except (ValidationError, services.LicenceRequestError) as error:
            if not form.non_field_errors():
                form.add_error(
                    None, error.messages[0] if isinstance(error, ValidationError) else str(error)
                )
        else:
            request.session[SENT_KEY] = data["contact_email"]
            response = redirect("licences:guest_request")
            response.status_code = 303
            return response
    return render(request, "licences/guest_request.html", {"form": form, "text": text})
