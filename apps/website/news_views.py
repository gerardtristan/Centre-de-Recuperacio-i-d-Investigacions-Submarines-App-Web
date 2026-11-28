"""Notícies (T-M07-08; P-M07-B, RN-M07-02, 05, 10 i 14).

- Públiques declarades (RN-M07-01): la llista i el detall de les publicades; un esborrany, una
  retirada o una que no existeix donen el mateix «no trobat». La foto, per la vista pública
  `media_view` (P-489), que la torna a comprovar a cada petició, darrere de
  `website.public_images_enabled` (apagat, D2).
- Les pantalles d'administració (WP2) esperen el torn del nucli (vegeu `docs/estat/M07.md`).
"""

from django.contrib.auth.decorators import login_not_required
from django.http import FileResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.core import business_settings

from . import media, news
from .views import switched_on

# D2 (pla d'acceleració F2-6): apagat, cap foto pública; les notícies es veuen sense.
IMAGES = "website.public_images_enabled"


@login_not_required
@require_GET
def public_list_view(request):
    return render(request, "website/news_list.html", {"items": news.published()})


@login_not_required
@require_GET
def public_detail_view(request, slug):
    context = {"item": news.get_published(slug), "images_on": business_settings.get(IMAGES)}
    return render(request, "website/news_detail.html", context)


@login_not_required
@never_cache
@switched_on(IMAGES)
@require_GET
def media_view(request, key):
    """La foto d'una pàgina o d'una notícia publicades (CA-M07-05; P-489). `?w=480` dona la mida
    en WebP si n'hi ha. Un PDF, sempre com a descàrrega (RN-M07-19)."""
    asset = media.public_asset(str(key))
    width = request.GET.get("w", "")
    if asset.content_type == media.PDF:
        response = FileResponse(
            media.open_content(asset), content_type=media.PDF, as_attachment=True,
            filename="document.pdf",
        )  # fmt: skip
    elif width in asset.renditions:
        response = FileResponse(media.open_content(asset, width), content_type="image/webp")
    else:
        response = FileResponse(media.open_content(asset), content_type=asset.content_type)
    response["X-Content-Type-Options"] = "nosniff"
    return response
