"""Importació de Cluber, fase de prova (T-M01-24; P-M01-G, passos 1 a 3).

`preview(data)` llegeix l'exportació en CSV, la valida i en torna el resultat. Precisions aplicades
(docs/planning.md, lectura de les tasques substituïdes, files de la T-M01-24):

- No escriu res: a la base de dades només fa consultes de lectura (tres com a màxim), i no
  escriu a la sessió, al disc ni a la cua. El registre de l'execució, el permís (P18) i la
  presentació del resum són del punt d'entrada que la cridi, que encara no existeix.
- Perfil CSV inicial revisable, no confirmat per Q-23: UTF-8 amb BOM opcional, separador «;»,
  cometes del mòdul `csv`, 1 MiB, 2.000 registres de dades i 10.000 caràcters per camp.
- Una columna d'IBAN (capçalera «iban» normalitzada, sense àlies) rebutja el fitxer sencer en
  llegir la capçalera, abans de cap fila (RN-94, CA-M01-21). Un IBAN dins d'una altra columna no
  es detecta (risc conegut).
- Cap equivalència aprovada per al tipus de soci, l'estat ni la data d'alta: cap fila no és
  preparada per importar, i aquestes dades surten com a pendents. No s'inventa res.
- Dades en memòria: de cada fila només el document normalitzat i el número de soci (amb el text
  original), que són el que fa servir la previsualització. Les altres columnes es llegeixen
  (cal processar la fila) però el seu valor no passa al resultat. `repr` no mostra aquestes
  dades, ni els valors de catàleg, ni els noms de columna desconeguts; això no impedeix altres
  serialitzacions (`dataclasses.asdict`, `vars`, `pickle`). L'únic que es pot mostrar o
  registrar sense cap valor del fitxer és `Preview.summary()`.

La fila (`row`) és el número de registre, amb la capçalera com a 1: un camp de diverses línies
compta com una sola fila, com en un full de càlcul. Una columna que no es reconeix s'identifica
per la seva posició («#33»), perquè el seu nom ve del fitxer.
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
from apps.core.normalization import normalize_document
from apps.members.models import Member

MAX_BYTES = 1024 * 1024
MAX_ROWS = 2000
MAX_FIELD = 10_000
# Amb més valors diferents, el detall s'omet i només se'n dona el recompte.
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

NUMBER = "Nº Soci"
FIRST_NAME = "Nom"
LAST_NAME = "Cognoms"
DOCUMENT = "Document d'Identitat"
EMAIL = "Email"
PHONE = "Telèfon"
REQUIRED_HEADERS = (NUMBER, FIRST_NAME, LAST_NAME, DOCUMENT)
# Presència comprovada (si falta, queda pendent); el valor no es conserva.
PRESENCE = {FIRST_NAME: "first_name", LAST_NAME: "last_name", EMAIL: "email", PHONE: "phone"}
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


def _label(header: str, position: int) -> str:
    """Nom de la columna si és reconegut; si no, la posició, perquè el nom ve del fitxer."""
    return header if header in KNOWN_HEADERS else f"#{position + 1}"


@dataclass
class Row:
    row: int
    data: dict = field(default_factory=dict, repr=False)
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

    def summary(self) -> dict:
        return {
            "row": self.row,
            "identity": self.identity,
            "ready": self.ready,
            "errors": list(self.errors),
            "error_columns": list(self.error_columns),
            "warnings": list(self.warnings),
            "pending": list(self.pending),
        }


@dataclass
class Preview:
    rejected: str | None = None
    rejected_column: str = ""
    rejected_row: int | None = None
    rows: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    unknown_columns: list = field(default_factory=list, repr=False)
    # Valors de catàleg: no fiables i potencialment personals; fora de `repr` i de `summary()`.
    catalogue: dict = field(default_factory=dict, repr=False)
    catalogue_omitted: dict = field(default_factory=dict)

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

    def summary(self) -> dict:
        """Resum sense cap valor del fitxer: el que es pot mostrar o registrar."""
        return {
            "rejected": self.rejected,
            "rejected_column": self.rejected_column,
            "rejected_row": self.rejected_row,
            "counts": self.counts,
            "warnings": list(self.warnings),
            "unknown_columns": len(self.unknown_columns),
            "catalogue": {column: len(values) for column, values in self.catalogue.items()},
            "catalogue_omitted": dict(self.catalogue_omitted),
            "rows": [r.summary() for r in self.rows],
        }


def _reject(code, *, column="", row=None) -> Preview:
    return Preview(rejected=code, rejected_column=column, rejected_row=row)


def preview(data: bytes) -> Preview:
    """Valida l'exportació de Cluber sense escriure res i en torna el resultat."""
    # La mida es comprova abans de descodificar: el text i el lector queden acotats per 1 MiB.
    if len(data) > MAX_BYTES:
        return _reject("too_large")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _reject("encoding")
    if not text.strip():
        return _reject("empty")

    # El lector va registre a registre: no es llegeix cap fila abans de validar la capçalera.
    # El límit aprovat (MAX_FIELD) es comprova a cada fila. El límit intern del mòdul csv
    # (131.072 caràcters) no es canvia perquè afecta tot el procés: un camp que el supera fa
    # rebutjar el fitxer com a «malformed», sense res del seu contingut.
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=";", strict=True)
    try:
        headers = [h.strip() for h in next(reader)]
    except csv.Error:
        return _reject("malformed", row=1)

    if any(h.lower() in IBAN_HEADERS for h in headers):
        return _reject("iban_column")
    seen = set()
    for header in headers:
        if header in seen:
            return _reject("duplicate_header", column=_label(header, headers.index(header)))
        seen.add(header)
    for required in REQUIRED_HEADERS:
        if required not in seen:
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
            too_long = [i for i, v in enumerate(values) if len(v) > MAX_FIELD]
            if too_long:
                for i in too_long:
                    row._error("field_too_long", _label(headers[i], i))
                continue
            _read_row(row, values, index)
            for column, counter in catalogue.items():
                if value := values[index[column]].strip():
                    counter[value] += 1
    except csv.Error:
        return _reject("malformed", row=row_number + 1)

    if not result.rows:
        return _reject("no_rows")
    for column, counter in catalogue.items():
        if len(counter) <= MAX_CATALOGUE:
            result.catalogue[column] = dict(counter)
        else:
            result.catalogue_omitted[column] = len(counter)
    _mark_duplicates(result.rows)
    _match(result.rows)
    return result


