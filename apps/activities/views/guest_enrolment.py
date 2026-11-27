"""«Inscriu-te sense ser soci» des del web (T-M02-54; decisió 108, C.1; abans T-M02-14 i T-M02-34).

Apuntar-se com a no soci demana la sessió del compte personal: aquesta adreça ja no mostra cap
formulari. Sense sessió porta a l'entrada amb `next` cap a aquesta mateixa adreça (l'entrada el
valida amb `safe_next`: mai cap a fora); amb sessió, a la inscripció de l'àrea personal
(`member_enrol`), que fa servir el preu de no soci i comprova que l'activitat és oberta a no socis.
Es queda declarada pública (`login_not_required`) perquè no torna cap dada: només redirigeix, i
una activitat que no és pública és «no trobat», com abans.

No canvien: l'enllaç segur del convidat per pagar i gestionar la inscripció (021, a la 00) ni la
inscripció presencial des de la fitxa (T-M02-14, `admin_activities`).
"""

from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .. import public


@login_not_required
@never_cache
@require_GET
def guest_enrol_view(request, pk):
    try:
        public.get_activity(pk)
    except public.NotFound as error:
        raise Http404 from error
    if not request.user.is_authenticated:
        # shortcut: l'entrada actual; quan hi hagi el compte ràpid (T-M01-53), la seva pantalla.
        return redirect_to_login(reverse("activities:guest_enrol", args=[pk]), "accounts:login")
    return redirect("activities:member_enrol", pk)
