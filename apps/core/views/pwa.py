"""Service worker de la web instal·lable (T-M01-21; decisió 041).

Es serveix des de l'arrel perquè el seu abast sigui tot el lloc (un fitxer de /static/ només
podria controlar /static/). És públic: la pàgina d'entrada també el registra i el fitxer no
porta cap dada. Què guarda al navegador i quan ho esborra: `static/js/service-worker.js`.
"""

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

SOURCE = settings.BASE_DIR / "static" / "js" / "service-worker.js"


@login_not_required
@require_GET
def service_worker(request):
    response = HttpResponse(SOURCE.read_bytes(), content_type="text/javascript; charset=utf-8")
    # Sempre es torna a comprovar: una versió nova (per exemple, una regla de privacitat
    # corregida) arriba a tots els dispositius a la primera visita amb connexió.
    response["Cache-Control"] = "no-cache"
    return response


@login_not_required
@require_GET
def install_help_iphone(request):
    """Com s'instal·la la web a l'iPhone (decisió 041: a l'iPhone només des de Safari, sense
    botiga). Pública i només de text: no llegeix ni mostra cap dada de la sessió."""
    return render(request, "core/install_help_iphone.html")
