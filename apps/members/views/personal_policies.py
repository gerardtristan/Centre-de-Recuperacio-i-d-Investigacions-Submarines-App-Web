"""«Accepta les polítiques» per als importats de Cluber a la primera entrada (T-M01-25; 079,
A-27 punt 4; CA-M01-109). Les regles són a `apps/members/policies.py`.

Compte personal de la sessió; la ruta no porta cap identificador. Un compte que no ve de
Cluber, o que ja les ha acceptades, només hi veu que no té res pendent. Sense les dues caselles,
no es desa res i la pàgina ho diu al camp.
"""

from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.accounts.sessions import safe_next

from .. import policies


class AcceptPoliciesForm(forms.Form):
    """Una casella obligatòria per a cada text pendent."""

    def __init__(self, data=None, *, pending):
        super().__init__(data)
        for kind, label, _text in pending:
            self.fields[f"accept_{kind}"] = forms.BooleanField(
                label=label,
                required=True,
                error_messages={"required": _("Cal que l'acceptis per continuar.")},
            )


@never_cache
@require_http_methods(["GET", "POST"])
def accept_policies_view(request):
    person = request.user.person
    pending = policies.pending_texts(person) if policies.applies(request.user) else []
    next_url = safe_next(request, request.POST.get("next") or request.GET.get("next"))
    form = AcceptPoliciesForm(request.POST if request.method == "POST" else None, pending=pending)
    if request.method == "POST" and pending and form.is_valid():
        policies.accept(person, [kind for kind, *_ in pending], by=request.user, request=request)
        request.session[policies.SESSION_FLAG] = True
        messages.success(request, _("Gràcies. Ja pots fer servir l'àrea de socis."))
        response = redirect(next_url or "core:home")
        response.status_code = 303
        return response
    rows = [(kind, label, text, form[f"accept_{kind}"]) for kind, label, text in pending]
    context = {"rows": rows, "form": form, "next": next_url or ""}
    return render(request, "members/accept_policies.html", context)
