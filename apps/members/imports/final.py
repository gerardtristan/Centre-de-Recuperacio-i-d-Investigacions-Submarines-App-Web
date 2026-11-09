"""Importació de Cluber, fase final (T-M01-25; CA-M01-22 i CA-M01-23; decisió 071).

Preparada però **bloquejada per configuració**: `confirm()` no llegeix ni escriu res mentre
`settings.CLUBER_FINAL_IMPORT_ALLOWED` no sigui exactament `True` (CA-M01-23). L'opció no és a
la configuració: s'activa quan el 05a pugui rebre mandats (T-M05a-20, CA-M05a-16). Cap vista ni
ordre no crida aquest servei encara: el comprovant que lliga la prova amb la confirmació depèn
d'una decisió oberta sobre l'empremta del fitxer (P-65, punt 1), i el punt d'entrada la
necessita.

Què fa, en una sola transacció (si falla qualsevol pas, no queda res escrit):
- torna a validar el fitxer amb `cluber.preview()`, que descarta la columna d'IBAN en llegir;
- exigeix que cada fila que no es pot importar estigui exclosa explícitament i que n'hi hagi
  almenys una d'importable (una importació buida gastaria l'única importació final, RN-93);
- crea el lot confirmat i, per cada fila importable, la persona (`persons.create_or_get`), el
  soci actiu amb el número de Cluber, `cluber_id`, la data d'alta si n'hi ha (Q-075), l'última
  renovació de Cluber (`cluber_renewed_on`, d'on compta el carnet, Q-076 [A validar: tresorer]),
  la llavor de l'avatar (`new_avatar_seed`, per defecte del model) i l'entrada inicial de
  l'historial amb la procedència «importat de Cluber» (Q-072), i el consentiment d'imatges amb el
  canal «importat de Cluber» si la cel·la diu «sí»;
- una línia per fila, amb codis de la llista tancada i sense cap valor del fitxer;
- el comptador de números continua després del més alt importat (RN-M01-32, CA-M01-22).

Què **no** fa, perquè depèn de decisions obertes (cap codi no en simula la regla):
- Fila importable = preparada (`Row.ready`), nova i **sense document**. Avui cap fila no és
  preparada: totes tenen pendent el tipus de document o el document (P-62, punt 5). Una fila amb
  document no s'importa fins que el servei desi també el tipus: mai no es perd el document en
  silenci. Sense data d'alta, s'importa sense cap data i no es mostra l'antiguitat (072, Q-075);
  l'entrada inicial de l'historial porta la data de la importació.
- Les files de baixa a Cluber (072, Q-071, que modifica el punt 7 de la 071) no s'importen mai:
  queden excloses soles, amb el codi «left_in_cluber» a la seva línia, que és la llista per a la
  secretaria. La resta entren actives.
- Les files coincidents no s'importen ni modifiquen la persona: s'han d'excloure (P-65, punt 3).
- Cap quota, càrrec ni moviment (RN-M01-33; 071, punts 3 i 6). Cap carnet: el provisional de la
  RN-M01-34 és [A validar: tresorer] i de la T-M01-19.
- Desfer no existeix: si desfer elimina o anul·la els registres és una decisió oberta (P-65,
  punt 2).
"""

from collections import Counter

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit, consents, imports
from apps.core.models import ImportBatch, ImportLine, Person
from apps.core.permissions import has_perm
from apps.core.persons import create_or_get

from ..models import Member, MembershipNumberCounter, MembershipType, MemberStatusChange
from . import cluber

PERMISSION = "members.cluber_import.run"  # P18
# Tipus del text del consentiment d'imatges de Cluber. Els tipus de text són dades (Q-16): si
# ha de comptar com el consentiment d'imatges de la plataforma és part de la mateixa pregunta.
IMAGE_CONSENT_KIND = "cluber_images"
IMAGE_CONSENT_LANGUAGE = "es"  # el text de la capçalera de Cluber és en castellà

DUPLICATE_CODES = {"duplicate_document", "duplicate_member_number"}

MESSAGES = {
    "blocked": _("La importació final no està disponible fins que el 05a pugui rebre mandats."),
    "excluded_row_unknown": _("S'ha exclòs una fila que no existeix al fitxer."),
    "rows_unresolved": _("Hi ha files que no es poden importar i no s'han exclòs."),
    "nothing_to_import": _("No hi ha cap fila per importar."),
    "conflict": _("Les dades han canviat mentre es confirmava: torna a fer la prova."),
    **cluber.MESSAGES,
}


class FinalImportBlocked(PermissionDenied):
    """La configuració no permet la importació final (CA-M01-23)."""


class FinalImportRefused(Exception):
    def __init__(self, code: str, rows: tuple = ()):
        super().__init__(code)
        self.code = code
        self.rows = rows  # números de registre, sense cap valor del fitxer


def is_allowed() -> bool:
    # Estricte: només el booleà `True` l'activa, no un text com "False".
    return getattr(settings, "CLUBER_FINAL_IMPORT_ALLOWED", False) is True


def importable(row: cluber.Row) -> bool:
    return (
        row.ready
        and row.identity == "new"
        and not row.data["id_document"]  # P-62, punt 5: el document no es desa sense tipus
    )