def _read_row(row: Row, values: list, index: dict) -> None:
    """Valida la fila i en conserva només el document normalitzat i el número de soci."""

    def value(header):
        return values[index[header]].strip() if header in index else ""

    number_text = value(NUMBER)
    row.data = {
        "member_number_text": number_text,
        "id_document": normalize_document(value(DOCUMENT)),
    }

    # Sense els zeros de l'esquerra, i amb la llargada comprovada abans de convertir-lo: int() no
    # accepta més de 4.300 xifres i el camp en pot tenir fins a 10.000.
    significant = number_text.lstrip("0")
    if not number_text:
        row.pending.append("member_number")
    elif (
        _NUMBER_RE.fullmatch(number_text)
        and 1 <= len(significant) <= len(str(MAX_MEMBER_NUMBER))
        and int(significant) <= MAX_MEMBER_NUMBER
    ):
        row.data["member_number"] = int(significant)
        if number_text.startswith("0"):
            row.warnings.append("member_number_leading_zeros")
    else:
        row._error("member_number_invalid", NUMBER)

    if email := value(EMAIL):
        try:
            validate_email(email)
        except ValidationError:
            row._error("email_invalid", EMAIL)

    row.pending.extend(code for header, code in PRESENCE.items() if not value(header))
    row.pending.append("id_document_type" if row.data["id_document"] else "id_document")
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

    Per document: persones no anonimitzades (`Person.status` actiu), sigui quin sigui el seu
    compte o l'estat del soci; es compara només el número normalitzat, de qualsevol tipus,
    perquè l'exportació no porta el tipus (per això no es fa servir `find_duplicates`). Per
    número: tots els socis, de qualsevol estat.
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
            # El document i el número apunten a persones diferents.
            (person and by_num and by_num[1] != person)
            # El document és d'un soci amb un altre número.
            or (person and not by_num and number and own_member and own_member[1] is not None)
            # El número és d'un soci amb un altre document.
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
