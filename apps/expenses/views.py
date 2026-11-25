"""Pantalles de les despeses (T-M09-06, part sense fitxer, i T-M09-15; P-M09-A; RN-M09-09;
CA-M09-01). Sense permís, «no trobat»: ho comproven el decorador i els serveis.

- **Despesa nova** (MG1): formulari d'una columna, pensat per al mòbil. La factura s'adjuntarà amb
  la T-M09-25 (tipus de fitxer privat i xifratge, 051): fins llavors, la despesa neix «sense
  factura» i en surt l'avís (CA-M09-01).
- **Sense factura** (MG2, consulta): les despeses vives sense factura, la més antiga primer.
- **Documents d'una despesa** (T-M09-04b, 05 i 15; RN-M09-25): adjuntar la factura (MG1) o el
  comprovant del banc (MG2), i, per al tresorer (MG2 i C5), marcar-los il·legibles i pujar-ne la
  còpia emmascarada. Obrir-los és la vista `private_file` (C5, amb registre). Els serveis
  (`documents.py`) tornen a comprovar-ho tot.
"""

from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core.charges import euros
from apps.core.models import Department
from apps.core.permission_catalog import SCOPE_ALL
from apps.core.permissions import has_perm, request_permissions, require_perm, scope_for

from . import documents, services
from .models import DocumentIllegibleMark, Expense, ExpenseCategory, Supplier

WITHOUT_INVOICE_URL = "administration:expenses_without_invoice"


def _euros(label, *, required=True):
    return forms.DecimalField(
        label=label, required=required, min_value=Decimal("0"), max_digits=11, decimal_places=2,
        localize=True,
    )  # fmt: skip


