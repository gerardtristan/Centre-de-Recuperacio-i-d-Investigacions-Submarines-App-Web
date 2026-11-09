"""Importació de Cluber, fase de prova (T-M01-24 i T-M01-24b; P-M01-G, passos 1 a 3).

`preview(data)` llegeix l'exportació en CSV, la valida i en torna el resultat. Precisions aplicades
(docs/planning.md, lectura de les tasques substituïdes, files de la T-M01-24; decisió 071):

- No escriu res: a la base de dades només fa consultes de lectura (cinc com a màxim: la de
  CA-20.8, la dels tipus de soci i tres de coincidències), i no escriu a la sessió, al disc ni a
  la cua. El registre de l'execució, el permís (P18) i la presentació del resum són del punt
  d'entrada que la crida (`views/admin.py`).
- Format (071): CSV separat per «;», cometes del mòdul `csv`; UTF-8 amb BOM opcional i, si no és
  UTF-8 vàlid, Windows-1252 (`Preview.encoding`). 1 MiB, 2.000 registres de dades i 10.000
  caràcters per camp.
- Una columna d'IBAN (capçalera «iban» normalitzada, sense àlies) es descarta en llegir: el seu
  valor s'esborra de cada registre abans de cap altre tractament i no passa enlloc (071, que
  matisa la RN-94 i el CA-M01-21). Un IBAN dins d'una altra columna no es detecta (risc conegut).
- Només es llegeixen les columnes d'`EQUIVALENCES` (071, punt 10); la resta s'ignoren.
- Tipus de soci per nom, per preu o pendent (071, punt 5). Tots entrarien actius (punt 7).
- Dades en memòria: de cada fila només el document normalitzat i el número de soci (amb el text
  original), que són el que fa servir la previsualització, i la llista dels camps que
  s'omplirien (`Row.fields`, sense valors). `normalize()` calcula els valors normalitzats, però
  aquí només se n'aprofiten les claus. `repr` no mostra aquestes dades, ni els valors de catàleg,
  ni els noms de columna desconeguts; això no impedeix altres serialitzacions
  (`dataclasses.asdict`, `vars`, `pickle`). L'únic que es pot mostrar o registrar sense cap valor
  del fitxer és `Preview.summary()`.

La fila (`row`) és el número de registre, amb la capçalera com a 1: un camp de diverses línies
compta com una sola fila, com en un full de càlcul. Una columna que no es reconeix s'identifica
per la seva posició («#33»), perquè el seu nom ve del fitxer.
"""

import csv
import datetime
import io
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import ImportBatch, Person
from apps.core.normalization import normalize_document
from apps.members.models import Member, MembershipType

MAX_BYTES = 1024 * 1024
MAX_ROWS = 2000
MAX_FIELD = 10_000
# Amb més valors diferents, el detall s'omet i només se'n dona el recompte.
MAX_CATALOGUE = 50
MAX_MEMBER_NUMBER = 2_147_483_647  # rang de PositiveIntegerField a PostgreSQL
DOCUMENT_MAX_LENGTH = Person._meta.get_field("id_document_number").max_length

IMAGE_CONSENT = (
    "CONSENTIMIENTO PARA USO DE IMÁGENES: Autorizo a la publicación de imágenes en redes "
    "sociales y página web del club/entidad. El club/entidad usará las imágenes solo para los "
    "fines autorizados y no las compartirá con terceros."
)
# Capçaleres de la mostra parcial del 04/11/2026, sense la d'IBAN, que a l'exportació real va
# just després de «Soci titular» i es descarta en llegir (071).
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
    IMAGE_CONSENT,
)
IBAN_HEADERS = frozenset({"iban"})  # comparació exacta normalitzada; cap àlies aprovat

NUMBER = "Nº Soci"
FIRST_NAME = "Nom"
LAST_NAME = "Cognoms"
DOCUMENT = "Document d'Identitat"
EMAIL = "Email"
PHONE = "Telèfon"
QUOTA = "Quota"
TOTAL_PRICE = "Preu total"
ADDRESS = "Adreça"
POSTAL_CODE = "Codi Postal"
CITY = "Ciutat"
BIRTH_DATE = "Data de Naixament"
JOINED_ON = "Data d'inscripció"
LAST_RENEWAL = "Data alta/renovació"
CLUBER_ID = "idInterno"


