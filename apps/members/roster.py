"""Llistat, fitxa i exportació de socis (T-M01-15; HU-M01-05, HU-M01-06; RN-M01-71, CA-M01-64).

Només lectura: aquí no s'escriu cap dada de socis. Què veu cada compte (decisió 059):
- P4 (`members.list`) amb abast «all»: totes les dades de la fitxa; amb «read_minimal» (tresorer),
  només número, nom, tipus, estat, quota i historial d'estats i tipus (wireframe aprovat).
- C1 (`members.field.birth_date`, protegit): la data de naixement a la fitxa i el filtre «sense
  data de naixement» (T-M01-33; RN-M01-48, RN-M01-55). Sense C1, la fitxa només diu «major
  d'edat», «menor d'edat» o «edat desconeguda» (`persons.age_band`) i el filtre no existeix.
- C2 (`members.field.identity`): document, adreça i consentiments.
- P10 (`members.fees.view`): l'estat de la quota.
- P11 (`members.export`): exportar, amb les mateixes restriccions de camp que la fitxa.
El llistat i l'exportació mai no porten la data de naixement (RN-M01-48, RN-M01-71).
"""

import codecs
import csv
import io
from dataclasses import dataclass
from datetime import date

import xlsxwriter
from django import forms
from django.db.models import Prefetch, Q, Value
from django.db.models.functions import Concat
from django.utils.translation import gettext_lazy as _

from apps.core.models import Charge, Person
from apps.core.normalization import normalize_document
from apps.core.permission_catalog import SCOPE_ALL
from apps.core.permissions import has_perm

from . import validity
from .fee_rules import local_today
from .models import AnnualFee, Member, MemberRequest, MembershipType

LIST = "members.list"  # P4
EXPORT = "members.export"  # P11
FEES = "members.fees.view"  # P10
IDENTITY = "members.field.identity"  # C2
BIRTH_DATE = "members.field.birth_date"  # C1


@dataclass(frozen=True)
class Visibility:
    full: bool  # P4 amb abast «all»: contacte, data d'alta i antiguitat
    identity: bool  # C2: document, adreça i consentiments
    birth_date: bool  # C1: data de naixement i filtre «sense data»
    fees: bool  # P10: estat de la quota


def visibility_for(user, perms) -> Visibility:
    """`perms` ja ha passat per `require_perm(…, LIST)`."""
    full = perms.get(LIST) == SCOPE_ALL
    return Visibility(
        full=full,
        identity=full and has_perm(user, IDENTITY, permissions=perms),
        birth_date=full and has_perm(user, BIRTH_DATE, permissions=perms),
        fees=has_perm(user, FEES, permissions=perms),
    )


# --- Filtres (HU-M01-05) ------------------------------------------------------------------


class MemberFilterForm(forms.Form):
    q = forms.CharField(label=_("Cerca"), required=False, max_length=100)
    tipus = forms.ChoiceField(label=_("Tipus"), required=False)
    estat = forms.ChoiceField(label=_("Estat del soci"), required=False)

    def __init__(self, data, *, can_search_document, can_see_birth_date=False):
        super().__init__(data)
        if can_see_birth_date:  # sense C1 el camp no existeix: un valor enviat no filtra
            self.fields["sense_data"] = forms.BooleanField(
                label=_("Només els que no tenen data de naixement"), required=False
            )
        self.fields["q"].label = (
            _("Cerca per nom, número o document")
            if can_search_document
            else _("Cerca per nom o número")
        )
        types = MembershipType.objects.order_by("name").values_list("code", "name")
        self.fields["tipus"].choices = [("", _("Tots")), *types]
        self.fields["estat"].choices = [("", _("Tots")), *Member.Status.choices]


def filtered_members(data, *, can_search_document, can_see_birth_date=False):
    """Socis segons els filtres vàlids. La cerca per document només per a qui pot veure'l (C2):
    sense C2, un document escrit a la cerca no troba ningú per aquesta via. El filtre «sense data
    de naixement», només amb C1. Una persona anonimitzada no surt en cap llistat, cerca ni
    exportació (spec 00, CA-19.2; T-M01-22)."""
    members = Member.objects.select_related("person", "type").filter(
        person__status=Person.Status.ACTIVE
    )
    if data.get("tipus"):
        members = members.filter(type__code=data["tipus"])
    if data.get("estat"):
        members = members.filter(status=data["estat"])
    if can_see_birth_date and data.get("sense_data"):
        members = members.filter(person__birth_date__isnull=True)
    text = (data.get("q") or "").strip()
    if text:
        members = members.annotate(
            full_name=Concat("person__first_name", Value(" "), "person__last_name")
        )
        match = Q(full_name__icontains=text)
        if text.isdigit():
            match |= Q(member_number=int(text))
        if can_search_document and normalize_document(text):
            match |= Q(person__id_document_number=normalize_document(text))
        members = members.filter(match)
    return members.order_by("member_number", "person__last_name", "person__first_name", "pk")


# --- Estat de la quota (decisió 070; càlcul únic de la 079, RN-M01-86) ----------------------


@dataclass(frozen=True)
class FeeState:
    kind: str  # PAID_UNTIL, PENDING o EXEMPT
    until: date | None = None


PAID_UNTIL = "paid_until"
PENDING = "pending"
EXEMPT = "exempt"


twelve_months_after = validity.twelve_months_after  # el càlcul és a `validity.py` (079)


