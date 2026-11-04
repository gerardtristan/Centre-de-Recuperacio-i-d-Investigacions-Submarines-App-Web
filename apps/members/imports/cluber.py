"""Importació de Cluber, fase de prova (T-M01-24; P-M01-G, passos 1 a 3).

`preview(data)` llegeix l'exportació en CSV, la valida i en torna el resum. Precisions aplicades
(docs/planning.md, lectura de les tasques substituïdes, files de la T-M01-24):

- No escriu res: a la base de dades només fa consultes de lectura (tres com a màxim), i no
  escriu a la sessió, al disc ni a la cua. El registre de l'execució, el permís (P18) i la
  presentació del resum són del punt d'entrada que la cridi, que encara no existeix.
- Perfil CSV inicial, no confirmat per Q-23: UTF-8 amb BOM opcional, separador «;», cometes del
  mòdul `csv`, 1 MiB, 2.000 registres de dades i 10.000 caràcters per camp. Sense heurístiques.
- Una columna d'IBAN (capçalera «iban» normalitzada, sense àlies) rebutja el fitxer sencer en
  llegir la capçalera, abans de cap fila (RN-94, CA-M01-21).
- Cap equivalència aprovada per al tipus de soci, l'estat ni la data d'alta: cap fila no és
  preparada per importar, i aquestes dades surten com a pendents. No s'inventa res.
- Els errors porten la fila, la columna i un codi, mai cap valor del fitxer. Els valors de les
  columnes de catàleg sí que surten al resum: informació no fiable i potencialment personal, que
  no va als registres. Les columnes que no s'utilitzen es llegeixen (cal processar la fila) però
  el seu valor no passa al resultat.

La fila (`row`) és el número de registre, amb la capçalera com a 1: un camp de diverses línies
compta com una sola fila, com en un full de càlcul.
"""

import csv
import io
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

from apps.core.models import Person
from apps.core.normalization import normalize_document, normalize_email, normalize_phone
from apps.members.models import Member

MAX_BYTES = 1024 * 1024
MAX_ROWS = 2000
MAX_FIELD = 10_000
# Més valors diferents que aquests i la columna no es tracta com un catàleg: només el recompte.
MAX_CATALOGUE = 50
MAX_MEMBER_NUMBER = 2_147_483_647  # rang de PositiveIntegerField a PostgreSQL

# Capçaleres de la mostra parcial del 04/11/2026, sense la d'IBAN (no substitueix S-M01-16).
KNOWN_HEADERS = (
    "Nº Soci",
    "Nom",
    "Cognoms",
    "Telèfon",
    "Document d'Identitat",
    "Quota",
    "Preu total",
    "Estat",
    "Soci titular",
    "Email",
    "Data alta/renovació",
    "Mètode de pagament",
    "Adreça",
    "Codi Postal",
    "Ciutat",
    "Província",
    "Renovació",
    "Polítiques de privadesa",
    "Informació addicional",
    "Identificador",
    "Sector seient",
    "Fila seient",
    "Seient nº",
    "Data d'inscripció",
    "Data de Naixament",
    "Edat",
    "Telèfon fix",
    "Professió;",
    "Titulacio;",
    "Especialitats;",
    "idInterno",
    "CONSENTIMIENTO PARA USO DE IMÁGENES: Autorizo a la publicación de imágenes en redes "
    "sociales y página web del club/entidad. El club/entidad usará las imágenes solo para los "
    "fines autorizados y no las compartirá con terceros.",
)
IBAN_HEADERS = frozenset({"iban"})  # comparació exacta normalitzada; cap àlies aprovat

# Concepte → capçalera. Només les correspondències directes; la resta de columnes és pendent.
NUMBER = "Nº Soci"
FIRST_NAME = "Nom"
LAST_NAME = "Cognoms"
DOCUMENT = "Document d'Identitat"
EMAIL = "Email"
PHONE = "Telèfon"
ADDRESS = "Adreça"
REQUIRED_HEADERS = (NUMBER, FIRST_NAME, LAST_NAME, DOCUMENT)
CATALOGUE_HEADERS = ("Quota", "Estat", "Renovació")
# Sense cap equivalència aprovada (S-M01-16, Q-23): pendents a totes les files.
UNMAPPED = ("member_type", "member_status", "joined_on")

_NUMBER_RE = re.compile(r"[0-9]+")

