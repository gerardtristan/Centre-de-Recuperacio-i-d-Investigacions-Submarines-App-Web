"""Serveis de persona de la 00."""

from dataclasses import dataclass, field

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q

from .models import Person
from .normalization import normalize_document, normalize_email, normalize_phone


@dataclass
class DuplicateCheck:
    """Resultat de buscar duplicats abans de crear un perfil (V-03).

    `same_document`: la persona amb el mateix document; no se n'ha de crear cap altra.
    `possible`: mateix correu, o mateix nom i cognoms amb el mateix telèfon. Només és un avís:
    qui crea el perfil decideix, i mai es fusionen perfils sols (RN-07).
    """

    same_document: Person | None = None
    possible: list[Person] = field(default_factory=list)


def find_duplicates(
    *,
    first_name: str = "",
    last_name: str = "",
    phone: str = "",
    contact_email: str = "",
    id_document_type: str = "",
    id_document_number: str = "",
) -> DuplicateCheck:
    active = Person.objects.filter(status=Person.Status.ACTIVE)
    result = DuplicateCheck()

    number = normalize_document(id_document_number)
    if id_document_type and number:
        result.same_document = active.filter(
            id_document_type=id_document_type, id_document_number=number
        ).first()

    conditions = Q()
    email = normalize_email(contact_email)
    if email:
        conditions |= Q(contact_email=email)
    phone = normalize_phone(phone)
    if first_name.strip() and phone:
        conditions |= Q(
            first_name__iexact=first_name.strip(),
            last_name__iexact=last_name.strip(),
            phone=phone,
        )
    if conditions:
        matches = active.filter(conditions)
        if result.same_document:
            matches = matches.exclude(pk=result.same_document.pk)
        result.possible = list(matches.order_by("pk"))
    return result


DUPLICATE_FIELDS = (
    "first_name",
    "last_name",
    "phone",
    "contact_email",
    "id_document_type",
    "id_document_number",
)


def create_or_get(*, origin: str, **fields) -> tuple[Person, bool, DuplicateCheck]:
    """Persona amb aquest document, o una de nova (V-03, RN-06, RN-07). Torna
    `(persona, creada, duplicats)`.

    Amb el mateix document es torna l'existent **sense modificar-la**: les dades noves no s'hi
    escriuen mai (la fusió de perfils queda fora d'abast). Amb un possible duplicat (correu, o
    nom i telèfon) es crea una persona nova i es torna l'avís; mai es fusionen soles.
    Dues altes simultànies amb el mateix document: la restricció única en deixa crear una i
    l'altra torna l'existent."""
    lookup = {k: fields.get(k, "") for k in DUPLICATE_FIELDS}
    check = find_duplicates(**lookup)
    if check.same_document is not None:
        return check.same_document, False, check
    try:
        with transaction.atomic():
            person = Person.objects.create(origin=origin, **fields)
    except IntegrityError:
        check = find_duplicates(**lookup)
        if check.same_document is None:
            raise
        return check.same_document, False, check
    return person, True, check


def language_for(person) -> str:
    """Llengua en què s'escriu a la persona: la preferida si és activa; si no, la de reserva
    (decisió 061)."""
    active = {code for code, _ in settings.LANGUAGES}
    if person.preferred_language in active:
        return person.preferred_language
    return settings.LANGUAGE_CODE


def age_on(birth_date, on) -> int:
    """Anys complerts el dia `on` (068). Peça de la 00 que la T-M01-33 farà servir a `age_band`;
    qui crida passa la data local (Barcelona), mai una edat que enviï el navegador."""
    return on.year - birth_date.year - ((on.month, on.day) < (birth_date.month, birth_date.day))
