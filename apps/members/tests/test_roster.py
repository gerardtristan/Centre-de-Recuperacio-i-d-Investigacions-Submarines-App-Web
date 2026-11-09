"""Llistat, fitxa i exportació de socis (T-M01-15; P4, P10, P11, C2; RN-M01-71, CA-M01-64).

Permisos segons la configuració inicial de la 059, visibilitat per camp, CSV, estat de la quota
(070 i decisió 1.3 del 09/11/2026) i que cap vista ni exportació no porta la data de naixement.
Només dades inventades.
"""

import codecs
import csv
import io
import time
import zipfile
from datetime import UTC, date, datetime
from unittest import mock
from xml.etree import ElementTree as ET  # noqa: N817 (nom habitual)

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import audit, charges, consents
from apps.core.models import AuditEntry, Charge, Payment, Person, PrivateFile, RolePermission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import roster
from apps.members.models import (
    AnnualFee,
    Member,
    MemberRequest,
    MembershipType,
    MemberStatusChange,
)
from conftest import PASSWORD

LIST = "administration:members_list"
DETAIL = "administration:member_detail"
EXPORT = "administration:members_export"
EXPORTED = "members.list.exported"

# Dades sentinella: si surten on no toca, la prova ho detecta.
EMAIL = "sentinella.correu@example.org"
PHONE = "+34600111222"
DOCUMENT = "SENTINELLADOC1"
ADDRESS = "Carrer Sentinella 9"
BIRTH = date(2014, 7, 7)  # menor: exempt fins al 31/12/2028 (068)
BIRTH_TEXTS = ("07/07/2014", "2014-07-07", "7 de juliol")

SEES_ALL = ["secretary", "administrator"]
NO_ACCESS = [
    "president",
    "board",
    "instructor",
    "courses_manager",
    "equipment_manager",
    "history_department",
]


def admin_client(account, *, csrf=False):
    client = Client(enforce_csrf_checks=csrf)
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_ADMIN
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


def make_member(number, first="Anna", last="Mero", *, type_code="full", status="active", **person):
    fields = {"origin": Person.Origin.IN_PERSON, **person}
    p = Person.objects.create(first_name=first, last_name=last, **fields)
    return Member.objects.create(
        person=p,
        member_number=number,
        type=MembershipType.objects.get(code=type_code),
        status=status,
        joined_on=date(2019, 3, 12),
    )


def add_fee(member, *, period=2026, kind=AnnualFee.Kind.ANNUAL, cents=9000):
    charge = charges.create_charge(
        member.person,
        kind=Charge.Kind.FEE,
        amount_cents=cents,
        concept="Quota de prova",
        origin="members",
        by=audit.system("proves"),
    )
    AnnualFee.objects.create(
        member=member, period=period, kind=kind, charge=charge, due_on=date(period, 1, 1)
    )
    return charge


def pay(charge, paid_at, *, amount=None, confirm=True):
    payment = Payment.objects.create(
        charge=charge,
        method=Payment.Method.CARD,
        amount_cents=amount or charge.amount_cents,
        paid_at=paid_at,
    )
    if confirm:
        charges.mark_paid(charge, payment, origin="provider", by=audit.system("proves"))
    return payment


def approved_join(member, birth_date):
    return MemberRequest.objects.create(
        kind=MemberRequest.Kind.JOIN,
        person=member.person,
        member=member,
        requested_type=member.type,
        channel=MemberRequest.Channel.WEB,
        status=MemberRequest.Status.APPROVED,
        birth_date=birth_date,
    )


def state(member, today=date(2026, 11, 9)):
    loaded = roster.with_fee_data(Member.objects.filter(pk=member.pk)).get()
    return roster.fee_state(loaded, today)


FORMATS = ["xlsx", "csv"]
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
TEXT_FORMAT_ID = "49"  # format de nombre «@» (text) de l'Office Open XML


def export(client, fmt="csv", **data):
    return client.post(reverse(EXPORT), {"format": fmt, **data})


