"""Pantalla de la prova de Cluber (T-M01-24; CA-M01-20, CA-20.1).

Precisions: files de la T-M01-24 a docs/planning.md#ajustos-060-lectura (pantalla, recepció,
CSRF, registre de la prova i numeració).

- P18 es comprova abans de llegir el fitxer. La vista exterior és exempta de CSRF només perquè
  els gestors de pujada es puguin canviar abans que el CSRF llegeixi el POST (patró documentat
  de Django); `_protected` sí que està protegida.
- Un sol gestor de pujada, en memòria, que compta els bytes rebuts: mai cap fitxer temporal.
  Exactament un fitxer al camp `fitxer`. Si el cos declarat supera 1 MiB + 64 KiB, es rebutja
  abans de llegir-lo (413, sense registre: encara no s'ha comprovat el CSRF).
- Una entrada al registre per intent autoritzat i amb CSRF vàlid. L'empremta, només amb el
  fitxer complet i si no s'ha rebutjat per IBAN. La pantalla només fa servir `summary()`.
"""

import hashlib
from collections import Counter

from django.core.files.uploadhandler import MemoryFileUploadHandler, StopUpload
from django.http.multipartparser import MultiPartParserError
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods

from apps.core import audit
from apps.core.permissions import permission_required
from apps.members.imports import cluber

FIELD = "fitxer"
# Marge per a les capçaleres del multipart: no amplia el límit del CSV (cluber.MAX_BYTES).
BODY_CEILING = cluber.MAX_BYTES + 64 * 1024

RECEPTION_MESSAGES = {
    "too_large": cluber.MESSAGES["too_large"],
    "no_file": _("No s'ha rebut cap fitxer. Tria un fitxer CSV i torna-ho a provar."),
    "too_many_files": _("Cal enviar exactament un fitxer CSV, al camp del formulari."),
    "unreadable": _("No s'ha pogut llegir la pujada. Torna-ho a provar."),
}
RELATION = _("Relació entre el document i el número")
WHOLE_ROW = _("Tot el registre")


class _OneFileInMemory(MemoryFileUploadHandler):
    """Un sol fitxer al camp previst, només en memòria, amb els bytes comptats en arribar."""

    def __init__(self, request=None):
        super().__init__(request)
        self.problem = None
        self.files = 0
        self.received = 0

    def handle_raw_input(self, *args, **kwargs):
        # Sempre en memòria, sigui quina sigui la mida declarada: no hi ha cap gestor de disc.
        self.activated = True

    def new_file(self, field_name, *args, **kwargs):
        self.files += 1
        if field_name != FIELD or self.files > 1:
            self.problem = "too_many_files"
            raise StopUpload(connection_reset=False)
        super().new_file(field_name, *args, **kwargs)

    def receive_data_chunk(self, raw_data, start):
        self.received += len(raw_data)
        if self.received > cluber.MAX_BYTES:
            self.problem = "too_large"
            raise StopUpload(connection_reset=False)
        return super().receive_data_chunk(raw_data, start)


def _declared_length(request) -> int:
    try:
        return int(request.META.get("CONTENT_LENGTH") or 0)
    except ValueError:
        return 0


@csrf_exempt
@never_cache
@require_http_methods(["GET", "POST"])
@permission_required("members.cluber_import.run")
def cluber_preview_view(request):
    handler = _OneFileInMemory(request)
    request.upload_handlers = [handler]  # abans que res llegeixi el POST
    if request.method == "POST" and _declared_length(request) > BODY_CEILING:
        return _page(request, reception="too_large", status=413)
    try:
        return _protected(request, handler)
    except MultiPartParserError:
        return _page(request, reception="unreadable", status=400)


@csrf_protect
def _protected(request, handler):
    if request.method == "GET":
        return _page(request)
    files = request.FILES.getlist(FIELD)
    problem = handler.problem
    if problem is None and len(files) != 1:
        problem = "no_file" if not files else "too_many_files"
    if problem:
        _record(request, problem)
        status = 413 if problem == "too_large" else 400
        return _page(request, reception=problem, status=status, recorded=True)

    data = files[0].read()
    summary = cluber.preview(data).summary()
    rejected = summary["rejected"]
    sha256 = None if rejected == "iban_column" else hashlib.sha256(data).hexdigest()
    _record(request, rejected, summary["counts"], sha256)
    return _page(request, summary=summary, recorded=True)


def _record(request, rejected, counts=None, sha256=None):
    details = {"rejected": rejected, "counts": counts or {}}
    if sha256:
        details["file_sha256"] = sha256
    audit.record(audit.Action.CLUBER_PREVIEW, actor=request.user, details=details, request=request)


def _page(request, *, summary=None, reception=None, status=200, recorded=False):
    context = {
        "summary": summary,
        "reception": RECEPTION_MESSAGES.get(reception),
        "recorded": recorded,
    }
    if summary:
        context.update(_display(summary))
    return render(request, "members/cluber_preview.html", context, status=status)


def _display(summary):
    """Textos per a la pantalla, només a partir del resum segur (codis, files i columnes)."""
    messages = cluber.MESSAGES
    problems = []
    pending = Counter()
    for row in summary["rows"]:
        for kind, codes in ((_("Error"), row["errors"]), (_("Advertiment"), row["warnings"])):
            columns = row["error_columns"] if codes is row["errors"] else [""] * len(codes)
            for code, column in zip(codes, columns, strict=True):
                if column:
                    label = column
                elif code == "identity_conflict":
                    label = RELATION
                else:
                    label = WHOLE_ROW
                problems.append((row["row"], label, kind, messages[code]))
        pending.update(row["pending"])
    return {
        "rejection": messages.get(summary["rejected"]) if summary["rejected"] else None,
        "file_warnings": [messages[code] for code in summary["warnings"]],
        "problems": problems,
        "pending": [(messages[code], count) for code, count in sorted(pending.items())],
        "omitted": sorted(summary["catalogue_omitted"].items()),
    }
