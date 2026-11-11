"""Enllaços de convidat: pàgina pública del convidat i pantalla d'administració (T-M00-02;
spec 00, HU-02, CA-02.1 a CA-02.8, V-02; decisió 021).

Pàgina del convidat (rutes públiques declarades, RN-40):
- `convidat/<testimoni>/`: l'enllaç del correu. Comprova el testimoni, en desa a la sessió
  l'identificador intern (mai el testimoni) i redirigeix a `convidat/`, sense testimoni a
  l'adreça. La resposta és la mateixa redirecció tant si el testimoni funciona com si no. El
  camí no s'escriu al registre `django.request` (CA-02.8) i no surt cap «Referer».
- `convidat/`: només el càrrec de l'enllaç obert en aquest navegador (concepte, import i estat);
  cap dada personal i cap identificador a l'adreça. Si l'enllaç no funciona, cap dada i l'opció
  de demanar-ne un de nou (CA-02.3). El pagament és del 05b: aquí no n'hi ha cap.
- `convidat/enllac-nou/`: demanar un enllaç nou amb el correu; sempre la mateixa resposta
  (CA-02.6).

Administració (M5, `core.guest_links.manage`): llista, generar o reenviar i revocar. El servei
torna a comprovar el permís.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts.forms import RecoveryRequestForm

from .. import guest_links
from ..charges import euros
from ..permissions import permission_required

PER_PAGE = 50


def _private(response, referrer="same-origin"):
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Referrer-Policy"] = referrer
    return response


def _open(request, token):
    if request.method not in ("GET", "HEAD"):
        return HttpResponseNotAllowed(["GET", "HEAD"])
    if not guest_links.start_session(request, token):
        return render(request, "core/guest.html", {"state": "limited"}, status=429)
    return redirect("core:guest")


@login_not_required
@never_cache
def guest_link_view(request, token):
    response = _open(request, token)
    # Django escriu el camí de les respostes 4xx (amb el testimoni) al registre `django.request`;
    # aquesta marca, la mateixa que fa servir Django per no registrar-les dues vegades, ho evita.
    response._has_been_logged = True
    return _private(response, "no-referrer")


@login_not_required
@never_cache
@require_GET
def guest_view(request):
    link = guest_links.for_request(request)
    if link is None:
        return _private(render(request, "core/guest.html", {"state": "invalid"}))
    context = {
        "state": "open",
        "charge": link.charge,
        "amount": euros(link.charge.amount_cents),
        "can_pay": guest_links.can_pay(link),
        "expires_at": link.expires_at,
    }
    return _private(render(request, "core/guest.html", context))


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def guest_link_request_view(request):
    form = RecoveryRequestForm(request.POST or None)
    sent = request.method == "POST" and form.is_valid()
    if sent:
        guest_links.request_new(request, form.cleaned_data["email"])
    return _private(render(request, "core/guest_link_request.html", {"form": form, "sent": sent}))


# --- Administració (M5) ------------------------------------------------------------------------


@never_cache
@permission_required(guest_links.MANAGE)
@require_GET
def guest_links_admin_view(request):
    page = Paginator(guest_links.manageable_charges(), PER_PAGE).get_page(request.GET.get("pagina"))
    rows = [
        (charge, euros(charge.amount_cents), next(iter(charge.current_links), None))
        for charge in page
    ]
    context = {"page": page, "rows": rows, "days": guest_links.VALIDITY.days}
    return render(request, "core/guest_links_admin.html", context)


def _back(request, level, text):
    messages.add_message(request, level, text)
    response = redirect("administration:guest_links")
    response.status_code = 303
    return response


@never_cache
@permission_required(guest_links.MANAGE)
@require_POST
def guest_link_send_view(request, pk):
    charge = get_object_or_404(guest_links.manageable_charges(), pk=pk)
    try:
        guest_links.create(charge.person, charge, by=request.user, request=request)
    except ValidationError as error:
        return _back(request, messages.ERROR, " ".join(error.messages))
    return _back(request, messages.SUCCESS, _("Enllaç enviat al correu de contacte de la persona."))


@never_cache
@permission_required(guest_links.MANAGE)
@require_POST
def guest_link_revoke_view(request, pk):
    charge = get_object_or_404(guest_links.manageable_charges(), pk=pk)
    link = next(iter(charge.current_links), None)
    if link is None or not guest_links.revoke(link, by=request.user, request=request):
        return _back(request, messages.ERROR, _("Aquest càrrec no té cap enllaç per revocar."))
    return _back(request, messages.SUCCESS, _("Enllaç revocat: ja no funciona."))
