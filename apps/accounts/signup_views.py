"""Pantalla «Crea el compte» (T-M01-53; decisió 108, D.1 i D.4). Ruta pública declarada, amb
CSRF. POST, 303 i GET: recarregar la confirmació no torna a enviar res. La confirmació és la
mateixa tant si el correu ja té compte com si no. On tornar (`next`) es valida (`safe_next`, mai
cap a un altre domini) i es guarda a la sessió fins que el correu es confirma."""

from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from . import signup
from .forms import SignupForm
from .sessions import safe_next

SENT_KEY = "signup_sent"
NEXT_KEY = "signup_next"


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def signup_view(request):
    next_url = safe_next(request, request.POST.get("next") or request.GET.get("next"))
    if request.user.is_authenticated:
        return redirect(next_url or reverse("core:home"))
    if request.method == "GET" and request.session.pop(SENT_KEY, False):
        return render(request, "accounts/signup.html", {"sent": True})
    texts = signup.current_texts()
    if texts is None:
        return render(request, "accounts/signup.html", {"unavailable": True}, status=503)
    form = SignupForm(request.POST or None, texts=texts)
    if request.method == "POST" and form.is_valid():
        if not signup.create_account(request, form.cleaned_data, texts):
            form.add_error(
                None, _("S'han fet massa peticions seguides. Torna-ho a provar més tard.")
            )
            context = {"form": form, "texts": texts, "next": next_url}
            return render(request, "accounts/signup.html", context, status=429)
        request.session[SENT_KEY] = True
        if next_url:
            request.session[NEXT_KEY] = next_url
        response = redirect("accounts:signup")
        response.status_code = 303
        return response
    return render(request, "accounts/signup.html", {"form": form, "texts": texts, "next": next_url})
