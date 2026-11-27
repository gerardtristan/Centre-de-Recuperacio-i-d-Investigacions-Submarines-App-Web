"""Versions comparables i publicació o retirada programades (T-M07-22, decisió 106; RN-M07-16 i 17;
CA-M07-26).

- `compare(old, new)`: dues llistes de blocs, bloc per bloc (igual, canviat, afegit o tret).
- `schedule` i `cancel`: WP1 (fa de WP1b fins a la T-M07-26), amb registre.
- `run_due(now)`: la crida la cua cada minut. Cada acció es fa una sola vegada (fila bloquejada i
  estat «programada»), a nom de qui la va programar: si ja no té permís o l'esborrany no es pot
  publicar, queda «no s'ha pogut fer» amb el motiu i no es publica res.
"""

import difflib

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit

from . import blocks as catalog
from . import editor, pages
from .editor_forms import summary
from .models import ScheduledAction

ACTION_SCHEDULED = "website.page_scheduled"
ACTION_CANCELLED = "website.schedule_cancelled"
S = ScheduledAction.Status


def compare(old: list, new: list) -> list[tuple[str, str, str]]:
    """(estat, bloc d'abans, bloc de després) amb l'estat `same`, `changed`, `added` o `removed`."""
    old, new = catalog.upgrade_all(old), catalog.upgrade_all(new)
    keys = difflib.SequenceMatcher(
        a=[editor.fingerprint(b) for b in old], b=[editor.fingerprint(b) for b in new],
        autojunk=False,
    )  # fmt: skip
    rows = []
    for tag, i1, i2, j1, j2 in keys.get_opcodes():
        left, right = old[i1:i2], new[j1:j2]
        if tag == "equal":
            rows += [("same", summary(a), summary(b)) for a, b in zip(left, right, strict=True)]
            continue
        for k in range(max(len(left), len(right))):
            a = summary(left[k]) if k < len(left) else ""
            b = summary(right[k]) if k < len(right) else ""
            rows.append(("changed" if a and b else "removed" if a else "added", a, b))
    return rows


@transaction.atomic
def schedule(page, action: str, run_at, actor) -> ScheduledAction:
    pages.require(actor)
    if action not in ScheduledAction.Action.values:
        raise ValidationError(_("Aquesta acció no es pot programar."))
    if run_at <= timezone.now():
        raise ValidationError(_("Tria un moment que encara no hagi passat."))
    item = ScheduledAction.objects.create(page=page, action=action, run_at=run_at,
                                          created_by=actor)  # fmt: skip
    audit.record(ACTION_SCHEDULED, actor=actor, target=page, field=action, new=run_at.isoformat())
    return item


@transaction.atomic
def cancel(item: ScheduledAction, actor) -> ScheduledAction:
    """Fins que s'executa; una de feta o ja anul·lada no canvia."""
    pages.require(actor)
    item = ScheduledAction.objects.select_for_update().get(pk=item.pk)
    if item.status != S.PENDING:
        raise ValidationError(_("Aquesta acció ja no es pot anul·lar."))
    item.status = S.CANCELLED
    item.save(update_fields=["status"])
    audit.record(ACTION_CANCELLED, actor=actor, target=item.page, field=item.action,
                 old=S.PENDING, new=S.CANCELLED)  # fmt: skip
    return item


def _run(item: ScheduledAction) -> None:
    actor = item.created_by
    if item.action == ScheduledAction.Action.PUBLISH:
        note = _("Publicació programada")
        pages.publish_draft(item.page, actor, note)
    else:
        pages.retire_page(item.page, actor)


def run_due(now=None) -> int:
    """CA-M07-26: les accions vençudes, una sola vegada. Torna quantes s'han fet."""
    done = 0
    due = ScheduledAction.objects.filter(status=S.PENDING, run_at__lte=now or timezone.now())
    for pk in due.values_list("pk", flat=True):
        with transaction.atomic():
            item = ScheduledAction.objects.select_for_update(skip_locked=True).filter(
                pk=pk, status=S.PENDING
            ).select_related("page", "created_by").first()  # fmt: skip
            if item is None:
                continue  # una altra execució l'ha agafada
            try:
                with transaction.atomic():
                    _run(item)
            except (ValidationError, Http404) as error:
                item.status = S.FAILED
                messages = getattr(error, "messages", None) or [_("Ja no té permís.")]
                item.error = " ".join(messages)[:300]
            else:
                item.status, done = S.DONE, done + 1
            item.save(update_fields=["status", "error"])
    return done