def read_csv(response):
    assert response.content.startswith(codecs.BOM_UTF8)
    body = response.content.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(body), delimiter=";"))


def _column(ref):
    letters = "".join(ch for ch in ref if ch.isalpha())
    index = 0
    for ch in letters:
        index = index * 26 + ord(ch) - ord("A") + 1
    return index - 1


def read_xlsx(response):
    """Llegeix l'.xlsx només amb la biblioteca estàndard (zipfile i XML). De pas comprova que no hi
    ha macros ni enllaços externs, que cap cel·la és una fórmula i que totes són text, amb el
    format de text i el prefix de text."""
    book = zipfile.ZipFile(io.BytesIO(response.content))
    names = set(book.namelist())
    assert not any("vbaProject" in n or "externalLink" in n for n in names)
    assert "xl/calcChain.xml" not in names  # cap fórmula al llibre

    def xml(name):
        # L'XML és el que acaba de generar el nostre codi en aquesta prova, no dades de fora.
        return ET.fromstring(book.read(name))  # noqa: S314

    shared = []
    if "xl/sharedStrings.xml" in names:
        for item in xml("xl/sharedStrings.xml").findall("m:si", NS):
            shared.append("".join(t.text or "" for t in item.iter(f"{{{NS['m']}}}t")))
    xfs = xml("xl/styles.xml").find("m:cellXfs", NS).findall("m:xf", NS)
    rows = []
    sheet = xml("xl/worksheets/sheet1.xml")
    for row in sheet.find("m:sheetData", NS).findall("m:row", NS):
        values = {}
        for cell in row.findall("m:c", NS):
            assert cell.find("m:f", NS) is None, "cap cel·la no pot ser una fórmula"
            xf = xfs[int(cell.get("s", "0"))]
            assert xf.get("numFmtId") == TEXT_FORMAT_ID and xf.get("quotePrefix") == "1"
            value = cell.find("m:v", NS)
            if value is None:
                values[_column(cell.get("r"))] = ""
                continue
            assert cell.get("t") == "s", "només text: mai número, data ni booleà"
            values[_column(cell.get("r"))] = shared[int(value.text)]
        rows.append([values.get(i, "") for i in range(max(values) + 1)] if values else [])
    return rows


def read_export(response, fmt):
    return read_xlsx(response) if fmt == "xlsx" else read_csv(response)


def as_text(response, fmt=None):
    if fmt == "xlsx":
        return "\n".join(";".join(row) for row in read_xlsx(response))
    return response.content.decode("utf-8")


def remove_permission(role, code):
    RolePermission.objects.filter(role__code=role, permission_code=code).delete()


@pytest.fixture
def full_member(db):
    member = make_member(
        427,
        "Marta",
        "Puig",
        contact_email=EMAIL,
        phone=PHONE,
        address=ADDRESS,
        id_document_type=Person.DocumentType.PASSPORT,
        id_document_number=DOCUMENT,
    )
    approved_join(member, BIRTH)  # data declarada a l'alta: mai a cap pantalla ni al CSV
    return member


# --- Permisos per rol (059; CA-M01-24 per a P4 i P11) -------------------------------------


@pytest.mark.parametrize("role", SEES_ALL)
def test_secretary_and_administrator_see_list_detail_and_export(make_admin, full_member, role):  # noqa: F811
    client = admin_client(make_admin(role))
    assert client.get(reverse(LIST)).status_code == 200
    assert client.get(reverse(DETAIL, args=[full_member.pk])).status_code == 200
    for fmt in FORMATS:
        assert export(client, fmt).status_code == 200


def test_treasurer_reads_but_cannot_export(make_admin, full_member):  # noqa: F811
    client = admin_client(make_admin("treasurer"))
    assert client.get(reverse(LIST)).status_code == 200
    assert client.get(reverse(DETAIL, args=[full_member.pk])).status_code == 200
    for fmt in FORMATS:
        assert export(client, fmt).status_code == 404
    assert not AuditEntry.objects.filter(action=EXPORTED).exists()


