"""Pantalles dels ajuts a l'administració. Calendari (T-M09A-05; HU-M09A-03; AJ3): el mes que es
tria (amb el mes anterior i el següent) i, a sota, totes les dates a partir d'avui. Sense AJ3,
«no trobat».

Justificació d'una sol·licitud (T-M09A-10c; P-M09A-F, pas 3; AJ7): els paquets generats, amb els
totals i les excloses; generar-ne un (AJ7 i AJ12), descarregar-lo (vista `private_file`, AJ12) i
enviar-lo (la versió 1 la justifica; les següents, amb un requeriment obert). Els serveis
(`package.py`) tornen a comprovar-ho tot."""

import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.charges import euros
from apps.core.permissions import has_perm, request_permissions, require_perm

from . import package
from .calendar import calendar
from .justification import JUSTIFY
from .models import GrantApplication, GrantRequirement

VIEW = "grants.view"  # AJ3


def _month(value: str, today: datetime.date) -> datetime.date:
    """`AAAA-MM` → el primer dia del mes; qualsevol altra cosa, el mes d'avui."""
    try:
        return datetime.datetime.strptime(value or "", "%Y-%m").date()
    except ValueError:
        return today.replace(day=1)


def _shift(first: datetime.date, months: int) -> datetime.date:
    month = first.month - 1 + months
    return first.replace(year=first.year + month // 12, month=month % 12 + 1)


@never_cache
@require_GET
def calendar_view(request):
    require_perm(request, VIEW)
    today = timezone.localdate()
    first = _month(request.GET.get("mes"), today)
    last = _shift(first, 1) - datetime.timedelta(days=1)
    context = {
        "month": first,
        "previous": _shift(first, -1),
        "next": _shift(first, 1),
        "events": calendar(first, last),
        "upcoming": calendar(today, datetime.date.max),  # totes les dates a partir d'avui
        "can_justify": has_perm(request.user, JUSTIFY),
    }
    return render(request, "grants/calendar.html", context)


def _open_requirement(application, raw):
    if not raw:
        return None
    return get_object_or_404(
        GrantRequirement, pk=raw, application=application, answered_on__isnull=True
    )


def _post_justification(request, application):
    action = request.POST.get("action")
    try:
        requirement = _open_requirement(application, request.POST.get("requeriment"))
        if action == "build":
            package.build_package(application, request.user, requirement=requirement)
            messages.success(request, _("Paquet generat."))
        elif action == "send":
            chosen = get_object_or_404(application.packages, pk=request.POST.get("paquet") or None)
            sent_on = datetime.date.fromisoformat(request.POST.get("enviat", ""))
            done = package.submit_package_version(
                application, chosen, sent_on=sent_on, by=request.user, requirement=requirement
            )
            messages.success(request, _("Versió %(n)s enviada.") % {"n": done.version})
        else:
            raise Http404
    except ValueError:
        messages.error(request, _("Escriu la data d'enviament."))
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))


@never_cache
@require_http_methods(["GET", "POST"])
def justification_view(request, pk):
    perms = request_permissions(request)
    require_perm(request, JUSTIFY)
    application = get_object_or_404(GrantApplication.objects.select_related("call"), pk=pk)
    if request.method == "POST":
        _post_justification(request, application)
        return redirect("administration:grant_justification", application.pk)
    sent = {s.package_id: s for s in application.submissions.all()}
    packages = [
        {
            "package": item,
            "included": euros(item.totals["included_cents"]),
            "submission": sent.get(item.pk),
        }
        for item in application.packages.order_by("-pk")
    ]
    context = {
        "application": application,
        "packages": packages,
        "requirements": application.requirements.filter(answered_on__isnull=True),
        "can_build": has_perm(request.user, JUSTIFY, write=True, permissions=perms)
        and has_perm(request.user, package.OPEN_DOCUMENTS, permissions=perms),
        "can_open": has_perm(request.user, package.OPEN_DOCUMENTS, permissions=perms),
        "today": timezone.localdate(),
    }
    return render(request, "grants/justification.html", context)
