"""Patrons i blocs compartits des de l'editor (T-M07-20a, decisió 106): desar la pàgina com a
patró, inserir-ne un, fer compartit el bloc triat, inserir-ne un i canviar-ne el contingut (es
canvia a totes les pàgines on surt). Tot demana WP1 i els serveis ho tornen a comprovar; els
canvis a l'esborrany porten la revisió de la pantalla (CA-M07-32)."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from apps.core.permissions import require_perm

from . import editor, library, pages
from .editor_forms import BlockForm
from .editor_views import _editor as render_editor
from .editor_views import revision_of
from .models import Page, Pattern, SharedBlock


def _insert(blocks, index, new):
    at = index + 1 if 0 <= index < len(blocks) else len(blocks)
    return blocks[:at] + new + blocks[at:]


def _update_shared(request, page, blocks, index):
    """El contingut d'un bloc compartit: una versió nova, si ningú no l'ha canviat abans."""
    ref = blocks[index]
    shared = get_object_or_404(SharedBlock, pk=ref.get("shared"))
    content = library.current_shared([shared.pk])[shared.pk]
    if request.POST.get("base", "") != editor.fingerprint(content):
        raise pages.DraftConflict
    form = BlockForm(content["kind"], request.POST, block=content)
    if not form.is_valid():
        raise ValidationError(" ".join(str(e) for errors in form.errors.values() for e in errors))
    library.save_shared(shared, form.to_block(content), request.user)
    return _(
        "Bloc compartit desat: canvia l'esborrany de totes les pàgines on surt; a la web, "
        "quan es torni a publicar cada pàgina."
    )


@never_cache
@require_POST
def library_view(request, pk):
    require_perm(request, pages.PERMISSION, write=True)
    page = get_object_or_404(Page, pk=pk)
    action, name = request.POST.get("action", ""), request.POST.get("name", "")
    url = reverse("administration:website_page_editor", args=[page.pk])
    revision = revision_of(request)
    try:
        index = int(request.POST.get("index", "-1"))
        blocks = editor.editing_blocks(page)
        if action in ("make_shared", "update_shared") and not 0 <= index < len(blocks):
            raise IndexError(index)
        if action == "save_pattern":
            library.save_pattern(name, blocks, request.user)
            done = _("Patró desat.")
        elif action == "insert_pattern":
            pattern = get_object_or_404(Pattern, pk=request.POST.get("pattern"))
            new = library.pattern_blocks(pattern)
            editor.change(request, page, lambda b: _insert(b, index, new), revision=revision)
            done = _("Patró inserit.")
        elif action == "insert_shared":
            shared = get_object_or_404(SharedBlock, pk=request.POST.get("shared"))
            ref = [{"kind": "shared", "shared": shared.pk}]
            editor.change(request, page, lambda b: _insert(b, index, ref), revision=revision)
            done = _("Bloc compartit inserit.")
        elif action == "make_shared":
            with transaction.atomic():
                version = library.save_shared(name, blocks[index], request.user)
                ref = {"kind": "shared", "shared": version.shared_id,
                       "hidden": blocks[index].get("hidden", False)}  # fmt: skip
                editor.change(request, page, lambda b: editor.apply(b, "update", index, block=ref),
                              revision=revision)  # fmt: skip
            done = _("Ara és un bloc compartit.")
        elif action == "update_shared" and blocks[index].get("kind") == "shared":
            done = _update_shared(request, page, blocks, index)
        else:
            raise ValueError(action)
    except (ValueError, IndexError):
        messages.error(request, _("Aquesta acció no es pot fer amb aquest bloc."))
        return redirect(url)
    except ValidationError as error:  # també `DraftConflict`
        messages.error(request, " ".join(error.messages))
        return render_editor(request, page, status=409 if isinstance(error, pages.DraftConflict)
                             else 400)  # fmt: skip
    messages.success(request, done)
    return redirect(f"{url}?bloc={index}" if index >= 0 else url)
