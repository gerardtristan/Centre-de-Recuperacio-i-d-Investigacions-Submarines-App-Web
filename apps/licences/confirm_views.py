"""Llicències «pendents de confirmar» a l'administració (T-M06-24; RN-M06-24 i 26; CA-M06-29 i
32; LC5): la llista, la confirmació en bloc de les d'any natural i posar o confirmar la data
d'una. Sense LC5, «no trobat»: ho comprova el decorador i ho tornen a comprovar els serveis."""

from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy, ngettext
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core.permissions import require_perm

from . import imports
from .models import Licence
from .services import LicenceRequestError

URL = "administration:licences_unconfirmed"


class BulkForm(forms.Form):
    llicencies = forms.TypedMultipleChoiceField(coerce=int, required=False)
    any = forms.TypedChoiceField(label=gettext_lazy("Caduquen el 31/12 de"), coerce=int)

    def __init__(self, *args, choices, years, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["llicencies"].choices = choices
        self.fields["any"].choices = [(year, year) for year in years]


class ExpiryForm(forms.Form):
    caducitat = forms.DateField(
        label=gettext_lazy("Caduca el"),
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )


@never_cache
@require_http_methods(["GET", "POST"])
def unconfirmed_view(request):
    require_perm(request, imports.CONFIRM_EXPIRY_PERMISSION, write=True)
    licences = list(imports.unconfirmed(request.user))
    years = imports.allowed_years()
    choices = [(lic.pk, lic.pk) for lic in licences if lic.expires_on is None]
    form = BulkForm(request.POST or None, choices=choices, years=years,
                    initial={"any": years[0]})  # fmt: skip
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            count = imports.confirm_in_bulk(data["llicencies"], data["any"], actor=request.user)
        except LicenceRequestError as error:
            form.add_error(None, str(error))
        else:
            messages.success(request, ngettext(
                "Confirmada %(count)s llicència amb caducitat el 31/12/%(year)s.",
                "Confirmades %(count)s llicències amb caducitat el 31/12/%(year)s.", count,
            ) % {"count": count, "year": data["any"]})  # fmt: skip
            return redirect(URL, permanent=False)
    selected = {str(pk) for pk in form["llicencies"].value() or []}
    context = {"form": form, "licences": licences, "selected": selected}
    return render(request, "licences/unconfirmed.html", context)


@never_cache
@require_http_methods(["GET", "POST"])
def confirm_view(request, licence_id):
    require_perm(request, imports.CONFIRM_EXPIRY_PERMISSION, write=True)
    licence = get_object_or_404(
        Licence.objects.select_related("person", "licence_type"),
        pk=licence_id, status=Licence.Status.ACTIVE, expiry_confirmed=False,
    )  # fmt: skip
    form = ExpiryForm(request.POST or None, initial={"caducitat": licence.expires_on})
    if request.method == "POST" and form.is_valid():
        try:
            imports.confirm_expiry(licence, form.cleaned_data["caducitat"], actor=request.user)
        except LicenceRequestError as error:
            form.add_error(None, str(error))
        else:
            messages.success(request, gettext_lazy("Caducitat confirmada."))
            return redirect(URL)
    context = {"licence": licence, "form": form, "today": timezone.localdate()}
    return render(request, "licences/confirm.html", context)