@dataclass(frozen=True)
class Equivalence:
    column: str  # capçalera de Cluber
    target: str  # camp de destinació, o què en fa la importació final
    purpose: str  # finalitat: per què es llegeix


# Taula d'equivalències (decisió 071, punt 10): les úniques columnes que es llegeixen. Afegir-ne
# una és afegir-hi una fila, el seu tractament a `normalize()` i la seva prova. Cap mode
# «importa-ho tot»: la resta (també «Estat», «Renovació», «Soci titular», «Mètode de pagament»
# i «Polítiques de privadesa») s'ignoren sense conservar-ne el valor.
EQUIVALENCES = (
    Equivalence(NUMBER, "Member.member_number", "Conservar el número de soci (RN-M01-32)."),
    Equivalence(FIRST_NAME, "Person.first_name", "Identificar la persona."),
    Equivalence(LAST_NAME, "Person.last_name", "Identificar la persona."),
    Equivalence(DOCUMENT, "Person.id_document_number", "Identificar i detectar duplicats."),
    Equivalence(EMAIL, "Person.contact_email", "Contactar i obrir el compte personal."),
    Equivalence(PHONE, "Person.phone", "Contactar; tal com ve (071, punt 16)."),
    Equivalence(BIRTH_DATE, "Person.birth_date", "Franja d'edat (058, RN-M01-55); pot ser buida."),
    Equivalence(ADDRESS, "Person.address", "Adreça postal."),
    Equivalence(POSTAL_CODE, "Person.address", "Adreça postal: codi postal."),
    Equivalence(CITY, "Person.address", "Adreça postal: ciutat; «-» és buida (071, punt 17)."),
    Equivalence(JOINED_ON, "Member.joined_on", "Antiguitat [A validar: tresorer, P-62]."),
    Equivalence(LAST_RENEWAL, "last_renewal", "Carnet provisional (RN-M01-34) [A validar]."),
    Equivalence(QUOTA, "Member.type", "Deduir el tipus per nom o per preu (071, punt 5)."),
    Equivalence(TOTAL_PRICE, "total_price", "Només informatiu; no crea cap càrrec (071, punt 6)."),
    Equivalence(CLUBER_ID, "Member.cluber_id", "Referència de Cluber per seguir el lot."),
    Equivalence(IMAGE_CONSENT, "image_consent", "Consentiment d'imatges importat de Cluber."),
)

# Noms dels camps per a la pantalla de la prova («què s'importaria»), en l'ordre de la taula.
FIELD_LABELS = {
    "Member.member_number": _("Número de soci"),
    "Person.first_name": _("Nom"),
    "Person.last_name": _("Cognoms"),
    "Person.id_document_number": _("Document"),
    "Person.contact_email": _("Correu"),
    "Person.phone": _("Telèfon"),
    "Person.birth_date": _("Data de naixement"),
    "Person.address": _("Adreça"),
    "Member.joined_on": _("Data d'alta"),
    "last_renewal": _("Última renovació (carnet provisional)"),
    "Member.cluber_id": _("Referència de Cluber"),
    "image_consent": _("Consentiment d'imatges atorgat"),
}
TYPE_BY_LABELS = {"name": _("pel nom"), "price": _("pel preu")}
ENCODING_LABELS = {"utf-8": "UTF-8", "windows-1252": "Windows-1252"}

REQUIRED_HEADERS = (NUMBER, FIRST_NAME, LAST_NAME, DOCUMENT)
# Presència comprovada (si falta, queda pendent); el valor no es conserva.
PRESENCE = {FIRST_NAME: "first_name", LAST_NAME: "last_name", EMAIL: "email", PHONE: "phone"}
CATALOGUE_HEADERS = (QUOTA,)
# Llargada dels camps de destinació: un valor més llarg és un error de fila, sense retallar-lo.
MAX_LENGTH = {
    "Person.first_name": Person._meta.get_field("first_name").max_length,
    "Person.last_name": Person._meta.get_field("last_name").max_length,
    "Person.phone": Person._meta.get_field("phone").max_length,
    "Person.address": Person._meta.get_field("address").max_length,
    "Member.cluber_id": Member._meta.get_field("cluber_id").max_length,
}
# «Sí» al consentiment d'imatges, sense majúscules ni accents. Qualsevol altre valor, o buit, és
# no atorgat [A validar: valors reals de Cluber].
YES = frozenset({"si", "s", "yes", "1", "true", "x", "acepto", "autorizo"})

