"""Serveis de persona de la 00."""

from dataclasses import dataclass, field

from django.conf import settings
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


def language_for(person) -> str:
    """Llengua en què s'escriu a la persona: la preferida si és activa; si no, la de reserva
    (decisió 061)."""
    active = {code for code, _ in settings.LANGUAGES}
    if person.preferred_language in active:
        return person.preferred_language
    return settings.LANGUAGE_CODE
