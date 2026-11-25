"""Notícies (T-M07-08; P-M07-B, RN-M07-02, 05, 10 i 14) i preguntes freqüents (T-M07-09).

- Públiques declarades (RN-M07-01): la llista i el detall de les publicades; un esborrany, una
  retirada o una que no existeix donen el mateix «no trobat». La foto, per la vista pública
  `media_view` (P-489), que la torna a comprovar a cada petició.
- Les pantalles d'administració (WP2) esperen el torn del nucli (vegeu `docs/estat/M07.md`).
"""

from django.contrib.auth.decorators import login_not_required
from django.http import FileResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.core import business_settings

from . import contact, media, news
from . import help as faq


@login_not_required
@require_GET
def public_list_view(request):
    return render(request, "website/news_list.html", {"items": news.published()})


@login_not_required
@require_GET
def public_detail_view(request, slug):
    return render(request, "website/news_detail.html", {"item": news.get_published(slug)})


@login_not_required
@never_cache
@require_GET
def media_view(request, key):
    """La foto d'una pàgina o d'una notícia publicades (CA-M07-05; P-489)."""
    asset = media.public_asset(str(key))
    response = FileResponse(media.open_content(asset), content_type=asset.content_type)
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_not_required
@require_GET
def help_view(request):
    """Preguntes freqüents (T-M07-09; RN-M07-12, CA-M07-16): per temes, amb el cercador; sense
    resultats, l'enllaç al contacte si és encès."""
    query = request.GET.get("q", "").strip()[:100]
    entries = faq.search(query) if query else list(faq.published_entries())
    context = {
        "query": query,
        "entries": entries,
        "contact_on": business_settings.get(contact.ENABLED),
    }
    return render(request, "website/help.html", context)