_NUMBER_RE = re.compile(r"[0-9]+")
_DATE_RE = re.compile(r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})")
_PRICE_IN_TEXT_RE = re.compile(r"([0-9]+(?:[.,][0-9]{1,2})?)\s*€")
_AMOUNT_RE = re.compile(r"([0-9]+(?:[.,][0-9]{1,2})?)\s*€?")

MESSAGES = {
    # Fitxer sencer
    "too_large": _("El fitxer supera la mida màxima."),
    "encoding": _("El fitxer no és UTF-8 ni Windows-1252."),
    "empty": _("El fitxer és buit."),
    "malformed": _("El fitxer no té un format CSV vàlid."),
    "iban_discarded": _(
        "El fitxer té una columna d'IBAN: s'ha descartat sense desar-ne ni mostrar-ne cap valor."
    ),
    "duplicate_header": _("Hi ha una capçalera repetida."),
    "missing_header": _("Falta una columna obligatòria."),
    "no_rows": _("El fitxer no té cap fila de dades."),
    "too_many_rows": _("El fitxer supera el nombre màxim de files."),
    "cluber_already_imported": _("Ja hi ha una importació de Cluber confirmada."),
    "no_document_type": _("El fitxer no indica el tipus de document."),
    "unknown_columns": _("Hi ha columnes que no es reconeixen i no es fan servir."),
    # Errors de fila
    "field_count": _("La fila no té el mateix nombre de camps que la capçalera."),
    "field_too_long": _("Un camp supera la llargada màxima."),
    "member_number_invalid": _("El número de soci no és un enter positiu vàlid."),
    "email_invalid": _("El correu no té un format vàlid."),
    "date_invalid": _("La data no té el format dd/mm/aaaa, no existeix o és futura."),
    "duplicate_document": _("El document es repeteix en una altra fila del fitxer."),
    "duplicate_member_number": _("El número de soci es repeteix en una altra fila del fitxer."),
    "identity_conflict": _("El document i el número de soci apunten a persones diferents."),
    "member_number_unavailable": _(
        "El número de soci no està disponible i cal que el revisi una persona autoritzada."
    ),
    # Advertiments de fila
    "member_number_leading_zeros": _("El número de soci té zeros a l'esquerra."),
    "match_without_document_type": _("Coincidència sense tipus de document."),
    "joined_on": _("Falta la data d'alta: s'importaria igualment i la secretaria la posaria a mà."),
    "total_price_differs": _(
        "El preu total no coincideix amb la quota del tipus deduït (només informatiu)."
    ),
    # Dades pendents
    "member_type": _("No s'ha pogut deduir el tipus de soci: l'ha de triar la secretaria."),
    "id_document_type": _("Falta el tipus de document."),
    "member_number": _("Falta el número de soci."),
    "first_name": _("Falta el nom."),
    "last_name": _("Falten els cognoms."),
    "id_document": _("Falta el document."),
    "email": _("Falta el correu."),
    "phone": _("Falta el telèfon."),
}


_INVISIBLE = str.maketrans("", "", "﻿​")


def _header_key(header: str) -> str:
    """Només per comparar capçaleres (IBAN i repetides): sense U+FEFF ni U+200B, sense espais
    als extrems i en minúscules. El nom de la capçalera no es modifica per a cap altre ús."""
    return header.translate(_INVISIBLE).strip().lower()


def _label(header: str, position: int) -> str:
    """Nom de la columna si és reconegut; si no, la posició, perquè el nom ve del fitxer."""
    return header if header in KNOWN_HEADERS else f"#{position + 1}"