def with_fee_data(members):
    """Precàrrega per a `fee_state`: les quotes anuals amb el càrrec i els pagaments, i les
    sol·licituds d'alta aprovades (data declarada, només per saber si és exempt; no es mostra)."""
    return members.prefetch_related(
        Prefetch(
            "fees",
            queryset=AnnualFee.objects.filter(kind=AnnualFee.Kind.ANNUAL)
            .select_related("charge")
            .prefetch_related("charge__payments"),
            to_attr="annual_fees",
        ),
        Prefetch(
            "person__member_requests",
            queryset=MemberRequest.objects.filter(
                kind=MemberRequest.Kind.JOIN, status=MemberRequest.Status.APPROVED
            ).order_by("-created_at", "-id"),
            to_attr="approved_joins",
        ),
    )


def fee_state(member, today: date | None = None) -> FeeState | None:
    """Estat de la quota amb el càlcul únic de «vàlid fins al» (079, A-02; RN-M01-86): el
    llistat, la fitxa i la revisió de quotes diuen el mateix que el carnet. `member` ve de
    `with_fee_data`.

    - Pagaments parcials (els terminis, sense regla aprovada: P-61, T-M01-49): no es mostra res.
    - «Sense quota»: el «vàlid fins al» vigent surt de l'exempció per edat (068, Q-002).
    - «Pagada fins al»: té un «vàlid fins al» que no ha passat (pagament confirmat o renovació
      de Cluber), encara que la renovació ja estigui emesa i pendent.
    - «Pendent»: no té cap «vàlid fins al» vigent i té una quota anual amb el càrrec pendent i
      el venciment passat, o una amb el càrrec retornat.
    - La resta (cap quota, una de pendent que encara no ha vençut, anul·lades): res.

    L'impagat no surt d'aquí: és la marca manual del tresorer (RN-M01-09, 040).
    """
    today = today or local_today()
    if validity.has_partial_payments(member):
        return None
    until = validity.valid_until(member)
    if until is not None and today <= until:
        if validity.exempt_now(member, today):
            return FeeState(EXEMPT)
        return FeeState(PAID_UNTIL, until)
    for fee in member.annual_fees:
        status = fee.charge.status
        if status == Charge.Status.RETURNED:
            return FeeState(PENDING)
        if status == Charge.Status.PENDING and fee.due_on < today:
            return FeeState(PENDING)
    return None


# --- Exportació (RN-M01-71, CA-M01-64) ------------------------------------------------------

# Valors que un full de càlcul pot interpretar com a fórmula (decisió 1.2) i, a més, el
# tabulador i el retorn de carro (OWASP, «CSV Injection»).
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def csv_cell(value) -> str:
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(FORMULA_PREFIXES) else text


def export_columns(vis: Visibility) -> list[tuple[str, str]]:
    columns = [
        ("number", _("Número")),
        ("name", _("Nom i cognoms")),
        ("type", _("Tipus")),
        ("status", _("Estat")),
    ]
    if vis.full:
        columns += [
            ("joined_on", _("Data d'alta")),
            ("email", _("Correu")),
            ("phone", _("Telèfon")),
        ]
    if vis.identity:
        columns += [("document", _("Document")), ("address", _("Adreça"))]
    return columns


def document_label(person) -> str:
    if not person.id_document_number:
        return ""
    return f"{person.get_id_document_type_display()} {person.id_document_number}"


def export_row(member, columns) -> list[str]:
    """Els valors tal com són, en text. Cada format els protegeix a la seva manera (`to_csv`,
    `to_xlsx`): el contingut és el mateix als dos."""
    person = member.person
    values = {
        "number": member.member_number,
        "name": str(person),
        "type": member.type.name,
        "status": member.get_status_display(),
        "joined_on": member.joined_on.strftime("%d/%m/%Y") if member.joined_on else "",
        "email": person.contact_email,
        "phone": person.phone,
        "document": document_label(person),
        "address": person.address,
    }
    return ["" if values[key] is None else str(values[key]) for key, _label in columns]


def to_csv(headers, rows) -> bytes:
    """UTF-8 amb BOM i «;», com el perfil CSV de la T-M01-24: l'Excel en català llegeix bé els
    accents i separa les columnes. Les fórmules possibles porten un apòstrof davant."""
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";")
    for row in [headers, *rows]:
        writer.writerow([csv_cell(value) for value in row])
    return codecs.BOM_UTF8 + out.getvalue().encode("utf-8")


def to_xlsx(headers, rows) -> bytes:
    """Un full, totes les cel·les com a text (format «@» i prefix de text): cap fórmula, cap
    número ni data deduïts, cap zero inicial perdut. Sense macros ni enllaços. En memòria."""
    out = io.BytesIO()
    book = xlsxwriter.Workbook(
        out,
        {
            "in_memory": True,
            "strings_to_formulas": False,
            "strings_to_numbers": False,
            "strings_to_urls": False,
        },
    )
    sheet = book.add_worksheet(str(_("Socis")))
    # 49 = format integrat «Text» («@») de l'Excel.
    text = book.add_format({"num_format": 49, "quote_prefix": True})
    header = book.add_format({"num_format": 49, "quote_prefix": True, "bold": True})
    for col, label in enumerate(headers):
        longest = max([len(label), *(len(row[col]) for row in rows)])
        sheet.set_column(col, col, min(max(longest, 8), 48) + 2, text)
        sheet.write_string(0, col, str(label), header)
    for r, row in enumerate(rows, start=1):
        for col, value in enumerate(row):
            sheet.write_string(r, col, value, text)
    sheet.freeze_panes(1, 0)
    book.close()
    return out.getvalue()


# Format → (tipus de contingut, extensió, escriptor). L'ordre és el de la llista de la pantalla.
FORMATS = {
    "xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xlsx",
        to_xlsx,
    ),
    "csv": ("text/csv; charset=utf-8", "csv", to_csv),
}


class ExportForm(MemberFilterForm):
    format = forms.ChoiceField(
        label=_("Format"),
        choices=[("xlsx", _("Excel (.xlsx)")), ("csv", _("CSV (.csv)"))],
    )