MESSAGES = {
    # Fitxer sencer
    "too_large": _("El fitxer supera la mida màxima."),
    "encoding": _("El fitxer no és UTF-8."),
    "empty": _("El fitxer és buit."),
    "malformed": _("El fitxer no té un format CSV vàlid."),
    "iban_column": _(
        "El fitxer té una columna d'IBAN i es rebutja sencer. Exporta'l sense aquesta columna."
    ),
    "duplicate_header": _("Hi ha una capçalera repetida."),
    "missing_header": _("Falta una columna obligatòria."),
    "no_rows": _("El fitxer no té cap fila de dades."),
    "too_many_rows": _("El fitxer supera el nombre màxim de files."),
    "no_document_type": _("El fitxer no indica el tipus de document."),
    "unknown_columns": _("Hi ha columnes que no es reconeixen i no es fan servir."),
    # Errors de fila
    "field_count": _("La fila no té el mateix nombre de camps que la capçalera."),
    "field_too_long": _("Un camp supera la llargada màxima."),
    "member_number_invalid": _("El número de soci no és un enter positiu vàlid."),
    "email_invalid": _("El correu no té un format vàlid."),
    "duplicate_document": _("El document es repeteix en una altra fila del fitxer."),
    "duplicate_member_number": _("El número de soci es repeteix en una altra fila del fitxer."),
    "identity_conflict": _("El document i el número de soci apunten a persones diferents."),
    # Advertiments de fila
    "member_number_leading_zeros": _("El número de soci té zeros a l'esquerra."),
    "match_without_document_type": _("Coincidència sense tipus de document."),
    # Dades pendents
    "member_type": _("Tipus de soci sense equivalència aprovada."),
    "member_status": _("Estat del soci sense equivalència aprovada."),
    "joined_on": _("Data d'alta sense equivalència aprovada."),
    "id_document_type": _("Falta el tipus de document."),
    "member_number": _("Falta el número de soci."),
    "first_name": _("Falta el nom."),
    "last_name": _("Falten els cognoms."),
    "id_document": _("Falta el document."),
    "email": _("Falta el correu."),
    "phone": _("Falta el telèfon."),
}


@dataclass
class Row:
    row: int
    data: dict = field(default_factory=dict)
    # Identitat: "new", "matching", "ambiguous", "conflict"; None si la fila no s'ha pogut llegir.
    identity: str | None = None
    person_id: int | None = None
    member_id: int | None = None
    errors: list = field(default_factory=list)
    error_columns: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    pending: list = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return not self.errors and not self.pending and self.identity in ("new", "matching")

    def _error(self, code, column):
        self.errors.append(code)
        self.error_columns.append(column)


@dataclass
class Preview:
    rejected: str | None = None
    rejected_column: str = ""
    rejected_row: int | None = None
    rows: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    unknown_columns: list = field(default_factory=list)
    catalogue: dict = field(default_factory=dict)

    @property
    def counts(self) -> dict:
        identities = Counter(r.identity for r in self.rows)
        return {
            "rows": len(self.rows),
            "new": identities["new"],
            "matching": identities["matching"],
            "ambiguous": identities["ambiguous"],
            "conflict": identities["conflict"],
            "with_errors": sum(1 for r in self.rows if r.errors),
            "ready": sum(1 for r in self.rows if r.ready),
        }


def _reject(code, *, column="", row=None) -> Preview:
    return Preview(rejected=code, rejected_column=column, rejected_row=row)


def preview(data: bytes) -> Preview:
    """Valida l'exportació de Cluber sense escriure res i en torna el resum."""
    # La mida es comprova abans de descodificar: res no creix més que el fitxer acotat.
    if len(data) > MAX_BYTES:
        return _reject("too_large")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _reject("encoding")
    if not text.strip():
        return _reject("empty")

    # El lector va registre a registre: no es llegeix cap fila abans de validar la capçalera.
    # El límit propi del mòdul csv (131.072 caràcters) no es toca perquè és global del procés:
    # un camp que el supera fa rebutjar el fitxer com a «malformed».
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=";", strict=True)
    try:
        headers = [h.strip() for h in next(reader)]
    except csv.Error:
        return _reject("malformed", row=1)

    if any(h.lower() in IBAN_HEADERS for h in headers):
        return _reject("iban_column")
    repeated = [h for h, n in Counter(headers).items() if n > 1]
    if repeated:
        return _reject("duplicate_header", column=repeated[0])
    for required in REQUIRED_HEADERS:
        if required not in headers:
            return _reject("missing_header", column=required)

    result = Preview(warnings=["no_document_type"])
    result.unknown_columns = [h for h in headers if h not in KNOWN_HEADERS]
    if result.unknown_columns:
        result.warnings.append("unknown_columns")
    index = {h: i for i, h in enumerate(headers)}
    catalogue = {h: Counter() for h in CATALOGUE_HEADERS if h in index}

    row_number = 1
    try:
        for values in reader:
            if not values:  # línia buida
                continue
            row_number += 1
            if len(result.rows) == MAX_ROWS:
                return _reject("too_many_rows")
            row = Row(row=row_number)
            result.rows.append(row)
            if len(values) != len(headers):
                row._error("field_count", "")
                continue
            too_long = [headers[i] for i, v in enumerate(values) if len(v) > MAX_FIELD]
            if too_long:
                for column in too_long:
                    row._error("field_too_long", column)
                continue
            _read_row(row, {h: values[i].strip() for h, i in index.items()})
            for column, counter in catalogue.items():
                if value := values[index[column]].strip():
                    counter[value] += 1
    except csv.Error:
        return _reject("malformed", row=row_number + 1)

    if not result.rows:
        return _reject("no_rows")
    result.catalogue = {
        column: dict(counter) if len(counter) <= MAX_CATALOGUE else len(counter)
        for column, counter in catalogue.items()
    }
    _mark_duplicates(result.rows)
    _match(result.rows)
    return result