def _codes(row: cluber.Row) -> list:
    left = ["left_in_cluber"] if row.left_in_cluber else []
    return list(dict.fromkeys([*left, *row.errors, *row.pending, *row.warnings]))


def _result(row: cluber.Row) -> str:
    if DUPLICATE_CODES & set(row.errors):
        return ImportLine.Result.DUPLICATE
    if row.errors:
        return ImportLine.Result.ERROR
    return ImportLine.Result.EXCLUDED


def confirm(data: bytes, *, by, file_sha256: str, excluded_rows=()) -> ImportBatch:
    """Importa les files importables de l'exportació. `excluded_rows`: números de registre que
    l'administrador exclou. `file_sha256`: l'empremta que es desa al lot; quina (P-65, punt 1) la
    decideix el punt d'entrada, que encara no existeix."""
    if not is_allowed():  # abans de llegir res ni consultar la base de dades
        raise FinalImportBlocked(MESSAGES["blocked"])
    if not has_perm(by, PERMISSION):
        raise PermissionDenied
    result = cluber.preview(data, keep_values=True)
    if result.rejected:
        raise FinalImportRefused(result.rejected)

    excluded = set(excluded_rows)
    rows = {r.row for r in result.rows}
    if unknown := excluded - rows:
        raise FinalImportRefused("excluded_row_unknown", tuple(sorted(unknown)))
    to_import = [r for r in result.rows if importable(r) and r.row not in excluded]
    # Les de baixa a Cluber queden excloses soles (072, Q-071).
    unresolved = [
        r.row
        for r in result.rows
        if not importable(r) and r.row not in excluded and not r.left_in_cluber
    ]
    if unresolved:
        raise FinalImportRefused("rows_unresolved", tuple(unresolved))
    if not to_import:
        raise FinalImportRefused("nothing_to_import")

    try:
        with transaction.atomic():
            return _write(result, to_import, by, file_sha256)
    except IntegrityError as error:
        # Un altre lot confirmat, o un número o un `cluber_id` ocupat mentrestant: res escrit.
        raise FinalImportRefused("conflict") from error


def _write(result, to_import, by, file_sha256) -> ImportBatch:
    new = {r.row for r in to_import}
    results = {r.row: ImportLine.Result.NEW if r.row in new else _result(r) for r in result.rows}
    counts = Counter(results.values())
    batch = imports.open_confirmed(
        ImportBatch.Kind.CLUBER,
        file_sha256=file_sha256,
        by=by,
        counts={f"{kind}_count": counts[kind] for kind in ImportLine.Result.values},
    )
    types = {t.code: t for t in MembershipType.objects.filter(active=True)}
    image_text = None
    people = {}
    for row in to_import:
        values = row.data["values"]
        person, created, _check = create_or_get(
            origin=Person.Origin.CLUBER_IMPORT,
            import_batch=batch,
            first_name=values["Person.first_name"],
            last_name=values["Person.last_name"],
            contact_email=values.get("Person.contact_email", ""),
            phone=values.get("Person.phone", ""),
            address=values.get("Person.address", ""),
            birth_date=values.get("Person.birth_date"),
        )
        if not created:  # sense document no hauria de passar; mai s'assigna un lot a una existent
            raise IntegrityError("persona preexistent")
        cluber_id = values.get("Member.cluber_id") or None
        member = Member.objects.create(
            person=person,
            member_number=row.data["member_number"],
            type=types[row.member_type],
            status=Member.Status.ACTIVE,  # 071, punt 7
            joined_on=values.get("Member.joined_on"),  # Q-075: cap data inventada
            cluber_id=cluber_id,
            # Q-076: el carnet compta des d'aquí [A validar: tresorer]; només amb `cluber_id`.
            cluber_renewed_on=values.get("last_renewal") if cluber_id else None,
            import_batch=batch,
        )
        MemberStatusChange.objects.create(
            member=member,
            to_status=Member.Status.ACTIVE,
            to_type=member.type,
            effective_on=member.joined_on or timezone.localdate(),
            actor_account=by,
            origin=MemberStatusChange.Origin.CLUBER_IMPORT,
        )
        if values.get("image_consent"):
            image_text = image_text or consents.imported_text(
                IMAGE_CONSENT_KIND, cluber.IMAGE_CONSENT, language=IMAGE_CONSENT_LANGUAGE, by=by
            )
            consents.grant_imported(person, image_text, by=by)
        people[row.row] = person

    highest = max(r.data["member_number"] for r in to_import)
    counter = MembershipNumberCounter.objects.select_for_update().get(pk=1)
    counter.last_number = max(counter.last_number, highest)
    counter.save(update_fields=["last_number"])

    imports.add_lines(
        batch,
        [
            {
                "row": r.row,
                "result": results[r.row],
                "codes": _codes(r),
                "person": people.get(r.row),
            }
            for r in result.rows
        ],
    )
    audit.record(
        audit.Action.CLUBER_IMPORT_CONFIRMED,
        actor=by,
        target=batch,
        details={f"{kind}_count": counts[kind] for kind in ImportLine.Result.values},
    )
    return batch
