"""Llistat i detall públics de les activitats (T-M02-08b; RN-M02-24, 25 i 45; CA-M02-05 i 48).

Rutes públiques declarades (`login_not_required`, RN-40): només llegeixen `public.py`, que no
dona cap dada personal ni les notes, el centre habitual, la còpia estàndard o el cost de material.
Una activitat que no és pública és «no trobat». Els enllaços «Inscriu-te» porten a la inscripció
del soci (àrea personal) o a la del convidat, que tornen a comprovar-ho tot.
"""

from django.contrib.auth.decorators import login_not_required
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET

from .. import public
from ..models import Activity

KINDS = (("", _("Totes")), *Activity.Kind.choices)


@login_not_required
@require_GET
def public_list_view(request):
    kind = request.GET.get("classe", "")
    kind = kind if kind in Activity.Kind.values else ""
    context = {"activities": public.public_list(kind=kind), "kind": kind, "kinds": KINDS}
    return render(request, "activities/public_list.html", context)


@login_not_required
@require_GET
def public_detail_view(request, pk):
    try:
        activity = public.get_activity(pk)
    except public.NotFound as error:
        raise Http404 from error
    return render(request, "activities/public_detail.html", {"activity": activity})
