"""«Fer-se soci» darrere de la sessió (T-M01-53 b; decisió 108, C.1 i D.1): sense sessió,
l'anunci amb «Entra» i «Crea el compte» que tornen aquí, sense preu ni formulari; amb el compte,
l'alta «per a mi» va a la persona del compte i les dades de soci es demanen aquí. Només dades
inventades."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.models import Person
from apps.members.models import MemberRequest
from apps.members.tests.test_join import (  # noqa: F401 (fixture texts)
    PUBLIC,
    form_data,
    texts,
    visitor,
)

pytestmark = pytest.mark.django_db
URL = reverse(PUBLIC)


def _self(**overrides):
    return form_data(for_whom="self", first_name="Visitant", last_name="Prova", **overrides)


def test_without_a_session_only_the_announcement_and_nothing_is_saved(texts):  # noqa: F811
    html = Client().get(URL).content.decode()
    assert f"{reverse('accounts:signup')}?next=/fer-se-soci/" in html
    assert f"{reverse('accounts:login')}?next=/fer-se-soci/" in html
    assert "quota anual" not in html and 'name="birth_date"' not in html
    before = Person.objects.count()
    assert Client().post(URL, form_data()).status_code == 200
    assert Person.objects.count() == before and not MemberRequest.objects.exists()


def test_the_form_comes_with_the_account_name_and_email(texts):  # noqa: F811
    client = visitor()
    html = client.get(URL).content.decode()
    assert 'value="Visitant"' in html and "visitant" in html and "@example.org" in html
    assert 'name="for_whom"' in html and "quota anual" in html


def test_for_me_goes_to_the_account_person_and_fills_only_what_is_missing(texts):  # noqa: F811
    client = visitor()
    person = Person.objects.order_by("-pk").first()
    response = client.post(URL, _self())
    assert response.status_code == 303
    join_request = MemberRequest.objects.get()
    assert join_request.person == person
    person.refresh_from_db()
    assert person.id_document_number == "12345678Z" and person.phone
    assert Person.objects.filter(id_document_number="12345678Z").count() == 1


def test_for_me_with_a_document_of_another_person_does_not_merge(texts):  # noqa: F811
    other = Person.objects.create(
        first_name="Altra", origin=Person.Origin.WEB, id_document_type=Person.DocumentType.DNI,
        id_document_number="12345678Z",
    )  # fmt: skip
    client = visitor()
    person = Person.objects.order_by("-pk").first()
    assert client.post(URL, _self()).status_code == 303
    join_request = MemberRequest.objects.get()
    assert join_request.person == person
    assert join_request.duplicate_warning == [{"match": "document", "person_id": other.pk}]
    person.refresh_from_db()
    assert person.id_document_number == ""


def test_for_me_under_14_is_refused(texts):  # noqa: F811
    client = visitor()
    response = client.post(URL, _self(birth_date="2016-04-01"))
    assert response.status_code == 200 and "Per a un menor de 14 anys" in response.content.decode()
    assert not MemberRequest.objects.exists()
