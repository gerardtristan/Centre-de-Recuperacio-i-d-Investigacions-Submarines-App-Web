"""Llistat i detall públics de les activitats (T-M02-08; AC1; CA-M02-05; RN-M02-24).

Rutes públiques declarades (`@login_not_required`): qualsevol visitant les pot obrir. Només
mostren el que dona `apps.activities.public`, que no porta cap dada personal. Un esborrany, una
activitat cancel·lada o una d'acabada responen «no trobat», igual que una que no existeix.
"""

from django.contrib.auth.decorators import login_not_required
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET

from .. import public
from ..models import Activity

KINDS = (("", _("Totes")), ("course", _("Cursos")), ("outing", _("Sortides")))


@login_not_required
@require_GET
def activities_view(request):
    kind = request.GET.get("classe", "")
    if kind not in Activity.Kind.values:
        kind = ""
    context = {"activities": public.public_list(kind=kind), "kind": kind, "kinds": KINDS}
    return render(request, "activities/public_list.html", context)


@login_not_required
@require_GET
def activity_view(request, pk):
    try:
        activity = public.get_activity(pk)
    except public.NotFound:
        raise Http404 from None
    return render(request, "activities/public_detail.html", {"activity": activity})
