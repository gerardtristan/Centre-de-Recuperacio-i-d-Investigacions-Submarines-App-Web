"""«Les meves factures» (T-M09-21; MG10, propi; M09-8 `invoicing.invoices_for`). Només les factures
emeses a nom de la persona del compte personal: mai les d'una altra (permís per objecte al
servidor, no a la plantilla). Sense descàrrega del PDF fins que es desi com a fitxer privat
(T-M09-25)."""

from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.core.charges import euros

from .models import Invoice


def invoices_for(person):
    """`invoicing.invoices_for(person)` (M09-8): les factures emeses a nom de la persona."""
    return Invoice.objects.filter(customer_person=person, status=Invoice.Status.ISSUED).order_by(
        "-issued_on", "-pk"
    )


@never_cache
@require_GET
def my_invoices_view(request):
    rows = [
        {"invoice": row, "total": euros(row.total_cents)}
        for row in invoices_for(request.user.person)
    ]
    return render(request, "invoicing/mine.html", {"rows": rows})