def _fold(text: str) -> str:
    """Sense majúscules ni accents, per comparar textos («Col·laborador» = «col·laborador»)."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def _cents(amount: str) -> int:
    return int(Decimal(amount.replace(",", ".")) * 100)


def parse_date(text: str) -> datetime.date | None:
    """dd/mm/aaaa (dia i mes d'una o dues xifres). None si no té el format o no existeix."""
    match = _DATE_RE.fullmatch(text)
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    try:
        return datetime.date(year, month, day)
    except ValueError:
        return None


def price_in_text(text: str) -> int | None:
    """Cèntims de l'únic preu en euros del text («… 35€.» → 3500); None si no n'hi ha cap o més
    d'un."""
    prices = _PRICE_IN_TEXT_RE.findall(text)
    return _cents(prices[0]) if len(prices) == 1 else None


def normalize(value) -> tuple[dict, list]:
    """Valors normalitzats de les columnes de text, dates i consentiment d'`EQUIVALENCES`.

    `value(columna)` torna el text de la cel·la sense espais als extrems ("" si no hi és). Torna
    `(camps, errors)`: `camps` té una clau per cada camp que s'ompliria; `errors`, parells
    (codi, columna) sense cap valor. El número, el document i el tipus es tracten a part. No
    s'inventa res: un valor buit o invàlid no omple el camp.
    """
    fields, errors = {}, []

    def text(column, target):
        if v := value(column):
            if len(v) > MAX_LENGTH[target]:
                errors.append(("field_too_long", column))
            else:
                fields[target] = v

    text(FIRST_NAME, "Person.first_name")
    text(LAST_NAME, "Person.last_name")
    text(PHONE, "Person.phone")  # tal com ve
    text(CLUBER_ID, "Member.cluber_id")
    if email := value(EMAIL):
        try:
            validate_email(email)
            fields["Person.contact_email"] = email
        except ValidationError:
            errors.append(("email_invalid", EMAIL))

    city = "" if value(CITY) == "-" else value(CITY)  # la província no s'hi afegeix
    locality = " ".join(part for part in (value(POSTAL_CODE), city) if part)
    if address := ", ".join(part for part in (value(ADDRESS), locality) if part):
        if len(address) > MAX_LENGTH["Person.address"]:
            errors.append(("field_too_long", ADDRESS))
        else:
            fields["Person.address"] = address

    today = timezone.localdate()
    for column, target in (
        (BIRTH_DATE, "Person.birth_date"),
        (JOINED_ON, "Member.joined_on"),
        (LAST_RENEWAL, "last_renewal"),
    ):
        if raw := value(column):
            date = parse_date(raw)
            if date is None or (target == "Person.birth_date" and date > today):
                errors.append(("date_invalid", column))
            else:
                fields[target] = date

    if _fold(value(IMAGE_CONSENT)) in YES:
        fields["image_consent"] = True
    return fields, errors


def resolve_type(quota: str, types: list) -> tuple[MembershipType | None, str | None]:
    """Tipus de soci a partir del text de «Quota» (071, punt 5).

    1r: el nom d'un sol tipus surt dins el text, per paraules senceres i sense majúscules ni
    accents. 2n: l'únic preu del text coincideix amb la quota vigent d'un sol tipus. Si no, cap
    tipus (pendent: el tria la secretaria). Torna `(tipus, "name" | "price" | None)`.
    """
    folded = _fold(quota)
    by_name = [t for t in types if re.search(rf"(?<!\w){re.escape(_fold(t.name))}(?!\w)", folded)]
    if len(by_name) == 1:
        return by_name[0], "name"
    cents = price_in_text(quota)
    by_price = [t for t in types if cents is not None and t.annual_fee_cents == cents]
    if len(by_price) == 1:
        return by_price[0], "price"
    return None, None


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
    # Camps que s'omplirien (destinacions d'`EQUIVALENCES`), sense cap valor.
    fields: list = field(default_factory=list)
    member_type: str | None = None  # codi del tipus deduït (catàleg de la plataforma)
    member_type_by: str | None = None  # "name" o "price"

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
            "fields": list(self.fields),
            "member_type": self.member_type,
            "member_type_by": self.member_type_by,
        }


@dataclass
class Preview:
    rejected: str | None = None
    rejected_column: str = ""
    rejected_row: int | None = None
    encoding: str | None = None  # "utf-8" o "windows-1252"
    rows: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    unknown_columns: list = field(default_factory=list, repr=False)
    # Valors de catàleg: no fiables i potencialment personals; fora de `repr` i de `summary()`.
    catalogue: dict = field(default_factory=dict, repr=False)
    catalogue_omitted: dict = field(default_factory=dict)
    # Noms dels tipus actius de la plataforma (codi → nom), per presentar el tipus deduït.
    type_names: dict = field(default_factory=dict)

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
            "encoding": self.encoding,
            "counts": self.counts,
            "warnings": list(self.warnings),
            "unknown_columns": len(self.unknown_columns),
            "catalogue": {column: len(values) for column, values in self.catalogue.items()},
            "catalogue_omitted": dict(self.catalogue_omitted),
            "type_names": dict(self.type_names),
            "rows": [r.summary() for r in self.rows],
        }


