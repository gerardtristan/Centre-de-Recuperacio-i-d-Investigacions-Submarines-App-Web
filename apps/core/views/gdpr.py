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
  frases sense imports ni dades. Un cop executada, només la referència.
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
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
from ..models import ErasureRequest, Person
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
            "Obligatori. Queda al registre d'activitat i s'envia a la persona per correu: "
            "no hi escriguis dades d'altres persones."
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


# --- Exportació amb les notes de l'administració (T-M01-22c; 085, A-1; P-416) ---------------


class NotesExportForm(ReauthForm):
    """Qui atén la sol·licitud revisa cada nota: les marcades queden fora, amb un motiu. Lliurar-les
    no es pot desfer: contrasenya i codi a la mateixa petició."""

    reason = forms.CharField(
        label=gettext_lazy("Motiu per deixar fora les notes marcades"),
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=gettext_lazy(
            "Obligatori si en deixes fora alguna (per exemple, perquè parla d'una altra persona). "
            "Queda al registre d'activitat; no hi escriguis dades d'altres persones."
        ),
    )

    def __init__(self, *args, notes, **kwargs):
        super().__init__(*args, **kwargs)
        self.notes = notes
        # Pel nom de la clau, no per la posició: si entre la pantalla i l'enviament apareix una
        # nota nova, la marca no passa a una altra.
        for item in notes:
            item["field"] = f"exclou:{item['key']}"
            self.fields[item["field"]] = forms.BooleanField(
                label=_("Deixa fora: %(context)s") % {"context": item["context"]}, required=False
            )
        # Les notes que s'han mostrat: si n'apareix una de nova abans d'enviar-ho, cal tornar-les a
        # revisar (cap nota no surt sense que algú l'hagi vista).
        self.fields["reviewed"] = forms.CharField(
            widget=forms.HiddenInput, required=False, initial=",".join(i["key"] for i in notes)
        )
        self.order_fields([*(item["field"] for item in notes), "reason"])

    def clean(self):
        data = super().clean()
        if data.get("reviewed", "") != ",".join(item["key"] for item in self.notes):
            raise forms.ValidationError(_("Les notes han canviat. Torna-les a revisar."))
        return data

    def note_rows(self):
        return [(item, self[item["field"]]) for item in self.notes]

    def excluded(self) -> set:
        return {item["key"] for item in self.notes if self.cleaned_data.get(item["field"])}


@never_cache
@permission_required(erasure.HANDLE_PERMISSION)
@require_http_methods(["GET", "POST"])
def gdpr_notes_export_view(request, pk):
    """M11 per veure-ho, M11 amb edició per preparar-la; sense l'interruptor, «no trobat»."""
    if not privacy.notes_export_enabled():
        raise Http404
    person = get_object_or_404(Person, pk=pk, status=Person.Status.ACTIVE)
    own = person.pk == request.user.person_id
    can_prepare = not own and has_perm(
        request.user,
        erasure.HANDLE_PERMISSION,
        write=True,
        permissions=request_permissions(request),
    )
    notes = privacy.admin_notes(person)
    form = NotesExportForm(request.POST or None, has_totp=request.user.has_totp, notes=notes)
    status = 200
    if request.method == "POST":
        require_perm(request, erasure.HANDLE_PERMISSION, write=True)
        if own:
            form.add_error(None, _("No pots preparar la teva pròpia exportació amb notes."))
            status = 403
        elif form.is_valid():
            if form.excluded() and not form.cleaned_data["reason"].strip():
                form.add_error("reason", _("Cal el motiu per deixar fora alguna nota."))
            else:
                error = reauth.require_recent_auth(
                    request,
                    0,
                    password=form.cleaned_data["password"],
                    code=form.cleaned_data.get("code", ""),
                )
                if error is not None:
                    form.add_error(
                        {WRONG_PASSWORD: "password", WRONG_CODE: "code"}.get(error), error
                    )
                    form.data = form.data.copy()
                    form.data.pop("code", None)
                else:
                    try:
                        privacy.export_with_notes(
                            person,
                            by=request.user,
                            excluded=form.excluded(),
                            reason=form.cleaned_data["reason"],
                            request=request,
                        )
                    except ValidationError as exc:
                        form.add_error(None, exc.messages)
                    else:
                        messages.success(
                            request,
                            _(
                                "Exportació preparada amb les notes revisades. La persona la pot "
                                "descarregar des de «Les meves dades» durant 7 dies."
                            ),
                        )
                        return redirect("administration:gdpr_notes_export", pk=person.pk)
    context = {"person": person, "form": form, "can_prepare": can_prepare, "own": own}
    return render(request, "core/gdpr_notes_export.html", context, status=status)


# --- Sol·licitud d'esborrat feta en persona per un menor de 14 anys (T-M01-22c; 085, A-2) -----


class InPersonForm(forms.Form):
    guardian_checked = forms.BooleanField(
        label=gettext_lazy(
            "He comprovat en persona la identitat del pare, la mare o el tutor legal que ho demana."
        ),
        error_messages={"required": gettext_lazy("Cal comprovar-ho abans de registrar-la.")},
    )


@never_cache
@permission_required(erasure.REGISTER_PERMISSION, write=True)
@require_http_methods(["GET", "POST"])
def gdpr_in_person_view(request, pk):
    """M11b amb edició; la persona ha de ser un menor de 14 anys (el servei ho torna a
    comprovar). Un cop registrada, l'atén qui té M11 a «Sol·licituds RGPD»."""
    person = get_object_or_404(Person, pk=pk, status=Person.Status.ACTIVE)
    form = InPersonForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            erasure.register_in_person(
                person, by=request.user, guardian_checked=True, request=request
            )
        except erasure.ErasureNotAllowed as exc:
            form.add_error(None, exc.messages)
        else:
            messages.success(
                request,
                _(
                    "Sol·licitud d'esborrat registrada. L'atendrà qui té el permís de les "
                    "sol·licituds RGPD."
                ),
            )
            return redirect("administration:gdpr_in_person", pk=person.pk)
    context = {
        "person": person,
        "form": form,
        "possible": erasure.can_register_in_person(person, request.user),
        "pending": erasure.pending_request(person),
    }
    return render(request, "core/gdpr_in_person.html", context)
