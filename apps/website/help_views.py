"""Preguntes freqüents a la web (T-M07-09; P-M07-G, RN-M07-01, 10 i 12; CA-M07-16): pública
declarada, per temes, amb el cercador; sense resultats, l'enllaç al contacte si és encès."""

from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from apps.core import business_settings

from . import contact
from . import help as faq
from .news_views import IMAGES


@login_not_required
@require_GET
def help_view(request):
    query = request.GET.get("q", "").strip()[:100]
    entries = faq.search(query) if query else list(faq.published_entries())
    context = {
        "query": query,
        "entries": entries,
        "contact_on": business_settings.get(contact.ENABLED),
        "tutorials": [] if query else list(faq.published_tutorials()),
    }
    return render(request, "website/help.html", context)


@login_not_required
@require_GET
def tutorial_view(request, slug):
    """Un tutorial publicat (T-M07-10; RN-M07-11): els passos i, amb les fotos públiques
    enceses (D2), la foto."""
    context = {
        "tutorial": faq.get_published_tutorial(slug),
        "images_on": business_settings.get(IMAGES),
    }
    return render(request, "website/tutorial.html", context)
