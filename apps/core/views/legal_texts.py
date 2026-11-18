"""Administració: publicar versions dels textos legals (T-M00-08b; M12, spec 00 HU-17, CA-17.2).

Tot amb M12; sense, «no trobat». Publicar és en dos passos: la revisió mostra el text com el
veurà la persona i porta l'empremta del text revisat; només es publica si el text que arriba és
el mateix que s'ha revisat. Cada publicació és una versió nova (no es modifica mai cap
anterior), en català (P-49), vigent des que es publica. El servei torna a comprovar el permís.
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from .. import consents
from ..models import LegalText
from ..permissions import has_perm, permission_required


class LegalTextForm(forms.Form):
    content = forms.CharField(
        label=gettext_lazy("Text de la versió nova"),
        widget=forms.Textarea(attrs={"rows": 16}),
        help_text=gettext_lazy("Text pla, sense HTML. Les línies en blanc separen paràgrafs."),
    )
    note = forms.CharField(
        label=gettext_lazy("Nota"),
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text=gettext_lazy("Per què es publica. Queda a l'historial i al registre."),
    )

    def clean_content(self):
        content = consents.normalise(self.cleaned_data["content"])
        consents.validate_content(content)
        return content


@never_cache
@require_GET
@permission_required(consents.PUBLISH_PERMISSION)
def legal_texts_view(request):
    rows = [(kind, label, consents.current_text(kind)) for kind, label in consents.KINDS.items()]
    return render(request, "core/legal_texts.html", {"rows": rows})


@never_cache
@require_http_methods(["GET", "POST"])
@permission_required(consents.PUBLISH_PERMISSION)
def legal_text_detail_view(request, kind):
    label = consents.KINDS.get(kind)
    if label is None:  # també els tipus que només porta una importació (071, punt 15)
        raise Http404
    # «Cons.» de M12 veu i revisa; publicar demana «Sí» (el servei ho torna a comprovar).
    can_publish = has_perm(request.user, consents.PUBLISH_PERMISSION, write=True)
    if "publish" in request.POST and not can_publish:
        raise Http404
    current = consents.current_text(kind)
    initial = {"content": current.content if current else ""}
    form = LegalTextForm(request.POST or None, initial=initial)
    review = None
    if form.is_bound and form.is_valid():
        content, note = form.cleaned_data["content"], form.cleaned_data["note"]
        fingerprint = consents.digest(content, note)
        if "publish" in request.POST and request.POST.get("reviewed", "") == fingerprint:
            try:
                text = consents.publish_text(kind, content, by=request.user, note=note)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                done = _("Versió %(n)s publicada: és la vigent des d'ara.")
                messages.success(request, done % {"n": text.version})
                return redirect("administration:legal_text_detail", kind=kind)
        else:
            # Amb «publish», el text o la nota han canviat després de la revisió: cal revisar-los.
            review = {
                "content": content,
                "digest": fingerprint,
                "changed": "publish" in request.POST,
            }
    context = {
        "kind": kind,
        "label": label,
        "current": current,
        "form": form,
        "review": review,
        "can_publish": can_publish,
        "next_version": consents.next_version(kind),
        # Totes les versions del tipus, de qualsevol llengua: cap salt de numeració amagat.
        "versions": LegalText.objects.filter(kind=kind)
        .select_related("published_by")
        .order_by("-version", "language"),
    }
    return render(request, "core/legal_text_detail.html", context)
