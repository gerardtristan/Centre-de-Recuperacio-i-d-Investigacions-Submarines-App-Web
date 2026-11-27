"""Versions d'una pàgina a l'administració (T-M07-22, decisió 106; RN-M07-16, 17 i 25; CA-M07-26 i
33): comparar dues versions o una amb l'esborrany, programar o anul·lar una publicació o una
retirada, i retirar o recuperar la pàgina. Tot demana WP1 (fa de WP1b fins a la T-M07-26) i els
serveis ho tornen a comprovar."""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from apps.core.permissions import require_perm

from . import editor, pages, schedule
from .models import Page, ScheduledAction

VERSIONS = "administration:website_page_versions"
DRAFT = "esborrany"


class ScheduleForm(forms.Form):
    action = forms.ChoiceField(label=gettext_lazy("Acció"), choices=ScheduledAction.Action.choices)
    run_at = forms.DateTimeField(
        label=gettext_lazy("Dia i hora"), help_text=gettext_lazy("Hora de Barcelona."),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
    )  # fmt: skip


def _page(request, pk) -> Page:
    require_perm(request, pages.PERMISSION, write=True)
    return get_object_or_404(Page, pk=pk)


def _blocks(page, choice: str):
    if choice == DRAFT:
        return editor.editing_blocks(page)
    version = page.versions.filter(number=choice).first() if choice.isdigit() else None
    return version.blocks if version else None


def _versions(request, page, form=None):
    versions = list(page.versions.order_by("-number"))
    a = request.GET.get("a") or (str(versions[0].number) if versions else "")
    b = request.GET.get("b") or DRAFT
    old, new = _blocks(page, a), _blocks(page, b)
    context = {
        "page": page,
        "versions": versions,
        "a": a,
        "b": b,
        "rows": schedule.compare(old, new) if old is not None and new is not None else None,
        "scheduled": page.scheduled.select_related("created_by").order_by("-run_at")[:20],
        "form": form or ScheduleForm(),
    }
    return render(request, "website/admin/page_versions.html", context, status=400 if form else 200)


@never_cache
@require_GET
def versions_view(request, pk):
    return _versions(request, _page(request, pk))


def _done(request, page, call, success: str):
    try:
        call()
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, success)
    return redirect(VERSIONS, page.pk)


@never_cache
@require_POST
def schedule_view(request, pk):
    page = _page(request, pk)
    form = ScheduleForm(request.POST)
    if not form.is_valid():
        return _versions(request, page, form)
    data = form.cleaned_data
    return _done(request, page, lambda: schedule.schedule(
        page, data["action"], data["run_at"], request.user), _("Acció programada."))  # fmt: skip


@never_cache
@require_POST
def cancel_view(request, pk, item):
    page = _page(request, pk)
    scheduled = get_object_or_404(ScheduledAction, pk=item, page=page)
    return _done(request, page, lambda: schedule.cancel(scheduled, request.user),
                 _("Acció anul·lada."))  # fmt: skip


@never_cache
@require_POST
def retire_view(request, pk):
    page = _page(request, pk)
    return _done(request, page, lambda: pages.retire_page(page, request.user),
                 _("Pàgina retirada. Es pot recuperar."))  # fmt: skip


@never_cache
@require_POST
def recover_view(request, pk):
    page = _page(request, pk)
    done = _("Pàgina recuperada en esborrany. No es veu fins que es torni a publicar.")
    return _done(request, page, lambda: pages.recover_page(page, request.user), done)