@pytest.mark.parametrize("role", [*NO_ACCESS, None])
def test_other_roles_get_not_found_everywhere(make_admin, full_member, role):  # noqa: F811
    client = admin_client(make_admin(role) if role else make_admin())
    assert client.get(reverse(LIST)).status_code == 404
    assert client.get(reverse(DETAIL, args=[full_member.pk])).status_code == 404
    for fmt in FORMATS:
        assert export(client, fmt).status_code == 404
    assert client.get(reverse(EXPORT)).status_code == 404  # sense permís, ni el mètode


def test_unknown_member_is_the_same_not_found(make_admin, full_member):  # noqa: F811
    client = admin_client(make_admin("secretary"))
    assert client.get(reverse(DETAIL, args=[full_member.pk + 999])).status_code == 404


def test_export_only_by_post(make_admin, full_member):  # noqa: F811
    response = admin_client(make_admin("secretary")).get(reverse(EXPORT))
    assert response.status_code == 405
    assert not AuditEntry.objects.filter(action=EXPORTED).exists()


def test_list_and_detail_only_by_get(make_admin, full_member):  # noqa: F811
    client = admin_client(make_admin("secretary"))
    assert client.post(reverse(LIST)).status_code == 405
    assert client.post(reverse(DETAIL, args=[full_member.pk])).status_code == 405


@pytest.mark.parametrize("fmt", FORMATS)
def test_export_needs_csrf_token(make_admin, full_member, fmt):  # noqa: F811
    client = admin_client(make_admin("secretary"), csrf=True)
    assert export(client, fmt).status_code == 403
    client.get(reverse(LIST))
    token = client.cookies["csrftoken"].value
    assert export(client, fmt, csrfmiddlewaretoken=token).status_code == 200


@pytest.mark.parametrize("value", [None, "", "pdf", "XLSX", "xls", "csv;", "xlsx csv"])
def test_invalid_or_tampered_format_is_rejected(make_admin, full_member, value):  # noqa: F811
    data = {} if value is None else {"format": value}
    response = admin_client(make_admin("secretary")).post(reverse(EXPORT), data)
    assert response.status_code == 400
    assert "attachment" not in response.get("Content-Disposition", "")
    assert EMAIL.encode() not in response.content
    assert not AuditEntry.objects.filter(action=EXPORTED).exists()


def test_two_format_values_are_rejected(make_admin, full_member):  # noqa: F811
    # Un camp repetit: Django en pren l'últim, que també ha de ser vàlid.
    client = admin_client(make_admin("secretary"))
    response = client.post(reverse(EXPORT), {"format": ["csv", "pdf"]})
    assert response.status_code == 400


def test_export_button_opens_a_list_with_both_formats(make_admin, full_member):  # noqa: F811
    # «Exporta» és el resum d'un <details> natiu (sense JavaScript); a dins, un botó d'enviament
    # per format, amb el mateix camp `format` que valida el servidor.
    page = admin_client(make_admin("secretary")).get(reverse(LIST)).content.decode()
    form = page[page.index(f'action="{reverse(EXPORT)}"') :]
    form = form[: form.index("</form>")]
    assert '<details class="menu-exporta">' in form and "<details open" not in form
    assert '<summary class="boto">Exporta' in form
    xlsx = '<button class="boto boto-petit" type="submit" name="format" value="xlsx">Excel (.xlsx)'
    csv_button = '<button class="boto boto-petit" type="submit" name="format" value="csv">CSV'
    assert xlsx in form and csv_button in form
    assert form.index("<summary") < form.index(xlsx) < form.index(csv_button)
    assert "<select" not in form
    # Millora progressiva (Esc, clic fora, sortir amb Tab): un fitxer propi, cap codi en línia.
    assert '<script src="/static/js/menu-exporta.js" defer></script>' in page
    assert "<script>" not in page