def _read_row(row: Row, values: dict) -> None:
    """Copia només les columnes utilitzades; la resta no passa al resultat."""
    number_text = values[NUMBER]
    document_text = values[DOCUMENT]
    email = values.get(EMAIL, "")
    row.data = {
        "member_number_text": number_text,
        "first_name": values[FIRST_NAME],
        "last_name": values[LAST_NAME],
        "id_document_text": document_text,
        "id_document": normalize_document(document_text),
        "email": normalize_email(email),
        "phone": normalize_phone(values.get(PHONE, "")),
        "address": values.get(ADDRESS, ""),
    }

    if not number_text:
        row.pending.append("member_number")
    elif _NUMBER_RE.fullmatch(number_text) and 1 <= int(number_text) <= MAX_MEMBER_NUMBER:
        row.data["member_number"] = int(number_text)
        if number_text.startswith("0"):
            row.warnings.append("member_number_leading_zeros")
    else:
        row._error("member_number_invalid", NUMBER)

    if email:
        try:
            validate_email(email)
        except ValidationError:
            row._error("email_invalid", EMAIL)

    for key in ("first_name", "last_name", "email", "phone"):
        if not row.data[key]:
            row.pending.append(key)
    if row.data["id_document"]:
        row.pending.append("id_document_type")
    else:
        row.pending.append("id_document")
    row.pending.extend(UNMAPPED)


def _mark_duplicates(rows: list) -> None:
    """Dins del fitxer, un document o un número repetit és error a totes les files (L-M01-06)."""
    for key, code, column in (
        ("id_document", "duplicate_document", DOCUMENT),
        ("member_number", "duplicate_member_number", NUMBER),
    ):
        seen = Counter(r.data[key] for r in rows if r.data.get(key))
        for row in rows:
            if seen[row.data.get(key)] > 1:
                row._error(code, column)


def _match(rows: list) -> None:
    """Coincidències amb la base de dades (RN-95): només lectures, cap fusió ni assignació.

    El document es compara només pel número normalitzat, amb persones actives de qualsevol
    tipus, perquè l'exportació no porta el tipus: per això no es fa servir `find_duplicates`.
    """
    readable = [r for r in rows if r.data]
    documents = {r.data["id_document"] for r in readable if r.data["id_document"]}
    numbers = {r.data["member_number"] for r in readable if "member_number" in r.data}

    by_document = defaultdict(list)
    if documents:
        people = Person.objects.filter(
            status=Person.Status.ACTIVE, id_document_number__in=documents
        ).values_list("id_document_number", "pk")
        for document, pk in people:
            by_document[document].append(pk)
    by_number = {}
    if numbers:
        members = Member.objects.filter(member_number__in=numbers).values_list(
            "member_number", "pk", "person_id", "person__id_document_number"
        )
        by_number = {number: (pk, person, doc) for number, pk, person, doc in members}
    member_of = {}
    single = {pks[0] for pks in by_document.values() if len(pks) == 1}
    if single:
        members = Member.objects.filter(person_id__in=single).values_list(
            "person_id", "pk", "member_number"
        )
        member_of = {person: (pk, number) for person, pk, number in members}

    for row in readable:
        document = row.data["id_document"]
        number = row.data.get("member_number")
        people = by_document.get(document, []) if document else []
        if len(people) > 1:
            row.identity = "ambiguous"
            continue
        person = people[0] if people else None
        by_num = by_number.get(number) if number else None
        own_member = member_of.get(person)
        conflict = (
            (person and by_num and by_num[1] != person)
            or (person and not by_num and number and own_member and own_member[1] is not None)
            or (by_num and not person and document and by_num[2] and by_num[2] != document)
        )
        if conflict:
            row.identity = "conflict"
            row._error("identity_conflict", DOCUMENT)
        elif person or by_num:
            row.identity = "matching"
            row.person_id = person or by_num[1]
            row.member_id = by_num[0] if by_num else own_member and own_member[0]
            if person:
                row.warnings.append("match_without_document_type")
        else:
            row.identity = "new"
