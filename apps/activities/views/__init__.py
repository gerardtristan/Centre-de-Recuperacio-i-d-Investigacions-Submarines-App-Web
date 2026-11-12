"""Vistes del mòdul 02. Cada ruta declara el seu permís a `apps/activities/permissions.py`."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect


def see_other(name, *args):
    """Redirecció després d'un POST (303): tornar enrere no torna a enviar el formulari."""
    response = redirect(name, *args)
    response.status_code = 303
    return response


def run(request, form, action, success):
    """Executa `action()` i en mostra el resultat. Un error de regla de negoci del servei surt al
    formulari, sense desar res. Torna si ha anat bé."""
    try:
        result = action()
    except ValidationError as error:
        form.add_error(None, error)
        return False
    messages.success(request, success(result) if callable(success) else success)
    return True
