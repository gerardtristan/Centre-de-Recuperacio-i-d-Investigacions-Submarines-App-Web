"""Editor de la web a l'administració (T-M07-06a, decisió 106; `/gestio/web/pagines/`): la llista
de pàgines i l'editor de blocs d'una pàgina. Tot demana WP1 (`website.pages`, «Sí»; fa de WP1a fins
a la T-M07-26) i els serveis ho tornen a comprovar; cada canvi desa l'esborrany validat."""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.permissions import require_perm

from . import editor, pages
from .editor_forms import GROUPS, KINDS, BlockForm, summary
from .models import Page, PageDraft

NewPageForm = forms.modelform_factory(Page, fields=["title", "slug", "template"])


@never_cache
@require_http_methods(["GET", "POST"])
def pages_view(request):
    require_perm(request, pages.PERMISSION, write=True)
    form = NewPageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        # El formulari ja ha fet la validació del model (adreça única i sense xocar amb cap ruta).
        page, _warnings = pages.save_page(None, actor=request.user, **form.cleaned_data)
        messages.success(request, _("Pàgina creada en esborrany."))
        return redirect("administration:website_page_editor", page.pk)
    drafts = set(PageDraft.objects.values_list("page_id", flat=True))
    rows = [(page, page.pk in drafts) for page in Page.objects.all()]
    return render(request, "website/admin/pages.html", {"rows": rows, "form": form})


def _editor(request, page, *, form=None, selected=None, status=200):
    blocks = editor.editing_blocks(page)
    if selected is None:
        bloc = request.GET.get("bloc", "")
        selected = int(bloc) if bloc.isdigit() and int(bloc) < len(blocks) else None
    if form is None and selected is not None:
        form = BlockForm(blocks[selected]["kind"], block=blocks[selected])
    context = {
        "page": page,
        "items": [(i, b, summary(b)) for i, b in enumerate(blocks)],
        "selected": selected,
        "selected_kind": KINDS[blocks[selected]["kind"]] if selected is not None else "",
        "last": len(blocks) - 1,
        "form": form,
        "groups": [(label, [(k, KINDS[k]) for k in kinds]) for label, kinds in GROUPS],
        "history": editor.can(request, page),
    }
    return render(request, "website/admin/page_editor.html", context, status=status)


@never_cache
@require_http_methods(["GET"])
def editor_view(request, pk):
    require_perm(request, pages.PERMISSION, write=True)
    return _editor(request, get_object_or_404(Page, pk=pk))


def _target(action: str, index: int) -> int | None:
    """Quin bloc queda triat després de l'acció."""
    if action in ("add", "down", "duplicate"):
        return index + 1 if index >= 0 else 0
    return {"up": index - 1, "hide": index, "update": index}.get(action)


@never_cache
@require_POST
def editor_action_view(request, pk):
    require_perm(request, pages.PERMISSION, write=True)
    page = get_object_or_404(Page, pk=pk)
    action = request.POST.get("action", "")
    url = reverse("administration:website_page_editor", args=[page.pk])
    if action in ("undo", "redo"):
        if not editor.step(request, page, action):
            messages.error(request, _("No hi ha res per desfer o refer."))
        return redirect(url)
    blocks = editor.editing_blocks(page)
    try:
        index = int(request.POST.get("index", "-1"))
        order = [int(i) for i in request.POST.get("order", "").split(",") if i != ""]
        block = None
        if action == "update":
            if not 0 <= index < len(blocks):
                raise IndexError(index)
            form = BlockForm(blocks[index]["kind"], request.POST, block=blocks[index])
            if not form.is_valid():
                return _editor(request, page, form=form, selected=index, status=400)
            block = form.to_block(blocks[index])
        new = editor.apply(blocks, action, index, kind=request.POST.get("kind", ""),
                           order=order, block=block)  # fmt: skip
    except (ValueError, IndexError):
        messages.error(request, _("Aquesta acció no es pot fer amb aquest bloc."))
        return redirect(url)
    try:
        editor.change(request, page, new)
    except ValidationError as error:
        if action == "update":
            form.add_error(None, error)
            return _editor(request, page, form=form, selected=index, status=400)
        messages.error(request, " ".join(error.messages))
        return redirect(url)
    messages.success(request, _("Esborrany desat."))
    target = _target(action, index)
    return redirect(f"{url}?bloc={target}" if target is not None and target < len(new) else url)