def _reject(code, *, column="", row=None, encoding=None) -> Preview:
    return Preview(rejected=code, rejected_column=column, rejected_row=row, encoding=encoding)


def _decode(data: bytes) -> tuple[str, str] | None:
    """UTF-8 (amb BOM opcional) i, si no ho és, Windows-1252 (071, punt 1)."""
    # shortcut: Windows-1252 accepta gairebé qualsevol byte; un fitxer en ISO-8859-15 o un altre
    # joc es llegiria malament sense avís. Si Cluber exporta en un altre joc, cal detectar-lo.
    for codec, name in (("utf-8-sig", "utf-8"), ("cp1252", "windows-1252")):
        try:
            return data.decode(codec), name
        except UnicodeDecodeError:
            continue
    return None


def preview(data: bytes, *, keep_values: bool = False) -> Preview:
    """Valida l'exportació de Cluber sense escriure res i en torna el resultat.

    `keep_values` només el fa servir la importació final (`imports/final.py`, T-M01-25): cada
    fila conserva en memòria els valors normalitzats d'`EQUIVALENCES` (`Row.data["values"]`,
    fora de `repr` i de `summary()`) per crear la persona i el soci. La prova no els conserva.
    """
    # La mida es comprova abans de descodificar: el text i el lector queden acotats per 1 MiB.
    if len(data) > MAX_BYTES:
        return _reject("too_large")
    # CA-20.8, abans de descodificar res. Preventiu: la garantia és l'índex únic del lot i la
    # transacció de la confirmació (T-M01-25).
    if ImportBatch.objects.filter(
        kind=ImportBatch.Kind.CLUBER, status=ImportBatch.Status.CONFIRMED
    ).exists():
        return _reject("cluber_already_imported")
    decoded = _decode(data)
    if decoded is None:
        return _reject("encoding")
    text, encoding = decoded
    # PostgreSQL no admet NUL en un text: el fitxer es rebutja abans de cap registre o consulta.
    if "\x00" in text:
        return _reject("malformed", encoding=encoding)
    if not text.strip():
        return _reject("empty", encoding=encoding)

    # El lector va registre a registre: no es llegeix cap fila abans de validar la capçalera.
    # El límit aprovat (MAX_FIELD) es comprova a cada fila. El límit intern del mòdul csv
    # (131.072 caràcters) no es canvia perquè afecta tot el procés: un camp que el supera fa
    # rebutjar el fitxer com a «malformed», sense res del seu contingut.
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=";", strict=True)
    try:
        raw_headers = next(reader)
    except csv.Error:
        return _reject("malformed", row=1, encoding=encoding)
    headers = [h.strip() for h in raw_headers]
    keys = [_header_key(h) for h in raw_headers]
    iban = [i for i, key in enumerate(keys) if key in IBAN_HEADERS]

    for i, header in enumerate(raw_headers):
        if len(header) > MAX_FIELD:
            return _reject("field_too_long", column=_label(headers[i], i), row=1, encoding=encoding)
    first = {}
    for i, key in enumerate(keys):
        if key in first:
            column = _label(headers[first[key]], first[key])
            return _reject("duplicate_header", column=column, encoding=encoding)
        first[key] = i
    for required in REQUIRED_HEADERS:
        if required not in headers:
            return _reject("missing_header", column=required, encoding=encoding)

    result = Preview(encoding=encoding, warnings=["no_document_type"])
    if iban:
        result.warnings.append("iban_discarded")
    result.unknown_columns = [
        h for i, h in enumerate(headers) if h not in KNOWN_HEADERS and i not in iban
    ]
    if result.unknown_columns:
        result.warnings.append("unknown_columns")
    index = {h: i for i, h in enumerate(headers) if i not in iban}
    catalogue = {h: Counter() for h in CATALOGUE_HEADERS if h in index}
    # Text de «Quota» i «Preu total» de cada fila llegida, només fins a resoldre'n el tipus.
    to_resolve = []

    row_number = 1
    try:
        for values in reader:
            if not values:  # línia buida
                continue
            for i in iban:  # abans de cap altre tractament: el valor no passa enlloc
                if i < len(values):
                    values[i] = ""
            row_number += 1
            if len(result.rows) == MAX_ROWS:
                return _reject("too_many_rows", encoding=encoding)
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

            def value(header, values=values):
                return values[index[header]].strip() if header in index else ""

            _read_row(row, value, keep_values)
            to_resolve.append((row, value(QUOTA), value(TOTAL_PRICE)))
            for column, counter in catalogue.items():
                if v := value(column):
                    counter[v] += 1
    except csv.Error:
        return _reject("malformed", row=row_number + 1, encoding=encoding)

    if not result.rows:
        return _reject("no_rows", encoding=encoding)
    for column, counter in catalogue.items():
        if len(counter) <= MAX_CATALOGUE:
            result.catalogue[column] = dict(counter)
        else:
            result.catalogue_omitted[column] = len(counter)
    _resolve_types(result, to_resolve)
    _mark_duplicates(result.rows)
    _match(result.rows)
    return result


