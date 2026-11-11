"""Administració: sol·licituds d'esborrat RGPD (T-M01-22; P-M01-F, pas 4; HU-19 de la spec 00;
M11, `core.gdpr.handle`). Peça de la 00: sense wireframe propi, fa servir els patrons de les
sol·licituds de socis (`design-system.md`, §6.7).

- Consultar: M11 amb qualsevol abast. Aprovar o rebutjar: M11 amb edició; el servei ho torna a
  comprovar (`erasure`). Sense permís, «no trobat», també abans de comprovar el mètode.
- Ningú no resol la seva pròpia sol·licitud (conflicte d'interès): 403, sense demanar cap
  credencial, i l'intent queda al registre.
- Aprovar és irreversible: casella de confirmació i reautenticació a la mateixa petició
  (`reauth.require_recent_auth` amb `minutes=0`: contrasenya i codi TOTP). Un error compta per al
  bloqueig de V-01 i no diu quants intents queden.
- Minimització: de la persona només es mostra el nom i el compte que ho demana; del que passarà,
  frases sense imports ni dades. Un cop executada, només la referència anònima.
"""

from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.accounts import reauth
from apps.accounts.forms import ReauthForm
from apps.accounts.security import WRONG_CODE, WRONG_PASSWORD

from .. import erasure, privacy
from ..models import ErasureRequest
from ..permissions import has_perm, permission_required, request_permissions, require_perm

APPROVE, REJECT = "approve", "reject"
RESOLVED_SHOWN = 50
S = ErasureRequest.Status


class ApproveForm(ReauthForm):
    field_order = ["confirm"]

    confirm = forms.BooleanField(
        label=gettext_lazy(
            "Entenc que l'esborrat s'executa ara, que afecta totes les dades d'aquesta persona i "
            "que no es pot desfer."
        ),
        error_messages={"required": gettext_lazy("Marca la casella per confirmar que ho entens.")},
    )


class RejectForm(forms.Form):
    reason = forms.CharField(
        label=gettext_lazy("Motiu del rebuig"),
        help_text=gettext_lazy(
            "Obligatori. Queda al registre d'activitat; el correu a la persona no el porta."
        ),
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


def _requests():
    return ErasureRequest.objects.select_related("person", "requested_by", "resolved_by")


@never_cache
@permission_required(erasure.HANDLE_PERMISSION)
@require_GET
def gdpr_requests_view(request):
    context = {
        "pending": _requests().filter(status=S.PENDING).order_by("created_at", "id"),
        "resolved": _requests()
        .exclude(status=S.PENDING)
        .order_by("-resolved_at", "-id")[:RESOLVED_SHOWN],
    }
    return render(request, "core/gdpr_requests.html", context)


def _approve(request, item, form) -> bool:
    """Reautentica i executa. Torna si s'ha fet; si no, l'error ja és al formulari."""
    found = erasure.blockers(item.person)
    if found:
        form.add_error(None, found)
        return False
    error = reauth.require_recent_auth(
        request, 0, password=form.cleaned_data["password"], code=form.cleaned_data.get("code", "")
    )
    if error is not None:
        # L'error al costat del camp que falla; el de massa intents, a tot el formulari.
        form.add_error({WRONG_PASSWORD: "password", WRONG_CODE: "code"}.get(error), error)
        form.data = form.data.copy()
        form.data.pop("code", None)
        return False
    erasure.approve(item, by=request.user, request=request)
    return True


@never_cache
@permission_required(erasure.HANDLE_PERMISSION)
@require_http_methods(["GET", "POST"])
def gdpr_request_detail_view(request, pk):
    item = get_object_or_404(_requests(), pk=pk)
    can_resolve = has_perm(
        request.user,
        erasure.HANDLE_PERMISSION,
        write=True,
        permissions=request_permissions(request),
    )
    own = item.person_id == request.user.person_id
    action = request.POST.get("action") if request.method == "POST" else None
    approve_form = ApproveForm(
        request.POST if action == APPROVE else None, has_totp=request.user.has_totp
    )
    reject_form = RejectForm(request.POST if action == REJECT else None)
    status = 200
    if request.method == "POST":
        require_perm(request, erasure.HANDLE_PERMISSION, write=True)
        if action not in (APPROVE, REJECT):
            raise Http404
        form = approve_form if action == APPROVE else reject_form
        try:
            # Abans de validar res ni de demanar cap credencial: conflicte d'interès.
            erasure.ensure_can_resolve(item, request.user, request=request)
            if form.is_valid():
                if action == REJECT:
                    erasure.reject(
                        item, by=request.user, reason=form.cleaned_data["reason"], request=request
                    )
                    messages.success(request, _("Sol·licitud rebutjada."))
                    return redirect("administration:gdpr_request_detail", pk=item.pk)
                if _approve(request, item, form):
                    item.person.refresh_from_db()
                    messages.success(
                        request,
                        _(
                            "Esborrat executat. La persona ha quedat anonimitzada amb la "
                            "referència %(ref)s."
                        )
                        % {"ref": item.person.anonymous_ref},
                    )
                    return redirect("administration:gdpr_request_detail", pk=item.pk)
        except erasure.OwnErasureRequest as exc:
            form.add_error(None, str(exc))
            status = 403
        except erasure.ErasureNotAllowed as exc:
            form.add_error(None, exc.messages)
    pending = item.status == S.PENDING
    blockers = erasure.blockers(item.person) if pending else []
    context = {
        "item": item,
        "pending": pending,
        "own": own,
        "can_resolve": can_resolve and not own,
        "approve_form": approve_form,
        "reject_form": reject_form,
        "blockers": blockers,
        # Frases sense dades personals: què farà cada mòdul.
        "consequences": privacy.describe(item.person) if pending else [],
    }
    return render(request, "core/gdpr_request_detail.html", context, status=status)
