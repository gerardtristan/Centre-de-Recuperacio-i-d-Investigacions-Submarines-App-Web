"""Serveis de persona de la 00."""

from dataclasses import dataclass, field

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from . import audit
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


UPDATED = "persons.updated"
EDITABLE_FIELDS = (
    "first_name",
    "last_name",
    "contact_email",
    "phone",
    "address",
    "landline",
    "postal_code",
    "city",
    "province",
    "id_document_type",
    "id_document_number",
)
DOCUMENT_IN_USE = _(
    "Aquest document ja és d'una altra persona. Revisa'l: els perfils no es fusionen sols."
)


def update(person, *, by, request=None, **fields) -> list[str]:
    """Corregeix les dades d'una persona i en deixa una entrada per camp al registre
    d'activitat, amb el valor anterior (RN-50). Torna els camps que han canviat; si no en canvia
    cap, no escriu res. Qui crida ja ha comprovat el permís i els camps que pot editar.

    Una persona anonimitzada no s'edita (028). El document segueix sent únic (RN-06): si ja és
    d'una altra persona, es rebutja i no es fusionen perfils (RN-07)."""
    unknown = set(fields) - set(EDITABLE_FIELDS)
    if unknown:
        raise ValueError(f"Camps no editables: {sorted(unknown)}")
    with transaction.atomic():
        locked = Person.objects.select_for_update().get(pk=person.pk)
        if locked.status != Person.Status.ACTIVE:
            raise ValidationError(
                _("Les dades d'aquesta persona estan anonimitzades i no es poden editar.")
            )
        old = {name: getattr(locked, name) for name in fields}
        for name, value in fields.items():
            setattr(locked, name, value)
        locked.normalize()
        changes = {
            name: (old[name], getattr(locked, name))
            for name in fields
            if old[name] != getattr(locked, name)
        }
        if not changes:
            return []
        document = (locked.id_document_type, locked.id_document_number)
        if {"id_document_type", "id_document_number"} & set(changes) and document[1]:
            other = Person.objects.filter(
                id_document_type=document[0], id_document_number=document[1]
            ).exclude(pk=locked.pk)
            if other.exists():
                raise ValidationError(DOCUMENT_IN_USE)
        try:
            with transaction.atomic():
                locked.save(update_fields=[*changes, "updated_at"])
        except IntegrityError:  # una altra edició simultània amb el mateix document
            raise ValidationError(DOCUMENT_IN_USE) from None
        audit.record_changes(UPDATED, actor=by, target=locked, changes=changes, request=request)
    person.refresh_from_db()
    return list(changes)


BIRTH_DATE_SET = "persons.birth_date_set"
BIRTH_DATE_IN_FUTURE = _("La data de naixement no pot ser posterior a avui.")


def check_birth_date(birth_date, today=None) -> None:
    """079 (A-10, RN-M01-90): una data de naixement futura es rebutja en desar."""
    if birth_date is not None and birth_date > (today or timezone.localdate()):
        raise ValidationError(BIRTH_DATE_IN_FUTURE)


def set_birth_date(person, birth_date, *, by, request=None, source="") -> bool:
    """Desa la data de naixement de la persona. Torna si ha canviat. El registre d'activitat
    guarda que ha canviat i d'on ve, **mai la data** (RN-M01-48). Qui crida ja ha comprovat el
    permís (C1). Una data futura es rebutja; una persona anonimitzada no s'edita."""
    check_birth_date(birth_date)
    with transaction.atomic():
        locked = Person.objects.select_for_update().get(pk=person.pk)
        if locked.status != Person.Status.ACTIVE:
            raise ValidationError(
                _("Les dades d'aquesta persona estan anonimitzades i no es poden editar.")
            )
        if locked.birth_date == birth_date:
            return False
        had = locked.birth_date is not None
        was_checked = locked.birth_date_checked_at is not None
        locked.birth_date = birth_date
        # Una data nova és una declaració nova: la comprovació anterior ja no la cobreix (081).
        locked.birth_date_checked_at = None
        locked.save(update_fields=["birth_date", "birth_date_checked_at", "updated_at"])
        audit.record(
            BIRTH_DATE_SET,
            actor=by,
            target=locked,
            field="birth_date",
            details={
                "had_value": had,
                "has_value": birth_date is not None,
                "source": source,
                "check_reset": was_checked,
            },
            request=request,
        )
    person.birth_date = birth_date
    person.birth_date_checked_at = None
    return True


BIRTH_DATE_CHECKED = "persons.birth_date_checked"


