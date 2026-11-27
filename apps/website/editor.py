"""Editor de blocs d'una pàgina (T-M07-06a, decisió 106; RN-M07-15 i 16).

- `editing_blocks(page)`: el que s'edita: l'esborrany o, si no n'hi ha, l'última versió (amb
  els tipus antics ja traduïts) o res.
- `apply(blocks, action, index, ...)`: afegir, moure, reordenar, duplicar, amagar, treure i
  canviar un bloc. Torna una llista nova; no desa res.
- `change`, `undo` i `redo`: desen l'esborrany amb `pages.save_draft` (WP1 i la validació de
  desar) i porten l'historial de desfer i refer a la sessió del navegador, per pàgina.
"""

import copy

from . import blocks as catalog
from . import pages
from .models import PageDraft

HISTORY_MAX = 50  # límit tècnic: la sessió no creix sense límit
ACTIONS = ("add", "up", "down", "reorder", "duplicate", "hide", "remove", "update")


def editing_blocks(page) -> list:
    draft = PageDraft.objects.filter(page=page).first()
    if draft is not None:
        return draft.blocks
    version = pages.current_version(page)
    return catalog.upgrade_all(version.blocks) if version else []


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


def change(request, page, blocks: list) -> None:
    """Desa l'esborrany i apunta l'estat anterior per desfer-lo. `ValidationError`: res."""
    previous = editing_blocks(page)
    pages.save_draft(page, blocks, request.user)
    history = _history(request, page)
    history["undo"] = (history["undo"] + [previous])[-HISTORY_MAX:]
    history["redo"] = []
    request.session.modified = True


def _step(request, page, source: str, target: str) -> bool:
    history = _history(request, page)
    if not history[source]:
        return False
    blocks = history[source][-1]
    current = editing_blocks(page)
    pages.save_draft(page, blocks, request.user)  # torna a validar i a demanar WP1
    history[source].pop()
    history[target] = (history[target] + [current])[-HISTORY_MAX:]
    request.session.modified = True
    return True


def undo(request, page) -> bool:
    return _step(request, page, "undo", "redo")


def redo(request, page) -> bool:
    return _step(request, page, "redo", "undo")


def can(request, page) -> dict:
    history = request.session.get(f"website.editor.{page.pk}", {})
    return {"undo": bool(history.get("undo")), "redo": bool(history.get("redo"))}
