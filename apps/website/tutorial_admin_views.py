"""Tutorials a l'administració (T-M07-10b; WP4, `website.help`; RN-M07-05, 11 i 14): la llista,
un tutorial nou (es desa sense publicar), editar-lo i publicar-lo o retirar-lo de l'ajuda. No
s'esborra res. Els serveis (`help.py`) tornen a comprovar WP4, la foto i la pantalla al servidor,
amb la fila bloquejada i el registre (`website.tutorial_*`)."""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.permissions import has_perm, require_perm

from . import help
from .models import MediaAsset, Tutorial

LIST = "administration:website_tutorials"


class TutorialForm(forms.ModelForm):
    class Meta:
        model = Tutorial
        fields = ["title", "slug", "steps", "image", "screen_code", "order"]
        widgets = {"steps": forms.Textarea(attrs={"rows": 8})}
        help_texts = {
            "slug": gettext_lazy("La part final de l'adreça: minúscules, xifres i guions."),
            "steps": gettext_lazy("Text pla: un pas per línia."),
            "image": gettext_lazy(
                "Opcional. Només les fotos amb autor, permís d'ús i consentiment."
            ),
            "screen_code": gettext_lazy(
                "Opcional. El nom de la pantalla on surt «Mira com es fa» (p. ex. payments:charge)."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active = MediaAsset.objects.filter(status=MediaAsset.Status.ACTIVE)
        self.fields["image"].queryset = active.filter(
            pk__in=[a.pk for a in active if a.publishable]
        )


@never_cache
@require_GET
def admin_list_view(request):
    require_perm(request, help.PERMISSION)
    context = {
        "tutorials": Tutorial.objects.all(),
        "can_write": has_perm(request.user, help.PERMISSION, write=True),
    }
    return render(request, "website/admin/tutorial_list.html", context)


@never_cache
@require_http_methods(["GET", "POST"])
def admin_edit_view(request, pk=None):
    require_perm(request, help.PERMISSION, write=True)
    tutorial = get_object_or_404(Tutorial, pk=pk) if pk else None
    form = TutorialForm(request.POST or None, instance=tutorial)
    if request.method == "POST" and form.is_valid():
        try:
            tutorial = help.save_tutorial(tutorial, actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Tutorial desat."))
            return redirect("administration:website_tutorial_edit", tutorial.pk)
    return render(request, "website/admin/tutorial_form.html", {"tutorial": tutorial, "form": form})


@never_cache
@require_POST
def admin_publish_view(request, pk):
    """Publica o retira de l'ajuda (`publish` = «1» o «0»)."""
    require_perm(request, help.PERMISSION, write=True)
    tutorial = get_object_or_404(Tutorial, pk=pk)
    published = request.POST.get("publish") == "1"
    try:
        help.save_tutorial(tutorial, actor=request.user, published=published)
    except ValidationError as error:  # una foto que ja no es pot publicar: es corregeix a la fitxa
        messages.error(request, " ".join(error.messages))
        return redirect("administration:website_tutorial_edit", tutorial.pk)
    messages.success(request, _("Tutorial publicat.") if published else _("Tutorial retirat."))
    return redirect(LIST)
