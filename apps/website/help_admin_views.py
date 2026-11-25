"""Preguntes freqüents a l'administració (T-M07-09b; WP4, `website.help`; P-M07-G, RN-M07-12): la
llista per tema, un tema nou, una pregunta nova, editar-la i publicar-la o retirar-la de l'ajuda.
No s'esborra res: una pregunta retirada deixa de sortir i es pot tornar a publicar. Els serveis
(`help.py`) tornen a comprovar WP4 al servidor."""

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
from .models import FaqEntry, FaqTopic

LIST = "administration:website_help"


class TopicForm(forms.ModelForm):
    class Meta:
        model = FaqTopic
        fields = ["name", "order"]


class EntryForm(forms.ModelForm):
    class Meta:
        model = FaqEntry
        fields = ["topic", "question", "answer", "order"]
        widgets = {"answer": forms.Textarea(attrs={"rows": 8})}
        help_texts = {"answer": gettext_lazy("Text pla: cada línia en blanc separa un paràgraf.")}


@never_cache
@require_GET
def admin_list_view(request):
    require_perm(request, help.PERMISSION)
    can_write = has_perm(request.user, help.PERMISSION, write=True)
    context = {
        "topics": FaqTopic.objects.prefetch_related("entries"),
        "can_write": can_write,
        "topic_form": TopicForm() if can_write else None,
    }
    return render(request, "website/admin/help_list.html", context)


@never_cache
@require_POST
def admin_topic_add_view(request):
    require_perm(request, help.PERMISSION, write=True)
    form = TopicForm(request.POST)
    if form.is_valid():
        try:
            help.save_topic(None, actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
        else:
            messages.success(request, _("Tema creat."))
    else:
        messages.error(request, " ".join(e for errors in form.errors.values() for e in errors))
    return redirect(LIST)


@never_cache
@require_http_methods(["GET", "POST"])
def admin_edit_view(request, pk=None):
    require_perm(request, help.PERMISSION, write=True)
    entry = get_object_or_404(FaqEntry, pk=pk) if pk else None
    form = EntryForm(request.POST or None, instance=entry)
    if request.method == "POST" and form.is_valid():
        try:
            entry = help.save_entry(entry, actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Pregunta desada."))
            return redirect("administration:website_help_edit", entry.pk)
    return render(request, "website/admin/help_form.html", {"entry": entry, "form": form})


@never_cache
@require_POST
def admin_publish_view(request, pk):
    """Publica o retira de l'ajuda (`publish` = «1» o «0»)."""
    require_perm(request, help.PERMISSION, write=True)
    entry = get_object_or_404(FaqEntry, pk=pk)
    published = request.POST.get("publish") == "1"
    try:
        help.save_entry(entry, actor=request.user, published=published)
    except ValidationError as error:  # una pregunta incompleta: es corregeix a la fitxa
        messages.error(request, " ".join(error.messages))
        return redirect("administration:website_help_edit", entry.pk)
    messages.success(request, _("Pregunta publicada.") if published else _("Pregunta retirada."))
    return redirect(LIST)