def test_without_session_goes_to_admin_login(client, full_member):
    for response in (
        client.get(reverse(LIST)),
        client.get(reverse(DETAIL, args=[full_member.pk])),
        export(client),
    ):
        assert response.status_code == 302
        assert reverse("administration:login") in response["Location"]


def test_personal_session_does_not_reach_the_admin_screens(login_as, make_person, full_member):
    account = Account.objects.create_personal(make_person(), "soci@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    client = login_as(account, AREA_PERSONAL)
    for response in (
        client.get(reverse(LIST)),
        client.get(reverse(DETAIL, args=[full_member.pk])),
        export(client, "xlsx"),
    ):
        assert response.status_code == 302
        assert reverse("administration:login") in response["Location"]
        assert EMAIL.encode() not in response.content


def test_permissions_are_data_removing_p4_closes_list_and_export(make_admin, full_member):  # noqa: F811
    client = admin_client(make_admin("secretary"))
    remove_permission("secretary", "members.list")
    assert client.get(reverse(LIST)).status_code == 404
    assert client.get(reverse(DETAIL, args=[full_member.pk])).status_code == 404
    for fmt in FORMATS:  # s'exporta el que es pot llistar
        assert export(client, fmt).status_code == 404


def test_removing_p11_hides_the_button_and_closes_export(make_admin, full_member):  # noqa: F811
    client = admin_client(make_admin("secretary"))
    remove_permission("secretary", "members.export")
    page = client.get(reverse(LIST)).content.decode()
    assert reverse(EXPORT) not in page and 'name="format"' not in page
    assert "menu-exporta.js" not in page
    for fmt in FORMATS:
        assert export(client, fmt).status_code == 404


def test_home_links_to_the_list_only_with_p4(make_admin, full_member):  # noqa: F811
    url = f'href="{reverse(LIST)}"'  # amb l'atribut: «Altes pendents» (T-M01-14) hi comença igual
    home = reverse("administration:home")
    assert url in admin_client(make_admin("secretary")).get(home).content.decode()
    assert url not in admin_client(make_admin("president")).get(home).content.decode()


# --- Visibilitat (P4 «dades mínimes», C2, P10; RN-M01-48) ---------------------------------


def test_treasurer_sees_only_minimal_data(make_admin, full_member):  # noqa: F811
    client = admin_client(make_admin("treasurer"))
    for url in (reverse(LIST), reverse(DETAIL, args=[full_member.pk])):
        page = client.get(url).content.decode()
        assert "Marta Puig" in page
        assert "427" in page
        assert "Ple dret" in page and "Actiu" in page
        for hidden in (EMAIL, PHONE, DOCUMENT, ADDRESS, "12/03/2019", "Consentiments"):
            assert hidden not in page
    assert "Exporta" not in client.get(reverse(LIST)).content.decode()


def test_secretary_sees_the_whole_file(make_admin, full_member):  # noqa: F811
    page = admin_client(make_admin("secretary")).get(reverse(DETAIL, args=[full_member.pk]))
    text = page.content.decode()
    for shown in (EMAIL, PHONE, DOCUMENT, ADDRESS, "12/03/2019", "Anys de soci"):
        assert shown in text


def test_without_c2_no_document_address_or_consents(make_admin, full_member):  # noqa: F811
    client = admin_client(make_admin("secretary"))
    remove_permission("secretary", "members.field.identity")
    text = client.get(reverse(DETAIL, args=[full_member.pk])).content.decode()
    assert EMAIL in text and PHONE in text
    for hidden in (DOCUMENT, ADDRESS, "Consentiments"):
        assert hidden not in text
    for fmt in FORMATS:
        rows = read_export(export(client, fmt), fmt)
        assert rows[0] == [
            "Número",
            "Nom i cognoms",
            "Tipus",
            "Estat",
            "Data d'alta",
            "Correu",
            "Telèfon",
        ]
        assert DOCUMENT not in str(rows) and ADDRESS not in str(rows)


def test_without_p10_no_fee_state(make_admin, full_member):  # noqa: F811
    pay(add_fee(full_member), datetime(2026, 11, 10, 10, tzinfo=UTC))
    client = admin_client(make_admin("secretary"))
    assert "Pagada fins al" in client.get(reverse(LIST)).content.decode()
    remove_permission("secretary", "members.fees.view")
    for url in (reverse(LIST), reverse(DETAIL, args=[full_member.pk])):
        text = client.get(url).content.decode()
        assert "Pagada fins al" not in text and ">Quota<" not in text


@pytest.mark.parametrize("role", ["secretary", "administrator", "treasurer"])
def test_request_birth_date_never_shown_nor_exported(make_admin, full_member, role):  # noqa: F811
    """La data declarada a la sol·licitud no surt enlloc; la de la persona (T-M01-33), només a
    la fitxa amb C1 (`test_birth_date.py`). L'exportació mai no en parla (RN-M01-71)."""
    client = admin_client(make_admin(role))
    texts = [
        as_text(client.get(reverse(LIST))),
        as_text(client.get(reverse(DETAIL, args=[full_member.pk]))),
    ]
    exports = [] if role == "treasurer" else [as_text(export(client, f), f) for f in FORMATS]
    for text in texts + exports:
        for value in BIRTH_TEXTS:
            assert value not in text
    for text in exports:
        assert "naixement" not in text.lower()


def test_document_search_only_with_c2(make_admin, full_member):  # noqa: F811
    make_member(500, "Biel", "Rap")
    search = {"q": DOCUMENT.lower()}
    secretary = admin_client(make_admin("secretary")).get(reverse(LIST), search)
    assert "Marta Puig" in secretary.content.decode()
    treasurer = admin_client(make_admin("treasurer")).get(reverse(LIST), search)
    assert "Marta Puig" not in treasurer.content.decode()
    assert "Cerca per nom o número" in treasurer.content.decode()


# --- Llistat: filtres i missatge sense socis (HU-M01-05, L-M01-08) ------------------------


def test_filters_by_type_status_name_and_number(make_admin, full_member):  # noqa: F811
    make_member(501, "Pau", "Llobarro", type_code="supporter", status="left")
    make_member(502, "Laia", "Dorada", status="unpaid")
    client = admin_client(make_admin("secretary"))

    def names(**params):
        text = client.get(reverse(LIST), params).content.decode()
        return {n for n in ("Marta Puig", "Pau Llobarro", "Laia Dorada") if n in text}

    assert names() == {"Marta Puig", "Pau Llobarro", "Laia Dorada"}
    assert names(tipus="supporter") == {"Pau Llobarro"}
    assert names(estat="unpaid") == {"Laia Dorada"}
    assert names(q="puig") == {"Marta Puig"}
    assert names(q="marta puig") == {"Marta Puig"}
    assert names(q="502") == {"Laia Dorada"}
    assert names(estat="inventat") == {"Marta Puig", "Pau Llobarro", "Laia Dorada"}


def test_empty_club_message_with_links_by_permission(make_admin):  # noqa: F811
    admin_page = admin_client(make_admin("administrator")).get(reverse(LIST)).content.decode()
    assert "Encara no hi ha socis" in admin_page
    assert reverse("administration:cluber_preview") in admin_page
    assert reverse("administration:join_in_person") in admin_page
    secretary = admin_client(make_admin("secretary")).get(reverse(LIST)).content.decode()
    assert reverse("administration:join_in_person") in secretary
    assert reverse("administration:cluber_preview") not in secretary
    treasurer = admin_client(make_admin("treasurer")).get(reverse(LIST)).content.decode()
    assert "Encara no hi ha socis" in treasurer
    assert "Importa'ls" not in treasurer


def test_no_results_message(make_admin, full_member):  # noqa: F811
    page = admin_client(make_admin("secretary")).get(reverse(LIST), {"q": "ningú"})
    assert "Cap soci coincideix" in page.content.decode()


# --- Fitxa: historial i consentiments (HU-M01-06; Q-044, opció 1) --------------------------


def test_history_newest_first_with_author_and_reason(make_admin, full_member):  # noqa: F811
    secretary = make_admin("secretary", username="anna.secretaria")
    full = MembershipType.objects.get(code="full")
    MemberStatusChange.objects.create(
        member=full_member, from_status="", to_status="pending", to_type=full,
        effective_on=date(2019, 3, 12), actor_account=secretary,
        created_at=timezone.make_aware(datetime(2019, 3, 12, 18, 30)),
    )  # fmt: skip
    MemberStatusChange.objects.create(
        member=full_member, from_status="active", to_status="unpaid", from_type=full,
        to_type=full, effective_on=date(2025, 2, 3), reason="Quota retornada pel banc",
        created_at=timezone.make_aware(datetime(2025, 2, 3, 10, 40)),
    )  # fmt: skip
    text = admin_client(make_admin("treasurer")).get(reverse(DETAIL, args=[full_member.pk]))
    text = text.content.decode()
    assert "Estat: Impagat (abans Actiu)" in text
    assert "motiu: Quota retornada pel banc" in text
    assert "Sistema" in text and "anna.secretaria" in text
    assert text.index("Impagat (abans") < text.index("Estat inicial: Pendent")


def test_consents_show_the_last_state_of_each_text(make_admin, full_member):  # noqa: F811
    admin = make_admin("administrator")
    consents.publish_text("privacy", "Text de prova.", by=admin)
    consents.publish_text("newsletter", "Text de prova.", by=admin)
    consents.grant(full_member.person, "privacy", channel="web")
    consents.grant(full_member.person, "newsletter", channel="web")
    consents.withdraw(full_member.person, "newsletter", channel="web")
    text = admin_client(admin).get(reverse(DETAIL, args=[full_member.pk])).content.decode()
    block = text[text.index("Consentiments") :]
    assert "privacy" in block and "Atorgat" in block
    assert "newsletter" in block and "Retirat" in block


# --- Exportació (RN-M01-71, CA-M01-64) ------------------------------------------------------


HEADERS = [
    "Número", "Nom i cognoms", "Tipus", "Estat", "Data d'alta",
    "Correu", "Telèfon", "Document", "Adreça",
]  # fmt: skip
ROW = [
    "427", "Marta Puig", "Ple dret", "Actiu", "12/03/2019",
    EMAIL, PHONE, f"Passaport {DOCUMENT}", ADDRESS,
]  # fmt: skip


def test_xlsx_columns_values_headers_and_file_name(make_admin, full_member):  # noqa: F811
    response = export(admin_client(make_admin("secretary")), "xlsx")
    assert response["Content-Type"] == XLSX_TYPE
    assert response["Content-Disposition"] == (
        f'attachment; filename="socis-{roster.local_today():%Y-%m-%d}.xlsx"'
    )
    assert read_xlsx(response) == [HEADERS, ROW]


def test_csv_columns_values_headers_and_file_name(make_admin, full_member):  # noqa: F811
    response = export(admin_client(make_admin("secretary")), "csv")
    assert response["Content-Type"] == "text/csv; charset=utf-8"
    assert response["Content-Disposition"] == (
        f'attachment; filename="socis-{roster.local_today():%Y-%m-%d}.csv"'
    )
    # El telèfon comença per «+»: al CSV porta l'apòstrof de protecció (RN-M01-71).
    assert read_csv(response) == [HEADERS, [*ROW[:6], "'" + PHONE, *ROW[7:]]]


def test_both_formats_have_the_same_content(make_admin, full_member):  # noqa: F811
    make_member(501, "Pau", "Llobarro", type_code="supporter", status="left", phone="0034600")
    make_member(2, "=1+1", "Prova", address="@SUM(A1)")
    client = admin_client(make_admin("secretary"))
    xlsx = read_xlsx(export(client, "xlsx"))
    csv_rows = read_csv(export(client, "csv"))
    assert len(xlsx) == len(csv_rows) == 4
    # Mateixos valors; el CSV només hi afegeix l'apòstrof de protecció.
    assert csv_rows == [[roster.csv_cell(value) for value in row] for row in xlsx]


def test_xlsx_keeps_leading_zeros_and_never_numbers(make_admin, db):  # noqa: F811
    make_member(
        7, "Zero", "Inicial", phone="0034 600 000 007",
        id_document_type=Person.DocumentType.DNI, id_document_number="00000007L",
    )  # fmt: skip
    rows = read_xlsx(export(admin_client(make_admin("secretary")), "xlsx"))
    assert rows[1][0] == "7"  # el número també és text
    assert rows[1][6] == "0034600000007"
    assert rows[1][7] == "DNI 00000007L"
    assert rows[1][4] == "12/03/2019"  # la data d'alta, text i no una data de l'Excel


@pytest.mark.parametrize("fmt", FORMATS)
def test_export_is_never_cached_nor_stored(make_admin, full_member, fmt):  # noqa: F811
    client = admin_client(make_admin("secretary"))
    with mock.patch("django.core.files.storage.default_storage.save") as save:
        response = export(client, fmt)
    cache_control = response["Cache-Control"]
    assert "no-store" in cache_control and "private" in cache_control
    save.assert_not_called()
    assert not PrivateFile.objects.exists()


def test_csv_neutralises_formulas(make_admin, db):  # noqa: F811
    make_member(1, '=HYPERLINK("http://x")', "-2+3", address="@SUM(A1)")
    rows = read_csv(export(admin_client(make_admin("secretary")), "csv"))
    name, address = rows[1][1], rows[1][8]
    assert name.startswith("'=HYPERLINK")
    assert address == "'@SUM(A1)"


def test_xlsx_formula_like_values_are_plain_text(make_admin, db):  # noqa: F811
    make_member(1, '=HYPERLINK("http://x")', "-2+3", address="@SUM(A1)")
    make_member(3, "Tab", "Prova", address="\tCMD")
    # `read_xlsx` falla si alguna cel·la és una fórmula o no és text amb el format de text.
    rows = read_xlsx(export(admin_client(make_admin("secretary")), "xlsx"))
    assert rows[1][1] == '=HYPERLINK("http://x") -2+3'
    assert rows[1][8] == "@SUM(A1)"
    assert rows[2][8] == "\tCMD"


@pytest.mark.parametrize("value", ["=1+1", "+34", "-5", "@A1", "\tx", "\rx"])
def test_csv_cell_prefixes_every_formula_start(value):
    assert roster.csv_cell(value) == "'" + value


@pytest.mark.parametrize("value", ["Anna", "", "1=1", None, 427])
def test_csv_cell_leaves_other_values(value):
    assert roster.csv_cell(value) == ("" if value is None else str(value))


@pytest.mark.parametrize("fmt", FORMATS)
def test_export_follows_the_list_filters(make_admin, full_member, fmt):  # noqa: F811
    make_member(501, "Pau", "Llobarro", status="left")
    client = admin_client(make_admin("secretary"))
    rows = read_export(export(client, fmt, estat="left"), fmt)
    assert [r[1] for r in rows[1:]] == ["Pau Llobarro"]


@pytest.mark.parametrize("fmt", FORMATS)
def test_export_audit_keeps_only_filters_rows_and_format(make_admin, full_member, fmt):  # noqa: F811
    export(admin_client(make_admin("secretary")), fmt, q="Marta", tipus="full", estat="active")
    entry = AuditEntry.objects.get(action=EXPORTED)
    assert entry.details == {
        "filters": {
            "type": "full",
            "status": "active",
            "search": True,
            "without_birth_date": False,
        },
        "rows": 1,
        "format": fmt,
    }
    assert entry.target_type == "" and entry.field == ""
    stored = f"{entry.details} {entry.old_value} {entry.new_value} {entry.reason}"
    for personal in ("Marta", "Puig", EMAIL, PHONE, DOCUMENT, ADDRESS):
        assert personal not in stored


# --- Estat de la quota (070; decisió 1.3) -------------------------------------------------


def test_paid_until_is_twelve_months_after_the_confirmed_payment(full_member):
    pay(add_fee(full_member), datetime(2026, 11, 10, 9, tzinfo=UTC))
    assert state(full_member) == roster.FeeState(roster.PAID_UNTIL, date(2027, 11, 10))


def test_paid_until_uses_the_local_date(full_member):
    # 31/12/2026 23:30 UTC ja és l'1/1/2027 a Barcelona.
    pay(add_fee(full_member), datetime(2026, 12, 31, 23, 30, tzinfo=UTC))
    assert state(full_member).until == date(2028, 1, 1)


def test_twenty_ninth_of_february_ends_on_the_last_day_of_february():
    assert roster.twelve_months_after(date(2028, 2, 29)) == date(2029, 2, 28)
    assert roster.twelve_months_after(date(2027, 3, 31)) == date(2028, 3, 31)


def test_latest_confirmed_payment_wins(full_member):
    pay(add_fee(full_member, period=2025), datetime(2025, 5, 1, 9, tzinfo=UTC))
    pay(add_fee(full_member, period=2026), datetime(2026, 5, 3, 9, tzinfo=UTC))
    assert state(full_member).until == date(2027, 5, 3)


def test_pending_fee(full_member):
    add_fee(full_member)
    assert state(full_member) == roster.FeeState(roster.PENDING)


def test_exempt_minor_without_fee(full_member):
    assert state(full_member) == roster.FeeState(roster.EXEMPT)


def test_minor_who_already_pays_is_not_exempt(full_member):
    # Any de naixement 2014: comença a pagar el 2029 (068).
    assert state(full_member, today=date(2029, 1, 1)) is None


def test_no_fee_and_not_exempt_shows_nothing(db):
    adult = make_member(9, "Oriol", "Sard")
    assert state(adult) is None
    approved_join(adult, date(1980, 1, 1))
    assert state(adult) is None


def test_partial_payments_show_nothing(full_member):
    # Tres pagaments de 32 € (070): sense comportament aprovat (P-61).
    charge = add_fee(full_member, cents=9600)
    pay(charge, datetime(2026, 1, 10, tzinfo=UTC), amount=3200, confirm=False)
    assert state(full_member) is None  # el càrrec continua pendent, però no es diu «pendent»
    pay(charge, datetime(2026, 3, 10, tzinfo=UTC), amount=3200, confirm=False)
    pay(charge, datetime(2026, 5, 10, tzinfo=UTC), amount=3200)
    assert state(full_member) is None


def test_paid_charge_with_two_payments_or_without_date_shows_nothing(full_member):
    charge = add_fee(full_member)
    pay(charge, None)
    assert state(full_member) is None
    other = make_member(10, "Clara", "Pop")
    charge = add_fee(other)
    pay(charge, datetime(2026, 1, 1, tzinfo=UTC), confirm=False)
    pay(charge, datetime(2026, 1, 2, tzinfo=UTC))
    assert state(other) is None


def test_cancelled_only_shows_nothing(full_member):
    charges.cancel(add_fee(full_member), "Prova", by=audit.system("proves"))
    assert state(full_member) is None


def test_type_change_supplement_is_not_the_annual_fee(full_member):
    add_fee(full_member, kind=AnnualFee.Kind.TYPE_CHANGE_SUPPLEMENT, cents=5500)
    assert state(full_member) == roster.FeeState(roster.EXEMPT)


def test_fee_state_on_screen(make_admin, full_member):  # noqa: F811
    pending = make_member(11, "Jordi", "Rap")
    add_fee(pending)
    paid = make_member(12, "Núria", "Serrà")
    pay(add_fee(paid), datetime(2026, 11, 10, 9, tzinfo=UTC))
    text = admin_client(make_admin("treasurer")).get(reverse(LIST)).content.decode()
    assert "Pagada fins al 10/11/2027" in text
    assert "Pendent" in text
    assert "Sense quota" in text
