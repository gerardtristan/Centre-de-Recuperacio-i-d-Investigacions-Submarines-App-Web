"""Selector d'activitats destacades a l'administració (T-M07-29; RN-M07-21; WP1, `website.pages`).

La llista de les destacades, en ordre, amb les dades del 02 resoltes a cada petició (una que ja no
és pública es marca i no surt a la web), i, amb «Sí», afegir-ne una de les publicades, canviar-ne
l'ordre i treure-la. Els serveis (`featured.py`) tornen a comprovar el permís al servidor.
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from apps.activities import public as activities
from apps.core.permissions import has_perm, require_perm

from . import featured
from .models import FeaturedActivity

LIST = "administration:website_featured"


class AddForm(forms.Form):
    activity = forms.TypedChoiceField(label=gettext_lazy("Activitat"), coerce=int)
    visible_from = forms.DateField(
        label=gettext_lazy("Visible des del"), required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )  # fmt: skip
    visible_until = forms.DateField(
        label=gettext_lazy("Visible fins al"), required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text=gettext_lazy("Buides, es veu mentre l'activitat és publicada."),
    )  # fmt: skip

    def __init__(self, *args, choices=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["activity"].choices = choices


def _choices():
    taken = set(FeaturedActivity.objects.values_list("activity_ref", flat=True))
    return [
        (a.pk, f"{a.title} · {a.starts_on:%d/%m/%Y}")
        for a in activities.public_list() if a.pk not in taken
    ]  # fmt: skip


def _rows():
    rows = []
    for row in FeaturedActivity.objects.all():
        try:
            info = activities.get_activity(row.activity_ref)
        except activities.NotFound:
            info = None  # retirada o ja no pública: no surt a la web
        rows.append((row, info))
    return rows


@never_cache
@require_GET
def featured_view(request):
    require_perm(request, featured.PERMISSION)
    can_write = has_perm(request.user, featured.PERMISSION, write=True)
    context = {
        "rows": _rows(),
        "can_write": can_write,
        "form": AddForm(choices=_choices()) if can_write else None,
    }
    return render(request, "website/admin/featured.html", context)


@never_cache
@require_POST
def featured_add_view(request):
    require_perm(request, featured.PERMISSION, write=True)
    form = AddForm(request.POST, choices=_choices())
    if form.is_valid():
        data = form.cleaned_data
        try:
            featured.add(
                data["activity"], actor=request.user, visible_from=data["visible_from"],
                visible_until=data["visible_until"],
            )  # fmt: skip
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
        else:
            messages.success(request, _("Activitat destacada."))
    else:
        messages.error(request, " ".join(e for errors in form.errors.values() for e in errors))
    return redirect(LIST)


@never_cache
@require_POST
def featured_change_view(request, pk):
    require_perm(request, featured.PERMISSION, write=True)
    row = get_object_or_404(FeaturedActivity, pk=pk)
    action = request.POST.get("action")
    if action == "remove":
        featured.remove(row, actor=request.user)
        messages.success(request, _("Ja no és destacada."))
    elif action in ("up", "down"):
        featured.move(row, actor=request.user, up=action == "up")
    return redirect(LIST)
