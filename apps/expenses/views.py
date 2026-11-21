"""Pantalles de les despeses (T-M09-06, part sense fitxer, i T-M09-15; P-M09-A; RN-M09-09;
CA-M09-01). Sense permís, «no trobat»: ho comproven el decorador i els serveis.

- **Despesa nova** (MG1): formulari d'una columna, pensat per al mòbil. La factura s'adjuntarà amb
  la T-M09-25 (tipus de fitxer privat i xifratge, 051): fins llavors, la despesa neix «sense
  factura» i en surt l'avís (CA-M09-01).
- **Sense factura** (MG2, consulta): les despeses vives sense factura, la més antiga primer.
"""

from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core.charges import euros
from apps.core.models import Department
from apps.core.permission_catalog import SCOPE_ALL
from apps.core.permissions import require_perm

from . import services
from .models import ExpenseCategory, Supplier

WITHOUT_INVOICE_URL = "administration:expenses_without_invoice"


def _euros(label, *, required=True):
    return forms.DecimalField(
        label=label, required=required, min_value=Decimal("0"), max_digits=11, decimal_places=2,
        localize=True,
    )  # fmt: skip


class ExpenseForm(forms.Form):
    supplier = forms.ModelChoiceField(
        label=gettext_lazy("Proveïdor"), queryset=Supplier.objects.filter(active=True)
    )
    invoice_number = forms.CharField(
        label=gettext_lazy("Número de factura"), max_length=40, required=False
    )
    invoice_date = forms.DateField(
        label=gettext_lazy("Data de la factura"),
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    category = forms.ModelChoiceField(
        label=gettext_lazy("Categoria"), queryset=ExpenseCategory.objects.filter(active=True)
    )
    description = forms.CharField(label=gettext_lazy("Descripció"), max_length=200)
    amount = _euros(gettext_lazy("Import (€)"))
    tax = _euros(gettext_lazy("IVA (€), si en porta"), required=False)
    department = forms.ModelChoiceField(
        label=gettext_lazy("Departament"), queryset=Department.objects.order_by("name")
    )


def _cents(value):
    return None if value is None else int(value * 100)


@never_cache
@require_http_methods(["GET", "POST"])
def new_view(request):
    # MG1 amb l'abast «tot»: amb «les seves activitats» cal el repartiment (com el menú).
    if require_perm(request, services.RECORD, write=True) != SCOPE_ALL:
        raise Http404
    form = ExpenseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = dict(form.cleaned_data)
        data["amount_cents"], data["tax_cents"] = (
            _cents(data.pop("amount")),
            _cents(data.pop("tax")),
        )
        try:
            expense = services.record_expense(by=request.user, **data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(
                request,
                _("Despesa registrada (%(amount)s). Queda «sense factura» fins que s'adjunti.")
                % {"amount": euros(expense.amount_cents)},
            )
            return redirect(WITHOUT_INVOICE_URL)
    return render(request, "expenses/new.html", {"form": form})


@never_cache
@require_http_methods(["GET"])
def without_invoice_view(request):
    require_perm(request, services.PAY)
    rows = services.without_invoice().select_related("supplier", "department")
    rows = [
        {"expense": row, "amount": euros(row.amount_cents)}
        for row in rows.order_by("invoice_date", "pk")
    ]
    return render(request, "expenses/without_invoice.html", {"rows": rows})
