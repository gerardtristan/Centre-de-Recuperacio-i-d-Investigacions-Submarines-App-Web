"""Menú, capçalera i peu de la web a l'administració (T-M07-21; WP9, `website.chrome`; addenda 106):
la llista dels enllaços del menú principal, un enllaç nou o canviat, treure'n un, i una versió nova
de la capçalera i el peu. Els serveis (`menus.py`) tornen a comprovar WP9, l'adreça (`https:` o una
ruta que existeix) i el submenú d'un nivell al servidor, amb el registre."""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.permissions import require_perm

from . import menus
from .models import Menu, MenuItem, SiteChrome

LIST = "administration:website_menu"


def _main_menu():
    return get_object_or_404(Menu, code=menus.MAIN)


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["label", "page", "url", "parent", "order"]
        help_texts = {
            "page": gettext_lazy("Una pàgina de la web; només surt al menú quan és publicada."),
            "url": gettext_lazy(
                "O bé una adreça de la plataforma (p. ex. /noticies/) o una adreça que comenci "
                "per https://. Buida i sense pàgina: un grup amb submenú."
            ),
            "parent": gettext_lazy("Opcional: l'enllaç de dalt del qual penja (un sol nivell)."),
            "order": gettext_lazy("A partir del setè enllaç de dalt, van a «Més»."),
        }

    def __init__(self, *args, menu, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.menu = menu  # la validació del model compara el menú del submenú
        top = MenuItem.objects.filter(menu=menu, parent=None)
        if self.instance.pk:
            top = top.exclude(pk=self.instance.pk)
        self.fields["parent"].queryset = top


class ChromeForm(forms.ModelForm):
    class Meta:
        model = SiteChrome
        fields = ["header_text", "footer_text", "note"]
        widgets = {"footer_text": forms.Textarea(attrs={"rows": 4})}
        help_texts = {
            "footer_text": gettext_lazy("Text pla: no admet HTML."),
            "note": gettext_lazy("Opcional: per què es canvia. Queda al registre."),
        }


@never_cache
@require_http_methods(["GET", "POST"])
def admin_menu_view(request):
    """La llista dels enllaços i la capçalera i el peu. WP9 només té l'abast «Tot»."""
    require_perm(request, menus.PERMISSION, write=True)
    chrome = menus.current_chrome()
    initial = (
        {"header_text": chrome.header_text, "footer_text": chrome.footer_text} if chrome else {}
    )
    form = ChromeForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            menus.save_chrome(actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Capçalera i peu desats."))
            return redirect(LIST)
    items = MenuItem.objects.filter(menu=_main_menu()).select_related("page", "parent")
    context = {"items": items, "chrome": chrome, "form": form}
    return render(request, "website/admin/menu.html", context)


@never_cache
@require_http_methods(["GET", "POST"])
def admin_item_view(request, pk=None):
    require_perm(request, menus.PERMISSION, write=True)
    menu = _main_menu()
    item = get_object_or_404(MenuItem, pk=pk, menu=menu) if pk else None
    form = MenuItemForm(request.POST or None, instance=item, menu=menu)
    if request.method == "POST" and form.is_valid():
        fields = form.cleaned_data if item else {**form.cleaned_data, "menu": menu}
        try:
            menus.save_item(item, actor=request.user, **fields)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Enllaç desat."))
            return redirect(LIST)
    return render(request, "website/admin/menu_item.html", {"item": item, "form": form})


@never_cache
@require_POST
def admin_item_remove_view(request, pk):
    require_perm(request, menus.PERMISSION, write=True)
    item = get_object_or_404(MenuItem, pk=pk, menu=_main_menu())
    try:
        menus.remove_item(item, actor=request.user)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, _("Enllaç tret del menú."))
    return redirect(LIST)
