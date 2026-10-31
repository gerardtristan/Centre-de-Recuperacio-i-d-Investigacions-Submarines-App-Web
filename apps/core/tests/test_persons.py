"""Persona: perfil únic, normalització i duplicats (spec 00, RN-01 a RN-10, V-03).

Només dades inventades.
"""

import pytest
from django.apps import apps
from django.db import IntegrityError

from apps.core.models import Person
from apps.core.normalization import normalize_document, normalize_phone
from apps.core.persons import find_duplicates

pytestmark = pytest.mark.django_db


def make_person(**fields):
    defaults = {"first_name": "Anna", "last_name": "Puig Soler", "origin": Person.Origin.WEB}
    return Person.objects.create(**(defaults | fields))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("0000 0000-t", "00000000T"), (" x1234567.l ", "X1234567L"), ("", "")],
)
def test_normalize_document(raw, expected):
    assert normalize_document(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("+34 600-00.00.00", "+34600000000"), ("(93) 000 00 00", "930000000"), ("", "")],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


def test_create_person_normalizes_fields():
    person = make_person(
        first_name="  Anna ",
        contact_email=" Anna@Example.ORG ",
        phone="600 00 00 00",
        id_document_type=Person.DocumentType.DNI,
        id_document_number="0000 0000-t",
    )
    person.refresh_from_db()
    assert person.first_name == "Anna"
    assert person.contact_email == "anna@example.org"
    assert person.phone == "600000000"
    assert person.id_document_number == "00000000T"
    assert person.status == Person.Status.ACTIVE


def test_same_document_written_differently_is_rejected():
    # CA-01.2
    make_person(id_document_type="dni", id_document_number="00000000T")
    with pytest.raises(IntegrityError):
        make_person(first_name="Joan", id_document_type="dni", id_document_number="0000-0000 t")


def test_same_number_with_another_document_type_is_allowed():
    make_person(id_document_type="dni", id_document_number="00000000T")
    make_person(first_name="Joan", id_document_type="passport", id_document_number="00000000T")


def test_people_without_document_are_allowed():
    make_person()
    make_person(first_name="Joan")
    assert Person.objects.count() == 2


@pytest.mark.parametrize(
    "fields",
    [{"id_document_type": "dni"}, {"id_document_number": "00000000T"}],
)
def test_document_type_and_number_go_together(fields):
    with pytest.raises(IntegrityError):
        make_person(**fields)


def test_contact_email_is_not_unique():
    # RN-10: famílies que comparteixen correu.
    make_person(contact_email="familia@example.org")
    make_person(first_name="Joan", contact_email="familia@example.org")


def test_anonymous_ref_only_when_anonymised():
    with pytest.raises(IntegrityError):
        make_person(anonymous_ref="A-0001")


def test_anonymised_person_requires_anonymous_ref():
    with pytest.raises(IntegrityError):
        make_person(status=Person.Status.ANONYMISED)


def test_anonymised_person_shows_only_the_reference():
    person = make_person(status=Person.Status.ANONYMISED, anonymous_ref="A-0042")
    assert str(person) == "A-0042"


class TestFindDuplicates:
    def test_same_document_is_the_same_person(self):
        existing = make_person(id_document_type="dni", id_document_number="00000000T")
        check = find_duplicates(id_document_type="dni", id_document_number="0000 0000-t")
        assert check.same_document == existing

    def test_same_contact_email_warns(self):
        existing = make_person(contact_email="anna@example.org")
        check = find_duplicates(first_name="Maria", contact_email="ANNA@example.org ")
        assert check.same_document is None
        assert check.possible == [existing]

    def test_same_name_and_phone_warns(self):
        existing = make_person(phone="600 00 00 00")
        check = find_duplicates(first_name="anna", last_name="puig soler", phone="600-000-000")
        assert check.possible == [existing]

    def test_same_name_with_another_phone_does_not_warn(self):
        make_person(phone="600000000")
        check = find_duplicates(first_name="Anna", last_name="Puig Soler", phone="611111111")
        assert check.possible == []

    def test_same_document_is_not_repeated_as_a_warning(self):
        make_person(
            contact_email="anna@example.org", id_document_type="dni", id_document_number="00000000T"
        )
        check = find_duplicates(
            contact_email="anna@example.org", id_document_type="dni", id_document_number="00000000T"
        )
        assert check.same_document is not None
        assert check.possible == []

    def test_anonymised_people_are_ignored(self):
        make_person(
            contact_email="anna@example.org",
            status=Person.Status.ANONYMISED,
            anonymous_ref="A-0001",
        )
        assert find_duplicates(contact_email="anna@example.org").possible == []


def test_no_model_has_iban_or_health_fields():
    # CLAUDE.md i spec 00 (RN-05; CA-15.6): cap camp d'IBAN ni de salut fora del mandat (05a).
    forbidden = ("iban", "health", "salut", "medical", "medic")
    project_models = [m for m in apps.get_models() if m.__module__.startswith("apps.")]
    fields = [f"{m.__name__}.{f.name}" for m in project_models for f in m._meta.get_fields()]
    assert not [f for f in fields if any(word in f.lower() for word in forbidden)]
