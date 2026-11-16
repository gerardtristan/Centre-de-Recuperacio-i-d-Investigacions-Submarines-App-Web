"""Vistes de les pantalles «En construcció»: només GET, sense cap model, i només si es poden veure
(decorador `under_construction`: SHOW_UNDER_CONSTRUCTION o el permís P-90; si no, 404)."""

from django.shortcuts import render

from apps.core.under_construction import under_construction

from .screens import discover


def screen_view(name, module):
    @under_construction
    def view(request):
        context = {"screen_title": module.TITLE, **getattr(module, "CONTEXT", {})}
        return render(request, f"previews/{name}.html", context)

    return view


@under_construction
def index(request):
    screens = [(name, module.TITLE) for name, module in discover()]
    return render(request, "previews/index.html", {"screens": screens})
