"""Vistes públiques del 07 (RN-M07-01: declarades amb `login_not_required`, amb CSRF).

Contacte (T-M07-11; P-M07-D, CA-M07-11): «no trobat» mentre `website.contact_enabled` és apagat
(P-486). POST, 303 i GET: la resposta és sempre la mateixa, també per a un robot o un origen
limitat, que no desen res.

Butlletí (T-M07-13; P-M07-E, CA-M07-06, 07, 09 i 10): «no trobat» mentre
`website.newsletter_enabled` és apagat (P-42). Subscriure's respon igual per a tothom (RN-M07-08);
confirmar i donar-se de baixa funcionen sense sessió amb l'enllaç del correu.
"""

from functools import wraps

from django import forms
from django.contrib.auth.decorators import login_not_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.accounts import limits
from apps.accounts.security import client_ip
from apps.core import business_settings, consents

from . import contact, newsletter
from .models import ContactReason

SENT_KEY = "website_contact_sent"
SUBSCRIBED_KEY = "website_newsletter_sent"
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


def switched_on(key):
    """«No trobat» amb l'interruptor apagat, abans de mirar el mètode (revisió de la #580)."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not business_settings.get(key):
                raise Http404
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


@login_not_required
@never_cache
@switched_on(contact.ENABLED)
@require_http_methods(["GET", "POST"])
def contact_view(request):
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
    context.update(form=form, started=contact.keep_started(request.POST.get("started", "")))
    return render(request, "website/contact.html", context)


class NewsletterForm(forms.Form):
    email = forms.EmailField(label=gettext_lazy("Correu electrònic"), max_length=254)
    accept_newsletter = forms.BooleanField(
        label=gettext_lazy("Butlletí del club"),
        error_messages={"required": gettext_lazy("Cal acceptar el text del butlletí.")},
    )


def _newsletter_on():
    if not business_settings.get(newsletter.ENABLED):
        raise Http404


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def newsletter_view(request):
    _newsletter_on()
    text = consents.current_text(newsletter.TEXT_KIND)
    if request.method == "GET" and request.session.pop(SUBSCRIBED_KEY, False):
        return render(request, "website/newsletter.html", {"text": text, "sent": True})
    form = NewsletterForm(request.POST or None)
    if request.method == "POST" and text is not None and form.is_valid():
        with transaction.atomic():
            # shortcut: el límit per origen del «Fer-se soci», com el contacte (T-M07-11).
            if limits.start_join(client_ip(request)) is not None:
                newsletter.subscribe(form.cleaned_data["email"], legal_text=text)
        request.session[SUBSCRIBED_KEY] = True
        response = redirect("website:newsletter")
        response.status_code = 303
        return response
    return render(request, "website/newsletter.html", {"text": text, "form": form})


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def newsletter_confirm_view(request, token):
    """Confirmar demana prémer el botó (POST): un programa que obre els enllaços del correu
    per revisar-los no subscriu ningú."""
    _newsletter_on()
    if request.method == "GET":
        return render(request, "website/newsletter_link.html", {"ask": True})
    confirmed = newsletter.confirm(token) is not None
    return render(request, "website/newsletter_link.html", {"confirmed": confirmed})


@login_not_required
@never_cache
@require_http_methods(["GET"])
def newsletter_unsubscribe_view(request, token):
    _newsletter_on()
    newsletter.unsubscribe(token)
    return render(request, "website/newsletter_link.html", {"unsubscribed": True})
