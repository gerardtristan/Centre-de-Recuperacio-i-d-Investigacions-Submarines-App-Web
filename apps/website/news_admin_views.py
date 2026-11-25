"""Notícies a l'administració (T-M07-08; WP2, `website.news`; P-M07-B, RN-M07-05 i 14): la
llista, crear i canviar, publicar i retirar amb motiu. Els serveis (`news.py`) tornen a comprovar el
permís i la regla de les fotos. Fins que DISSENY hi posi l'entrada del menú, la prova de navegació
d'`apps/accounts` les ha de llistar com a pàgines soltes (torn del nucli)."""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.permissions import has_perm, require_perm

from . import news
from .models import MediaAsset, NewsItem

LIST = "administration:website_news"


class NewsForm(forms.ModelForm):
    class Meta:
        model = NewsItem
        fields = ["title", "slug", "date", "body", "image"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "body": forms.Textarea(attrs={"rows": 10}),
        }
        help_texts = {
            "slug": gettext_lazy("La part final de l'adreça: minúscules, xifres i guions."),
            "body": gettext_lazy("Text pla: cada línia en blanc separa un paràgraf."),
            "image": gettext_lazy(
                "Opcional. Només es pot publicar amb una foto amb autor, permís d'ús i, si s'hi "
                "veuen persones, el seu consentiment."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].queryset = MediaAsset.objects.filter(status=MediaAsset.Status.ACTIVE)


class RetireForm(forms.Form):
    reason = forms.CharField(label=gettext_lazy("Motiu de la retirada"), max_length=300)


@never_cache
@require_GET
def admin_list_view(request):
    require_perm(request, news.PERMISSION)
    context = {
        "items": NewsItem.objects.all(),
        "can_write": has_perm(request.user, news.PERMISSION, write=True),
    }
    return render(request, "website/admin/news_list.html", context)


def _page(request, item, form, retire_form=None):
    context = {"item": item, "form": form, "retire_form": retire_form or RetireForm()}
    return render(request, "website/admin/news_form.html", context)


@never_cache
@require_http_methods(["GET", "POST"])
def admin_edit_view(request, pk=None):
    require_perm(request, news.PERMISSION, write=True)
    item = get_object_or_404(NewsItem, pk=pk) if pk else None
    form = NewsForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        try:
            item = news.save_news(item, actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Notícia desada."))
            return redirect("administration:website_news_edit", item.pk)
    return _page(request, item, form)


@never_cache
@require_POST
def admin_publish_view(request, pk):
    require_perm(request, news.PERMISSION, write=True)
    item = get_object_or_404(NewsItem, pk=pk)
    try:
        news.publish(item, actor=request.user)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
        return redirect("administration:website_news_edit", item.pk)
    messages.success(request, _("Notícia publicada."))
    return redirect(LIST)


@never_cache
@require_POST
def admin_retire_view(request, pk):
    require_perm(request, news.PERMISSION, write=True)
    item = get_object_or_404(NewsItem, pk=pk)
    form = RetireForm(request.POST)
    if not form.is_valid():
        return _page(request, item, NewsForm(instance=item), form)
    news.retire(item, actor=request.user, reason=form.cleaned_data["reason"])
    messages.success(request, _("Notícia retirada."))
    return redirect(LIST)
