"""Formulari públic «Fer-se soci» (T-M01-13; P1; CA-M01-01, CA-M01-02).

- Ruta pública declarada (RN-40), amb CSRF. P1: visitant i participant no soci. Una sessió
  d'administració o la d'un soci (no de baixa) rep «no trobat», com qualsevol cel·la «—».
- Límit per origen i per destinatari del rebut amb el limitador dels enllaços del correu i
  llindars provisionals de la configuració [A validar] (`apps/accounts/limits.py`).
- La resposta és la mateixa tant si el document ja existia com si no, si ja hi havia una
  sol·licitud pendent o si el rebut no s'envia per límit de destinatari.
- POST, 303 i GET (T-M01-38): recarregar la confirmació no torna a enviar res.
"""

from django.contrib.auth.decorators import login_not_required
from django.db import transaction
from django.forms.utils import ErrorDict
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.accounts import limits
from apps.accounts.models import Account
from apps.accounts.security import client_ip
from apps.core import audit
from apps.members import join
from apps.members.forms import JoinForm
from apps.members.models import Member, MemberRequest

SENT_KEY = "members_join_sent_to"
# Vista prèvia (HTMX): en canviar la data de naixement, el servidor torna la part del formulari
# que en depèn (tipus i quota, representant i acceptació). No desa res ni compta per al límit.
PREVIEW = "vista_previa"


def render_preview(request, form):
    # Només recalcula: sense errors, que surten en enviar i no mentre la persona escriu.
    form._errors = ErrorDict()
    return render(request, "members/_join_preview.html", {"form": form})


def _p1(user) -> bool:
    """Visitant o participant no soci (matriu de M01-4)."""
    if not user.is_authenticated:
        return True
    if not isinstance(user, Account) or user.kind != Account.Kind.PERSONAL:
        return False
    members = Member.objects.filter(person_id=user.person_id)
    return not members.exclude(status=Member.Status.LEFT).exists()


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def join_view(request):
    if not _p1(request.user):
        raise Http404
    texts = join.current_texts()
    if texts is None:
        return render(request, "members/join.html", {"unavailable": True}, status=503)
    if request.method == "GET" and SENT_KEY in request.session:
        sent_to = request.session.pop(SENT_KEY)
        return render(request, "members/join.html", {"sent_to": sent_to})

    form = JoinForm(request.POST or None, texts=texts)
    if request.method == "POST" and request.POST.get(PREVIEW):
        return render_preview(request, form)
    if request.method == "POST" and form.is_valid():
        email = join.receipt_address(form.cleaned_data)  # RN-M01-78: el del representant
        with transaction.atomic():
            accepted = limits.start_join(client_ip(request))
            if accepted is None:
                audit.record(audit.Action.JOIN_REQUEST_LIMITED, request=request)
                form.add_error(
                    None, _("S'han enviat massa sol·licituds seguides. Torna-ho a provar més tard.")
                )
                context = {"form": form, "texts": texts}
                return render(request, "members/join.html", context, status=429)
            join.submit(
                form.cleaned_data,
                channel=MemberRequest.Channel.WEB,
                request=request,
                send_receipt=limits.join_receipt_allowed(accepted, email),
            )
        request.session[SENT_KEY] = email
        response = redirect("members:join")
        response.status_code = 303
        return response
    return render(request, "members/join.html", {"form": form, "texts": texts})
