"""Editor de blocs d'una pàgina (T-M07-06a, decisió 106; RN-M07-15 i 16). `apply` canvia una
llista de blocs sense desar res; `change` i `step` desen l'esborrany amb `pages.save_draft` (WP1
i la validació de desar) i porten l'historial de desfer i refer a la sessió, per pàgina."""

import copy
import datetime
import hashlib
import json

from django.db import transaction
from django.utils import timezone

from apps.core import business_settings

from . import blocks as catalog
from . import pages
from .models import Page, PageDraft, PageEditing

HISTORY_MAX = 50  # límit tècnic: la sessió no creix sense límit


def editing_blocks(page) -> list:
    """L'esborrany o, si no n'hi ha, l'última versió (amb els tipus antics traduïts) o res."""
    return pages.draft_state(page)[0]


def apply(blocks: list, action: str, index: int, *, kind="", order=(), block=None) -> list:
    """`IndexError` o `ValueError` si l'acció no té sentit amb aquesta llista."""
    blocks = copy.deepcopy(blocks)
    if action == "add":
        if kind not in catalog.CATALOG:
            raise ValueError(kind)
        blocks.insert(index + 1 if blocks else 0, {"kind": kind})
        return blocks
    if action == "reorder":
        if sorted(order) != list(range(len(blocks))):
            raise ValueError(order)
        return [blocks[i] for i in order]
    if not 0 <= index < len(blocks):
        raise IndexError(index)
    if action in ("up", "down"):
        other = index - 1 if action == "up" else index + 1
        if not 0 <= other < len(blocks):
            raise IndexError(other)
        blocks[index], blocks[other] = blocks[other], blocks[index]
    elif action == "duplicate":
        blocks.insert(index + 1, copy.deepcopy(blocks[index]))
    elif action == "hide":
        blocks[index]["hidden"] = not blocks[index].get("hidden", False)
    elif action == "remove":
        del blocks[index]
    elif action == "update":
        blocks[index] = block
    else:
        raise ValueError(action)
    return blocks


def _history(request, page) -> dict:
    return request.session.setdefault(f"website.editor.{page.pk}", {"undo": [], "redo": []})


@transaction.atomic
def _write(request, page, compute, revision) -> tuple[list, int, PageDraft]:
    """Amb la pàgina bloquejada: `compute(blocs actuals)` dona la llista nova. `revision`: la que
    té la pantalla; si no coincideix, `pages.DraftConflict` i no es desa res."""
    Page.objects.select_for_update().get(pk=page.pk)
    previous, current = pages.draft_state(page)
    if revision is not None and revision != current:
        raise pages.DraftConflict
    return previous, current, pages.save_draft(page, compute(previous), request.user)


def change(request, page, compute, *, revision: int | None) -> tuple[PageDraft, int]:
    """Desa l'esborrany i apunta l'estat anterior per desfer-lo. Torna l'esborrany i la revisió
    que hi havia abans. `ValidationError` (també `DraftConflict`): res."""
    previous, before, draft = _write(request, page, compute, revision)
    history = _history(request, page)
    history["undo"] = (history["undo"] + [previous])[-HISTORY_MAX:]
    history["redo"] = []
    request.session.modified = True
    return draft, before


def step(request, page, action: str, *, revision: int | None) -> bool:
    """`undo` o `redo`, només sobre la revisió que té la pantalla. Fals si no hi ha res a fer."""
    source, target = ("undo", "redo") if action == "undo" else ("redo", "undo")
    history = _history(request, page)
    if not history[source]:
        return False
    current, _before, _draft = _write(request, page, lambda _blocks: history[source][-1], revision)
    history[source].pop()
    history[target] = (history[target] + [current])[-HISTORY_MAX:]
    request.session.modified = True
    return True


def can(request, page) -> dict:
    history = request.session.get(f"website.editor.{page.pk}", {})
    return {"undo": bool(history.get("undo")), "redo": bool(history.get("redo"))}


def fingerprint(block: dict) -> str:
    """Empremta d'un bloc: el desat automàtic només el canvia si ningú no l'ha tocat abans."""
    return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()[:16]


def touch(page, account) -> list[str]:
    """Apunta que `account` té l'editor obert i torna qui més l'ha tocat fa poc (CA-M07-32)."""
    now = timezone.now()
    PageEditing.objects.update_or_create(page=page, account=account, defaults={"seen_at": now})
    seconds = business_settings.get("website.autosave_seconds")
    recent = PageEditing.objects.filter(page=page, seen_at__gte=now - datetime.timedelta(
        seconds=3 * seconds))  # fmt: skip  # tres desats perduts: ja no hi és
    return sorted(recent.exclude(account=account).values_list("account__login", flat=True))
