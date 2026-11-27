"""Vista prèvia en viu, desat automàtic, avís d'edició simultània, compartir, publicar i tornar a
una versió (T-M07-06b, decisió 106; RN-M07-13, 14, 16 i 23; HU-M07-02; CA-M07-20 i 32). Tot demana
WP1 (fa de WP1a i WP1b fins a la T-M07-26); la vista prèvia només s'obre amb sessió, dins de
l'editor (mateix origen), mai per una adreça pública."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET, require_POST

from apps.core.permissions import require_perm

from . import editor, pages
from . import render as renderer
from .editor_views import _editor as render_editor
from .editor_views import revision_of, save_block
from .models import Page, PageVersion

EDITOR = "administration:website_page_editor"


def _page(request, pk) -> Page:
    require_perm(request, pages.PERMISSION, write=True)
    return get_object_or_404(Page, pk=pk)


@never_cache
@xframe_options_sameorigin
@require_GET
def preview_view(request, pk):
    """RN-M07-23: l'esborrany amb els blocs reals; cada bloc porta el seu número per triar-lo."""
    page = _page(request, pk)
    content = renderer.render_blocks(editor.editing_blocks(page), page, preview=True)
    theme = "dark" if request.GET.get("tema") == "fosc" else "light"
    context = {"page": page, "content": content, "theme": theme}
    return render(request, "website/admin/page_preview.html", context)


@never_cache
@require_POST
def autosave_view(request, pk):
    """Desat automàtic del bloc triat (si porta `index`) i, sempre, qui més té la pàgina oberta."""
    page = _page(request, pk)
    others = editor.touch(page, request.user)
    if "index" not in request.POST:
        return JsonResponse({"others": others})
    blocks = editor.editing_blocks(page)
    try:
        index = int(request.POST["index"])
        form, status, revision = save_block(request, page, blocks, index)
    except (ValueError, IndexError):
        return JsonResponse({"error": _("Aquest bloc ja no hi és."), "others": others}, status=409)
    if status != 200:
        errors = [str(e) for errors in form.errors.values() for e in errors]
        return JsonResponse({"error": " ".join(errors), "others": others}, status=status)
    base = editor.fingerprint(editor.editing_blocks(page)[index])
    # `revision` és None si algú altre havia desat abans: la pantalla ha de tornar a carregar
    # abans de fer cap altra acció sobre la llista.
    return JsonResponse({"base": base, "revision": revision, "others": others})


@never_cache
@require_POST
def share_view(request, pk):
    """RN-M07-13: el títol i la descripció per compartir; massa llargs, un avís."""
    page = _page(request, pk)
    fields = {k: request.POST.get(k, "").strip() for k in ("share_title", "share_description")}
    try:
        page, warnings = pages.save_page(page, actor=request.user, **fields)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
        return redirect(EDITOR, page.pk)
    messages.success(request, _("Dades per compartir desades."))
    for warning in warnings:
        messages.warning(request, warning)
    return redirect(EDITOR, page.pk)


@never_cache
@require_POST
def publish_view(request, pk):
    """Publica el que s'edita (RN-M07-03; queda al registre, RN-M07-14 i CA-M07-20)."""
    page = _page(request, pk)
    try:
        version = pages.publish_draft(page, request.user, request.POST.get("note", ""),
                                      revision=revision_of(request))  # fmt: skip
    except pages.DraftConflict as error:
        messages.error(request, " ".join(error.messages))
        return render_editor(request, page, status=409)  # amb l'esborrany tal com és ara
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, _("Publicada la versió %(n)s.") % {"n": version.number})
    return redirect(EDITOR, page.pk)


@never_cache
@require_POST
def revert_view(request, pk, number):
    """HU-M07-02: torna a publicar una versió anterior. L'esborrany que hi hagués es pot recuperar
    amb «Desfés»."""
    page = _page(request, pk)
    version = get_object_or_404(PageVersion, page=page, number=number)
    try:
        with transaction.atomic():  # sobre una revisió antiga, ni es publica ni es desa res
            new = pages.revert_to(version, request.user)
            editor.change(request, page, lambda _blocks: new.blocks, revision=revision_of(request))
    except pages.DraftConflict as error:
        messages.error(request, " ".join(error.messages))
        return render_editor(request, page, status=409)  # amb l'esborrany tal com és ara
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, _("Publicada la versió %(n)s.") % {"n": new.number})
    return redirect(EDITOR, page.pk)
