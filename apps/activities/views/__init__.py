"""Vistes del mòdul 02. Cada ruta declara el seu permís a `apps/activities/permissions.py`."""

from django.shortcuts import redirect


def see_other(name, *args):
    """Redirecció després d'un POST (303): tornar enrere no torna a enviar el formulari."""
    response = redirect(name, *args)
    response.status_code = 303
    return response