def mark_birth_date_checked(person, *, by, request=None) -> bool:
    """Decisió 081, punt 16 (RN-M01-99): la secretaria ha comprovat la data de naixement amb el
    document d'identitat (el d'un menor, el DNI que mostra el seu representant legal). És
    posterior a la declaració i no condiciona res del que la data ja fa (per exemple, l'exempció
    de la quota). Torna si ha canviat. Decisió 082, punt 1: també sense document a la fitxa
    (RN-M01-70 no canvia), i el registre només diu qui i quan: ni la data, ni el document, ni cap
    còpia. Qui crida ja ha comprovat els permisos."""
    with transaction.atomic():
        locked = Person.objects.select_for_update().get(pk=person.pk)
        if locked.status != Person.Status.ACTIVE:
            raise ValidationError(
                _("Les dades d'aquesta persona estan anonimitzades i no es poden editar.")
            )
        if locked.birth_date is None:
            raise ValidationError(_("Aquesta persona no té data de naixement per comprovar."))
        if locked.birth_date_checked_at is not None:
            return False
        locked.birth_date_checked_at = timezone.now()
        locked.save(update_fields=["birth_date_checked_at", "updated_at"])
        audit.record(
            BIRTH_DATE_CHECKED,
            actor=by,
            target=locked,
            field="birth_date_checked_at",
            request=request,
        )
    person.birth_date_checked_at = locked.birth_date_checked_at
    return True


# Dades que la persona pot corregir des del seu perfil (HU-M01-08; 061). El nom, el document i la
# data de naixement només els corregeix la secretaria; el correu d'entrada té el seu propi camí.
PROFILE_FIELDS = (
    "phone",
    "address",
    "landline",
    "postal_code",
    "city",
    "province",
    "preferred_language",
)


def update_profile(person, *, actor, request=None, **values) -> list:
    """Desa les dades del perfil i registra cada camp que canvia amb el valor anterior (RN-50,
    CA-14.1). Torna les entrades del registre (cap si no canvia res). Un camp fora de
    `PROFILE_FIELDS` o una llengua que no és activa és un error de qui crida: el formulari ja ho
    ha validat."""
    unknown = set(values) - set(PROFILE_FIELDS)
    if unknown:
        raise ValueError(f"Camps que no es poden editar des del perfil: {sorted(unknown)}")
    active = {code for code, _ in settings.LANGUAGES}
    if "preferred_language" in values and values["preferred_language"] not in active:
        raise ValueError("Llengua no activa (decisió 061).")
    with transaction.atomic():
        person = Person.objects.select_for_update().get(pk=person.pk)
        # Una petició que esperava el bloqueig mentre s'executava l'esborrat (T-M01-22) no torna a
        # escriure cap dada a la persona ja anonimitzada.
        if person.status != Person.Status.ACTIVE:
            raise ValidationError(ANONYMISED_NOT_EDITABLE)
        old = {name: getattr(person, name) for name in values}
        for name, value in values.items():
            setattr(person, name, value)
        person.save(update_fields=[*values, "updated_at"])  # `save` normalitza el telèfon
        changes = {name: (old[name], getattr(person, name)) for name in values}
        return audit.record_changes(
            audit.Action.PROFILE_UPDATED,
            actor=actor,
            target=person,
            changes=changes,
            request=request,
        )


ANONYMISED_NOT_EDITABLE = _("Les dades d'aquesta persona estan anonimitzades i no es poden editar.")
# Domini reservat que no existeix (RFC 2606): cap correu no hi pot arribar.
ANONYMOUS_EMAIL_DOMAIN = "anonimitzat.invalid"


def anonymous_ref_for(person) -> str:
    """Referència d'una persona (028), p. ex. «A-0042». Surt de l'identificador intern:
    és única sense cap comptador i no diu res de la persona."""
    return f"A-{person.pk:04d}"


def anonymous_email(ref: str) -> str:
    """Adreça que substitueix un correu de la persona anonimitzada on el camp no pot ser buit."""
    return f"{ref.lower()}@{ANONYMOUS_EMAIL_DOMAIN}"


def language_for(person) -> str:
    """Llengua en què s'escriu a la persona: la preferida si és activa; si no, la de reserva
    (decisió 061)."""
    active = {code for code, _ in settings.LANGUAGES}
    if person.preferred_language in active:
        return person.preferred_language
    return settings.LANGUAGE_CODE


def age_on(birth_date, on) -> int:
    """Anys complerts el dia `on` (068). Qui crida passa la data local (Barcelona), mai una edat
    que enviï el navegador. Nascuts el 29 de febrer: en un any no de traspàs compleixen l'1 de
    març (comportament de la fórmula, provat a la T-M01-13; per confirmar)."""
    return on.year - birth_date.year - ((on.month, on.day) < (birth_date.month, birth_date.day))


ADULT_AGE = 18  # menor = menys de 18 anys complerts (RN-M01-62); el mateix que `fee_rules`


class AgeBand(models.TextChoices):
    """El que veu de l'edat qui no té C1 (RN-M01-48)."""

    ADULT = "adult", _("Major d'edat")
    MINOR = "minor", _("Menor d'edat")
    UNKNOWN = "unknown", _("Edat desconeguda")


def age_band(person, on=None) -> AgeBand:
    """Major, menor o edat desconeguda el dia `on` (per defecte, avui a Barcelona), sense
    revelar la data (058, RN-M01-48). Sense data, «desconeguda» i no es bloqueja res
    (RN-M01-55). Una data posterior a `on` no és vàlida: també «desconeguda»."""
    on = on or timezone.localdate()
    birth = person.birth_date
    if birth is None or birth > on:
        return AgeBand.UNKNOWN
    return AgeBand.ADULT if age_on(birth, on) >= ADULT_AGE else AgeBand.MINOR
