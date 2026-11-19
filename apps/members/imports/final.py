"""Importació de Cluber, fase final (T-M01-25; CA-M01-22 i CA-M01-23; decisió 071).

Preparada però **bloquejada per configuració**: `confirm()` i `undo()` no llegeixen ni escriuen
res mentre `settings.CLUBER_FINAL_IMPORT_ALLOWED` no sigui exactament `True` (CA-M01-23). L'opció
no és a la configuració: s'activa quan el 05a pugui rebre mandats (T-M05a-20, CA-M05a-16). Cap
vista ni ordre no crida aquest servei encara: el punt d'entrada és del 05a (T-M05a-20).

Decisió 079 (A-25, A-26 i A-27; RN-M01-95; CA-M01-107 i 108):
- **Tipus de document:** el lector el dedueix quan el DNI o el NIE té la lletra correcta. Per a
  la resta, la secretaria el tria fila per fila (`document_types`, número de registre → tipus);
  una fila amb document i sense tipus no s'importa mai.
- **Empremta:** la canònica de les columnes llegides, sense la d'IBAN (`Preview.fingerprint`).
  Si qui crida passa la de la prova (`file_sha256`), ha de coincidir: si no, el fitxer ha
  canviat i es rebutja. El lot desa sempre la canònica.
- **Desfer** (`undo`): el lot passa a «desfet» i els socis importats es donen de baixa amb
  motiu; cap número queda lliure (039) i cap persona s'esborra.
- Files coincidents: s'exclouen (com ara). Text d'imatges de Cluber: tipus propi (com ara).
- Polítiques a la primera entrada: `apps/members/policies.py`.

Què fa, en una sola transacció (si falla qualsevol pas, no queda res escrit):
- torna a validar el fitxer amb `cluber.preview()`, que descarta la columna d'IBAN en llegir;
- exigeix que cada fila que no es pot importar estigui exclosa explícitament i que n'hi hagi
  almenys una d'importable (una importació buida gastaria l'única importació final, RN-93);
- crea el lot confirmat i, per cada fila importable, la persona (`persons.create_or_get`), el
  soci actiu amb el número de Cluber, `cluber_id`, la data d'alta si n'hi ha (Q-075), l'última
  renovació de Cluber (`cluber_renewed_on`, d'on compten el venciment i el carnet, 097),
  la llavor de l'avatar (`new_avatar_seed`, per defecte del model) i l'entrada inicial de
  l'historial amb la procedència «importat de Cluber» (Q-072), el consentiment d'imatges amb el
  canal «importat de Cluber» si la cel·la diu «sí», i el carnet amb el servei de carnets si hi ha
  «Data alta/renovació» (RN-M01-34; 097, punt 1; T-M01-19b): sense aquesta data, cap carnet;
- una línia per fila, amb codis de la llista tancada i sense cap valor del fitxer;
- el comptador de números continua després del més alt importat (RN-M01-32, CA-M01-22).

Què **no** fa, perquè depèn de decisions obertes (cap codi no en simula la regla):
- Fila importable = nova, sense errors i amb el tipus de document (deduït o triat). Una fila
  **sense document** continua pendent («id_document») i no s'importa mai sola (decisió 081, punt
  19, opció A): s'ha d'excloure expressament, la línia en guarda el motiu i la secretaria en fa
  l'alta a mà, on valen les excepcions dels menors (RN-M01-70). No s'inventa cap document.
  Sense data d'alta, s'importa sense cap data i no es mostra l'antiguitat (072, Q-075); l'entrada
  inicial de l'historial porta la data de la importació.
- Les files de baixa a Cluber (072, Q-071, que modifica el punt 7 de la 071) no s'importen mai:
  queden excloses soles, amb el codi «left_in_cluber» a la seva línia, que és la llista per a la
  secretaria. La resta entren actives.
- Les files coincidents no s'importen ni modifiquen la persona: s'han d'excloure (P-65, punt 3).
- Cap quota, càrrec ni moviment (RN-M01-33; 071, punts 3 i 6).
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

from ..cards import issue_card, revoke_card
from ..models import Member, MembershipNumberCounter, MembershipType, MemberStatusChange
from . import cluber

PERMISSION = "members.cluber_import.run"  # P18
# Tipus del text del consentiment d'imatges de Cluber. Els tipus de text són dades (Q-16): si
# ha de comptar com el consentiment d'imatges de la plataforma és part de la mateixa pregunta.
IMAGE_CONSENT_KIND = consents.IMPORTED_IMAGES_KIND
IMAGE_CONSENT_LANGUAGE = "es"  # el text de la capçalera de Cluber és en castellà

DUPLICATE_CODES = {"duplicate_document", "duplicate_member_number"}

MESSAGES = {
    "blocked": _("La importació final no està disponible fins que el 05a pugui rebre mandats."),
    "excluded_row_unknown": _("S'ha exclòs una fila que no existeix al fitxer."),
    "rows_unresolved": _("Hi ha files que no es poden importar i no s'han exclòs."),
    "nothing_to_import": _("No hi ha cap fila per importar."),
    "conflict": _("Les dades han canviat mentre es confirmava: torna a fer la prova."),
    "file_changed": _("El fitxer no és el de la prova: torna a fer la prova."),
    "document_type_row_unknown": _("S'ha triat el tipus de document d'una fila que no el demana."),
    "document_type_invalid": _("El tipus de document triat no és vàlid."),
    "not_undoable": _("Aquest lot no es pot desfer."),
    "reason_required": _("Cal el motiu per desfer la importació."),
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


DOCUMENT_TYPES = set(Person.DocumentType.values)


def importable(row: cluber.Row, document_types=None) -> bool:
    """Nova, sense errors, no de baixa a Cluber, sense cap pendent llevat del tipus de document
    triat per la secretaria, i mai un document sense el seu tipus."""
    document_types = document_types or {}
    if row.left_in_cluber or row.errors or row.identity != "new":
        return False
    pending = set(row.pending)
    if pending - {"id_document_type"}:
        return False
    if not row.data["id_document"]:
        return True
    if "id_document_type" in pending:
        return row.row in document_types
    return bool(row.data.get("id_document_type"))


def _document_type(row: cluber.Row, document_types) -> str:
    return row.data.get("id_document_type") or document_types.get(row.row, "")


def _codes(row: cluber.Row) -> list:
    left = ["left_in_cluber"] if row.left_in_cluber else []
    return list(dict.fromkeys([*left, *row.errors, *row.pending, *row.warnings]))


def _result(row: cluber.Row) -> str:
    if DUPLICATE_CODES & set(row.errors):
        return ImportLine.Result.DUPLICATE
    if row.errors:
        return ImportLine.Result.ERROR
    return ImportLine.Result.EXCLUDED


def confirm(
    data: bytes, *, by, file_sha256: str | None = None, excluded_rows=(), document_types=None
) -> ImportBatch:
    """Importa les files importables de l'exportació. `excluded_rows`: números de registre que
    l'administrador exclou. `file_sha256`: l'empremta canònica que va mostrar la prova; si no
    coincideix, es rebutja (079, P-65 punt 1). `document_types`: número de registre → tipus de
    document, per a les files on no s'ha pogut deduir (079, A-25)."""
    if not is_allowed():  # abans de llegir res ni consultar la base de dades
        raise FinalImportBlocked(MESSAGES["blocked"])
    if not has_perm(by, PERMISSION):
        raise PermissionDenied
    result = cluber.preview(data, keep_values=True)
    if result.rejected:
        raise FinalImportRefused(result.rejected)

    if file_sha256 is not None and file_sha256 != result.fingerprint:
        raise FinalImportRefused("file_changed")
    document_types = dict(document_types or {})
    if set(document_types.values()) - DOCUMENT_TYPES:
        raise FinalImportRefused("document_type_invalid")
    needs_type = {r.row for r in result.rows if "id_document_type" in r.pending}
    if wrong := set(document_types) - needs_type:
        raise FinalImportRefused("document_type_row_unknown", tuple(sorted(wrong)))

    excluded = set(excluded_rows)
    rows = {r.row for r in result.rows}
    if unknown := excluded - rows:
        raise FinalImportRefused("excluded_row_unknown", tuple(sorted(unknown)))
    to_import = [r for r in result.rows if importable(r, document_types) and r.row not in excluded]
    # Les de baixa a Cluber queden excloses soles (072, Q-071).
    unresolved = [
        r.row
        for r in result.rows
        if not importable(r, document_types) and r.row not in excluded and not r.left_in_cluber
    ]
    if unresolved:
        raise FinalImportRefused("rows_unresolved", tuple(unresolved))
    if not to_import:
        raise FinalImportRefused("nothing_to_import")

    try:
        with transaction.atomic():
            return _write(result, to_import, by, result.fingerprint, document_types)
    except IntegrityError as error:
        # Un altre lot confirmat, o un número o un `cluber_id` ocupat mentrestant: res escrit.
        raise FinalImportRefused("conflict") from error


