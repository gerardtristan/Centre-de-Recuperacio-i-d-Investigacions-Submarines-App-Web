"""Pantalles «En construcció» (T-DX-03; design-system §6.9; pla dels recursos externs §1).

Una pantalla d'un mòdul que encara no s'ha fet es pot mostrar amb el seu disseny i contingut
d'exemple, inventat i fix, perquè es vegi la interfície sencera. És només visual, i ho garanteix el
servidor, no la plantilla:

- la vista només accepta GET (cap ruta que escrigui: un POST, PUT, PATCH o DELETE torna 405);
- no llegeix ni escriu cap model (contingut d'exemple a la plantilla o a una constant);
- només es veu amb SHOW_UNDER_CONSTRUCTION encès (local i entorn de proves) o, a producció, amb un
  compte d'administrador que tingui el permís core.under_construction.view (P-90, resposta C). Sense
  accés, «no trobat» (404), com qualsevol ruta que no existeix.

Quan la tasca d'aquella pantalla s'acaba, la vista deixa de portar el decorador, l'etiqueta se'n va
i les proves de la tasca substitueixen la de només lectura.
"""

from functools import wraps

from django.conf import settings
from django.http import Http404
from django.views.decorators.http import require_GET

from .permissions import has_perm, request_permissions

PERMISSION = "core.under_construction.view"


def can_see(request) -> bool:
    if settings.SHOW_UNDER_CONSTRUCTION:
        return True
    # Només els comptes d'administrador tenen permisos: un soci o la web pública mai no hi arriben.
    return has_perm(request.user, PERMISSION, permissions=request_permissions(request))


def under_construction(view):
    """Decorador de les vistes «En construcció»: només GET i només si es poden veure."""

    @require_GET
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not can_see(request):
            raise Http404
        return view(request, *args, **kwargs)

    wrapped.under_construction = True
    return wrapped
