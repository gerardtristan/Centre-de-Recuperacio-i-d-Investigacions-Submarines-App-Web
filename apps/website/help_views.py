"""Preguntes freqüents a la web (T-M07-09; P-M07-G, RN-M07-01, 10 i 12; CA-M07-16): pública
declarada, per temes, amb el cercador; sense resultats, l'enllaç al contacte si és encès."""

from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from apps.core import business_settings

from . import contact
from . import help as faq


@login_not_required
@require_GET
def help_view(request):
    query = request.GET.get("q", "").strip()[:100]
    entries = faq.search(query) if query else list(faq.published_entries())
    context = {
        "query": query,
        "entries": entries,
        "contact_on": business_settings.get(contact.ENABLED),
    }
    return render(request, "website/help.html", context)
