"""Administració: consulta de dades bloquejades (T-M00-04; M13 `core.locked_data.view`, protegit;
decisió 028; spec 00, CA-19.3 i RN-91). Peça de la 00 sense wireframe propi: fa servir els
patrons de les sol·licituds RGPD (`design-system.md`, §6.7).

- Sense M13, «no trobat», també abans de comprovar el mètode. M13 és protegit: el tenen el
  tresorer i l'administrador i no s'edita des de la matriu.
- La llista només mostra la referència anònima i la data del bloqueig.
- Les dades només surten a la resposta d'un POST amb un motiu, que queda al registre d'activitat
  amb qui i quan. Un GET no mostra res. Sense memòria cau (`never_cache`): tornar enrere no les
  torna a mostrar sense una consulta nova.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from .. import locked_data
from ..permissions import permission_required


class ConsultForm(forms.Form):
    reason = forms.CharField(
        label=gettext_lazy("Motiu de la consulta"),
        help_text=gettext_lazy(
            "Obligatori. Per a quina obligació legal les consultes (per exemple, una inspecció o "
            "un requeriment de la gestoria). Queda al registre d'activitat amb el teu compte."
        ),
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
        error_messages={"required": gettext_lazy("Escriu el motiu de la consulta.")},
    )


@never_cache
@permission_required(locked_data.PERMISSION)
@require_GET
def locked_data_list_view(request):
    return render(
        request, "core/locked_data_list.html", {"items": locked_data.locked_people()[:200]}
    )


@never_cache
@permission_required(locked_data.PERMISSION)
@require_http_methods(["GET", "POST"])
def locked_data_detail_view(request, pk):
    item = get_object_or_404(locked_data.locked_people(), pk=pk)
    form = ConsultForm(request.POST if request.method == "POST" else None)
    result = None
    if request.method == "POST" and form.is_valid():
        try:
            result = locked_data.consult(
                item, by=request.user, reason=form.cleaned_data["reason"], request=request
            )
        except ValidationError as exc:
            form.add_error("reason", exc)
    return render(
        request,
        "core/locked_data_detail.html",
        {"item": item, "form": form, "result": result},
    )
