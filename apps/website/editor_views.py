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

from apps.core import business_settings
from apps.core.permissions import require_perm

from . import blocks as catalog
from . import editor, pages, review, video
from .editor_forms import GROUPS, KINDS, BlockForm, summary
from .models import Page, PageDraft, PageVersion

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
    # «Amb canvis sense publicar»: l'esborrany (que es queda en publicar) no és l'última versió.
    drafts = dict(PageDraft.objects.values_list("page_id", "blocks"))
    latest = PageVersion.objects.order_by("page_id", "-number").distinct("page_id")
    published = {v.page_id: catalog.upgrade_all(v.blocks) for v in latest}
    rows = [(page, page.pk in drafts and drafts[page.pk] != published.get(page.pk))
            for page in Page.objects.all()]  # fmt: skip
    return render(request, "website/admin/pages.html", {"rows": rows, "form": form})


def _editor(request, page, *, form=None, selected=None, status=200):
    blocks, revision = pages.draft_state(page)
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
        "base": editor.fingerprint(blocks[selected]) if selected is not None else "",
        "others": editor.touch(page, request.user),
        "autosave_ms": 1000 * business_settings.get("website.autosave_seconds"),
        "theme": "fosc" if request.GET.get("tema") == "fosc" else "clar",
        "versions": page.versions.order_by("-number")[:10],
        "share_warnings": pages.share_warnings(page),
        "review": review.review(page, blocks),
        "revision": revision,
    }
    return render(request, "website/admin/page_editor.html", context, status=status)


@never_cache
@require_http_methods(["GET"])
def editor_view(request, pk):
    require_perm(request, pages.PERMISSION, write=True)
    return _editor(request, get_object_or_404(Page, pk=pk))


def revision_of(request) -> int:
    """La revisió de l'esborrany que té la pantalla; sense, una que no coincideix mai."""
    value = request.POST.get("revision", "")
    return int(value) if value.isdigit() else -1


def save_block(request, page, blocks: list, index: int) -> tuple[BlockForm, int, int | None]:
    """Desa el formulari del bloc `index`. Estat 200: desat; 400: no és vàlid; 409: algú altre ha
    canviat o mogut aquest bloc des que es va obrir (CA-M07-32: no se li esborra res). La revisió
    nova només torna si la pantalla estava al dia (si no, l'ha de tornar a carregar)."""
    if not 0 <= index < len(blocks):
        raise IndexError(index)
    form = BlockForm(blocks[index]["kind"], request.POST, block=blocks[index])
    if not form.is_valid():
        return form, 400, None
    base = request.POST.get("base", "")
    # La miniatura d'un vídeo es baixa abans de bloquejar la pàgina (cap espera a la xarxa amb el
    # bloqueig posat).
    prepared = video.with_thumbnail(form.to_block(blocks[index]), request.user, blocks[index])
    extra = {"thumbnail": prepared["thumbnail"]} if prepared.get("thumbnail") else {}

    def compute(current):
        if index >= len(current) or base != editor.fingerprint(current[index]):
            raise pages.DraftConflict
        block = {**form.to_block(current[index]), **extra}
        return editor.apply(current, "update", index, block=block)

    try:
        draft, before = editor.change(request, page, compute, revision=None)
    except ValidationError as error:  # també `DraftConflict`
        form.add_error(None, error)
        return form, 409 if isinstance(error, pages.DraftConflict) else 400, None
    return form, 200, draft.revision if before == revision_of(request) else None


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
    try:
        if action in ("undo", "redo"):
            if not editor.step(request, page, action, revision=revision_of(request)):
                messages.error(request, _("No hi ha res per desfer o refer."))
            return redirect(url)
        index = int(request.POST.get("index", "-1"))
        order = [int(i) for i in request.POST.get("order", "").split(",") if i != ""]
        if action == "update":
            form, status, _revision = save_block(request, page, editor.editing_blocks(page), index)
            if status == 400:
                return _editor(request, page, form=form, selected=index, status=status)
            if status == 409:  # el formulari, de nou amb el bloc tal com és ara
                messages.error(request, " ".join(form.non_field_errors()))
                return redirect(f"{url}?bloc={index}")
            new = editor.editing_blocks(page)
        else:

            def compute(current):
                return editor.apply(current, action, index, kind=request.POST.get("kind", ""),
                                    order=order)  # fmt: skip

            new = editor.change(request, page, compute, revision=revision_of(request))[0].blocks
    except (ValueError, IndexError):
        messages.error(request, _("Aquesta acció no es pot fer amb aquest bloc."))
        return redirect(url)
    except ValidationError as error:  # sobretot `DraftConflict`: ara amb l'esborrany actual
        messages.error(request, " ".join(error.messages))
        return _editor(request, page, status=409 if isinstance(error, pages.DraftConflict) else 400)
    messages.success(request, _("Esborrany desat."))
    target = _target(action, index)
    return redirect(f"{url}?bloc={target}" if target is not None and target < len(new) else url)
