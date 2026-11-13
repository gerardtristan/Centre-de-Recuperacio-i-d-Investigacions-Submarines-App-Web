"""Administració: importació de l'extracte bancari (T-M00-01; M9 `core.bank_statement.import`;
spec 00, HU-21). Sense wireframe propi: només components existents (`design-system.md`, §6.7).

- Sense M9, «no trobat» (059), abans de llegir cap fitxer. Ruta d'administració, amb TOTP.
- La pujada es llegeix sempre en memòria i fins a `MAX_BYTES`: mai cap fitxer temporal (RN-101).
  La vista exterior és exempta de CSRF només perquè el gestor de pujada es pugui canviar abans
  que el CSRF llegeixi el POST (com la prova de Cluber); `_upload` sí que està protegida.
- Confirmar i desfer són POST amb CSRF; desfer demana un motiu. El servei torna a comprovar M9.
"""

import datetime

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.uploadhandler import MemoryFileUploadHandler, StopUpload
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods, require_POST

from ..charges import euros
from ..files import IMPORT_TYPES, validate_upload
from ..imports import bank_statement
from ..imports.bank_statement import PERMISSION, Rejected
from ..models import ImportBatch
from ..permissions import permission_required

FIELD = "fitxer"
HISTORY = 20


def _signed(cents):
    return None if cents is None else f"{'+' if cents >= 0 else '−'}{euros(abs(cents))}"


class _InMemory(MemoryFileUploadHandler):
    """Sempre en memòria, sigui quina sigui la mida declarada, i com a molt `MAX_BYTES`."""

    too_large = False
    received = 0

    def handle_raw_input(self, *args, **kwargs):
        self.activated = True

    def receive_data_chunk(self, raw_data, start):
        self.received += len(raw_data)
        if self.received > bank_statement.MAX_BYTES:
            self.too_large = True
            raise StopUpload(connection_reset=False)
        return super().receive_data_chunk(raw_data, start)


def _page(request, *, preview=None, error=None, status=200):
    batches = ImportBatch.objects.filter(kind=ImportBatch.Kind.BANK_STATEMENT)
    context = {
        "preview": preview,
        "error": error,
        "batches": batches.select_related("created_by").order_by("-created_at")[:HISTORY],
        "profile": settings.BANK_STATEMENT_CSV_PROFILE,
    }
    return render(request, "core/bank_statement.html", context, status=status)


@csrf_exempt
@never_cache
@permission_required(PERMISSION)
@require_http_methods(["GET", "POST"])
def bank_statement_view(request):
    handler = _InMemory(request)
    request.upload_handlers = [handler]  # abans que res llegeixi el POST
    return _upload(request, handler)


@csrf_protect
def _upload(request, handler):
    if request.method == "GET":
        return _page(request)
    files = request.FILES.getlist(FIELD)
    if handler.too_large:
        return _page(request, error=_("El fitxer supera la mida màxima d'1 MB."), status=413)
    if len(files) != 1:
        return _page(request, error=_("Tria un sol fitxer CSV."), status=400)
    try:
        validate_upload(files[0], allowed=IMPORT_TYPES)
        preview = bank_statement.preview(files[0].read(), by=request.user, request=request)
    except ValidationError as exc:
        return _page(request, error=exc.messages[0], status=400)
    except Rejected as exc:
        return _page(request, error=exc.message, status=400)
    for line in preview["lines"]:
        line["shown"] = {
            "date": line.get("date") and datetime.date.fromisoformat(line["date"]),
            "amount": _signed(line.get("amount")),
            "balance": line.get("balance") is not None and euros(line["balance"]),
            "errors": [bank_statement.LINE_MESSAGES[code] for code in line["codes"]],
        }
    return _page(request, preview=preview)


@never_cache
@permission_required(PERMISSION)
@require_POST
def bank_statement_confirm_view(request):
    try:
        bank_statement.confirm(
            request.POST.get("testimoni", ""),
            by=request.user,
            exclude_errors=request.POST.get("exclou_errors") == "1",
            request=request,
        )
    except Rejected as exc:
        return _page(request, error=exc.message, status=400)
    messages.success(request, _("Extracte importat: les línies noves ja es poden conciliar."))
    return redirect("administration:bank_statement")


@never_cache
@permission_required(PERMISSION)
@require_POST
def bank_statement_undo_view(request, pk):
    batch = get_object_or_404(ImportBatch, pk=pk, kind=ImportBatch.Kind.BANK_STATEMENT)
    try:
        bank_statement.undo(
            batch, by=request.user, reason=request.POST.get("motiu", ""), request=request
        )
    except Rejected as exc:
        return _page(request, error=exc.message, status=400)
    messages.success(request, _("Extracte desfet: les seves línies ja no surten a la conciliació."))
    return redirect("administration:bank_statement")