class ExpenseForm(forms.Form):
    supplier = forms.ModelChoiceField(
        label=gettext_lazy("Proveïdor"),
        queryset=Supplier.objects.filter(active=True),
        empty_label=gettext_lazy("Tria un proveïdor"),
    )
    invoice_number = forms.CharField(
        label=gettext_lazy("Número de factura"), max_length=40, required=False
    )
    invoice_date = forms.DateField(
        label=gettext_lazy("Data de la factura"),
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    category = forms.ModelChoiceField(
        label=gettext_lazy("Categoria"),
        queryset=ExpenseCategory.objects.filter(active=True),
        empty_label=gettext_lazy("Tria una categoria"),
    )
    description = forms.CharField(label=gettext_lazy("Descripció"), max_length=200)
    amount = _euros(gettext_lazy("Import (€)"))
    tax = _euros(gettext_lazy("IVA (€), si en porta"), required=False)
    department = forms.ModelChoiceField(
        label=gettext_lazy("Departament"),
        queryset=Department.objects.order_by("name"),
        empty_label=gettext_lazy("Tria un departament"),
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
            # Sense MG2 no es veu «Despeses sense factura»: va als documents per adjuntar-hi la
            # factura (CA-M09-27).
            if has_perm(request.user, services.PAY):
                return redirect(WITHOUT_INVOICE_URL)
            return redirect("administration:expense_documents", expense.pk)
    return render(request, "expenses/new.html", {"form": form})


class DepartmentFilterForm(forms.Form):
    """Filtre per departament de «Despeses sense factura» (T-DX-107): només els que hi surten."""

    departament = forms.ChoiceField(label=gettext_lazy("Departament"), required=False)

    def __init__(self, data, departments):
        super().__init__(data)
        self.fields["departament"].choices = [("", _("Tots"))] + [
            (str(d.pk), str(d)) for d in departments
        ]


@never_cache
@require_http_methods(["GET"])
def without_invoice_view(request):
    require_perm(request, services.PAY)
    expenses = list(
        services.without_invoice()
        .select_related("supplier", "department")
        .order_by("invoice_date", "pk")
    )
    totals = {}  # departament → cèntims (Gastos, T-DX-107): l'anell mostra tota la llista
    for expense in expenses:
        totals[expense.department] = totals.get(expense.department, 0) + expense.amount_cents
    form = DepartmentFilterForm(request.GET, sorted(totals, key=str))
    chosen = form.cleaned_data["departament"] if form.is_valid() else ""
    shown = [e for e in expenses if not chosen or str(e.department_id) == chosen]
    rows = [
        {
            "expense": row,
            "amount": euros(row.amount_cents),
            "illegible": row.invoice_file_id is not None,  # sense factura amb fitxer: il·legible
        }
        for row in shown
    ]
    context = {
        "rows": rows,
        "form": form,
        "filtered": bool(chosen),
        "total": euros(sum(e.amount_cents for e in shown)),
        "segments": [(str(d), cents) for d, cents in totals.items()],
        "can_record": has_perm(request.user, services.RECORD, write=True),
    }
    return render(request, "expenses/without_invoice.html", context)


Document = DocumentIllegibleMark.Document
# Document → permís per pujar-lo (com `documents._FIELDS`).
UPLOAD_PERMISSION = {Document.INVOICE: services.RECORD, Document.PAYMENT_PROOF: services.PAY}
DONE = {
    "attach": gettext_lazy("Document desat. Només l'obren el tresorer i la junta."),
    "masked": gettext_lazy("Còpia emmascarada desada."),
    "illegible": gettext_lazy("Document marcat com a il·legible. Qui l'havia pujat en rep l'avís."),
}


def _post_documents(request, expense):
    document, action = request.POST.get("document"), request.POST.get("action")
    if document not in UPLOAD_PERMISSION or action not in DONE:
        raise Http404
    uploaded = request.FILES.get("fitxer")
    try:
        if action == "illegible":
            reason = request.POST.get("motiu", "")
            documents.mark_illegible(expense, document, reason=reason, by=request.user,
                                     request=request)  # fmt: skip
        elif uploaded is None:
            raise ValidationError(_("Tria un fitxer."))
        elif action == "attach":
            documents.attach(expense, document, uploaded, by=request.user, request=request)
        else:
            documents.attach_masked_copy(expense, document, uploaded, by=request.user,
                                         request=request)  # fmt: skip
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, DONE[action])


@never_cache
@require_http_methods(["GET", "POST"])
def documents_view(request, pk):
    perms = request_permissions(request)
    can = {code: scope_for(request.user, code, permissions=perms) == SCOPE_ALL
           for code in (services.RECORD, services.PAY)}  # fmt: skip
    if not any(can.values()):
        raise Http404
    expense = get_object_or_404(Expense.objects.select_related("supplier", "department"), pk=pk)
    if request.method == "POST":
        _post_documents(request, expense)
        return redirect("administration:expense_documents", expense.pk)
    can_open = has_perm(request.user, documents.OPEN_DOCUMENTS, permissions=perms)
    live = expense.status != Expense.Status.ANNULLED
    rows = []
    for document, permission in UPLOAD_PERMISSION.items():
        file = getattr(expense, f"{document}_file")
        illegible = file is not None and documents.illegible(expense, document)
        rows.append({
            "code": document,
            "label": Document(document).label,
            "file": file,
            "illegible": illegible,
            "masked": file is not None and documents.masking_status(expense, document) == "masked",
            "can_upload": live and can[permission] and (file is None or illegible),
        })  # fmt: skip
    context = {
        "expense": expense,
        "amount": euros(expense.amount_cents),
        "rows": rows,
        "can_open": can_open,
        # «Despeses sense factura» s'obre amb MG2, també «Cons.»: la mateixa comprovació que la
        # redirecció després de registrar una despesa.
        "can_list": has_perm(request.user, services.PAY, permissions=perms),
        "treasurer": live and can[services.PAY] and can_open,
        "accept": ",".join(sorted(documents.DOCUMENT_TYPES)),
    }
    return render(request, "expenses/documents.html", context)