def _read_row(row: Row, value, keep_values: bool = False) -> None:
    """Valida la fila i en conserva només el document normalitzat, el número de soci i la llista
    dels camps que s'omplirien (i, per a la importació final, els valors normalitzats)."""
    number_text = value(NUMBER)
    row.data = {
        "member_number_text": number_text,
        "id_document": normalize_document(value(DOCUMENT)),
    }
    # Sense retallar-lo: un document més llarg que el camp de destinació és un error de fila.
    if len(row.data["id_document"]) > DOCUMENT_MAX_LENGTH:
        row._error("field_too_long", DOCUMENT)

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

    fields, errors = normalize(value)
    if keep_values:
        row.data["values"] = dict(fields)
    for code, column in errors:
        row._error(code, column)
    if "member_number" in row.data:
        fields["Member.member_number"] = True
    if row.data["id_document"]:
        fields["Person.id_document_number"] = True
    row.fields = sorted(fields)  # només les claus: cap valor no queda al resultat
    # Sense data d'alta, s'importaria igualment (071, punt 8): és un advertiment, no un pendent.
    if "Member.joined_on" not in fields and ("date_invalid", JOINED_ON) not in errors:
        row.warnings.append("joined_on")

    row.pending.extend(code for header, code in PRESENCE.items() if not value(header))
    row.pending.append("id_document_type" if row.data["id_document"] else "id_document")


def _resolve_types(result: Preview, to_resolve: list) -> None:
    """Tipus de soci de cada fila llegida (071, punt 5), amb una sola consulta. «Preu total» només
    serveix per avisar si no coincideix amb la quota del tipus deduït (punt 6)."""
    if not to_resolve:
        return
    types = list(MembershipType.objects.filter(active=True).order_by("pk"))
    result.type_names = {t.code: t.name for t in types}
    for row, quota, total in to_resolve:
        membership_type, by = resolve_type(quota, types) if quota else (None, None)
        if membership_type is None:
            row.pending.append("member_type")
            continue
        row.member_type, row.member_type_by = membership_type.code, by
        amount = _AMOUNT_RE.fullmatch(total)
        if amount and _cents(amount.group(1)) != membership_type.annual_fee_cents:
            row.warnings.append("total_price_differs")


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
    número: tots els socis, de qualsevol estat. Si el soci és d'una persona anonimitzada, el
    número està ocupat: la fila és un conflicte bloquejant («member_number_unavailable») i no
    en conserva cap dada.
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
    # Números de socis de persones anonimitzades: ocupats, mai utilitzables per coincidir.
    unavailable = set()
    if numbers:
        members = Member.objects.filter(member_number__in=numbers).values_list(
            "member_number", "pk", "person_id", "person__id_document_number", "person__status"
        )
        for number, pk, person, doc, status in members:
            if status == Person.Status.ANONYMISED:
                unavailable.add(number)
            else:
                by_number[number] = (pk, person, doc)
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
        if number in unavailable:
            # Preval sobre tota la resta. Res de l'antic titular no passa a la fila.
            row.identity = "conflict"
            row._error("member_number_unavailable", NUMBER)
            if people:  # el document és d'una persona activa, per força una altra
                row._error("identity_conflict", "")  # la relació, no un camp
            continue
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
            row._error("identity_conflict", "")  # la relació, no un camp
        elif person or by_num:
            row.identity = "matching"
            row.person_id = person or by_num[1]
            row.member_id = by_num[0] if by_num else own_member and own_member[0]
            if person:
                row.warnings.append("match_without_document_type")
        else:
            row.identity = "new"
