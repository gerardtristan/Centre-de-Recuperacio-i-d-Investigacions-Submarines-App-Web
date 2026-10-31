from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def home(request):
    return render(request, "core/home.html")


@login_not_required
@require_GET
def health(request):
    """Comprovació de salut per al proxy i el monitor. No diu res de l'estat intern."""
    return HttpResponse("ok", content_type="text/plain")


@login_not_required
@require_GET
def login(request):
    # Provisional: l'entrada amb compte personal i d'administrador és la T-M01-05.
    return render(request, "core/login.html")
