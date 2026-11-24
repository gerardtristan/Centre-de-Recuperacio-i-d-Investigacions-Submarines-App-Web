"""Vistes públiques del 07 (RN-M07-01: declarades amb `login_not_required`, amb CSRF).

Contacte (T-M07-11; P-M07-D, CA-M07-11): «no trobat» mentre `website.contact_enabled` és apagat
(P-486). POST, 303 i GET: la resposta és sempre la mateixa, també per a un robot o un origen
limitat, que no desen res.
"""

from django import forms
from django.contrib.auth.decorators import login_not_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.accounts.security import client_ip
from apps.core import business_settings, consents

from . import contact
from .models import ContactReason

SENT_KEY = "website_contact_sent"
PRIVACY = "privacy"


class ContactForm(forms.Form):
    reason = forms.ModelChoiceField(
        label=gettext_lazy("Motiu"),
        queryset=ContactReason.objects.filter(active=True),
        empty_label=gettext_lazy("Tria un motiu"),
    )
    name = forms.CharField(label=gettext_lazy("Nom"), max_length=150)
    email = forms.EmailField(label=gettext_lazy("Correu electrònic"), max_length=254)
    body = forms.CharField(label=gettext_lazy("Missatge"), max_length=5000, widget=forms.Textarea)
    accept_privacy = forms.BooleanField(
        label=gettext_lazy("Política de privacitat"),
        error_messages={"required": gettext_lazy("Cal acceptar la política de privacitat.")},
    )


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def contact_view(request):
    if not business_settings.get(contact.ENABLED):
        raise Http404
    text = consents.current_text(PRIVACY)
    context = {"text": text, "club_contact": business_settings.get("website.club_contact")}
    if request.method == "GET" and request.session.pop(SENT_KEY, False):
        return render(request, "website/contact.html", {**context, "sent": True})
    form = ContactForm(request.POST or None)
    if request.method == "POST" and text is not None and form.is_valid():
        robot = contact.looks_like_a_robot(
            request.POST.get("web", ""), request.POST.get("started", "")
        )
        if not robot:
            contact.submit(form.cleaned_data, ip=client_ip(request), privacy_text=text)
        request.session[SENT_KEY] = True
        response = redirect("website:contact")
        response.status_code = 303
        return response
    context.update(form=form, started=contact.started_token())
    return render(request, "website/contact.html", context)