def _write(result, to_import, by, file_sha256, document_types) -> ImportBatch:
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
        document = row.data["id_document"]
        person, created, _check = create_or_get(
            origin=Person.Origin.CLUBER_IMPORT,
            import_batch=batch,
            first_name=values["Person.first_name"],
            last_name=values["Person.last_name"],
            contact_email=values.get("Person.contact_email", ""),
            phone=values.get("Person.phone", ""),
            address=values.get("Person.address", ""),
            birth_date=values.get("Person.birth_date"),
            id_document_type=_document_type(row, document_types) if document else "",
            id_document_number=document,
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
            # Q-076 (097, punt 1): el venciment compta des d'aquí; només amb `cluber_id`.
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
        if member.cluber_renewed_on:  # RN-M01-34: sense la data, cap carnet
            issue_card(member, by=by)
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
        details={
            **{f"{kind}_count": counts[kind] for kind in ImportLine.Result.values},
            # Quantes files porten el tipus deduït i quantes el triat per la secretaria.
            "document_type_deduced": sum(1 for r in to_import if r.data.get("id_document_type")),
            "document_type_chosen": sum(1 for r in to_import if r.row in document_types),
        },
    )
    return batch


UNDONE = "members.cluber_import.undone"


def undo(batch: ImportBatch, *, by, reason: str, request=None) -> int:
    """Desfà el lot confirmat de Cluber (079, A-26 punt 2; CA-M01-108): el lot passa a «desfet»
    i cada soci importat encara no de baixa es dona de baixa amb el motiu i amb el carnet
    revocat, si en tenia. Cap número de soci queda lliure (039), el comptador no baixa i cap
    persona, consentiment ni línia s'esborra. Torna quants socis s'han donat de baixa. Tot o
    res, en una sola transacció. Amb el lot desfet, `preview` torna a admetre una importació,
    però els números dels socis donats de baixa continuen ocupats."""
    from ..services import S, _change_status

    if not is_allowed():
        raise FinalImportBlocked(MESSAGES["blocked"])
    if not has_perm(by, PERMISSION):
        raise PermissionDenied
    reason = (reason or "").strip()
    if not reason:
        raise FinalImportRefused("reason_required")
    today = timezone.localdate()
    with transaction.atomic():
        locked = ImportBatch.objects.select_for_update().get(pk=batch.pk)
        if locked.kind != ImportBatch.Kind.CLUBER or locked.status != ImportBatch.Status.CONFIRMED:
            raise FinalImportRefused("not_undoable")
        members = Member.objects.filter(import_batch=locked).exclude(status=S.LEFT).order_by("pk")
        count = 0
        for member in members:
            revoke_card(member, by=by, reason=reason, request=request)
            _change_status(
                member, S.LEFT, by=by, effective_on=today, reason=reason, request=request
            )
            count += 1
        locked.status = ImportBatch.Status.UNDONE
        locked.undone_by = by
        locked.undone_at = timezone.now()
        locked.save(update_fields=["status", "undone_by", "undone_at"])
        audit.record(
            UNDONE,
            actor=by,
            target=locked,
            reason=reason,
            details={"members_left": count},
            request=request,
        )
    batch.refresh_from_db()
    return count
