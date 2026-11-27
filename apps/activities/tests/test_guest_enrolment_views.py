"""Inscripció d'un no soci: des del web, amb la sessió del compte personal (T-M02-54; decisió
108, C.1), i la inscripció presencial (T-M02-14 i T-M02-34; RN-M02-35; CA-M02-37; P-458).
El servei té les seves proves a `test_guests.py`. Només dades inventades."""

import html
from urllib.parse import parse_qs, urlsplit

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.activities import guests
from apps.activities.models import Enrolment
from apps.core.models import Consent, LegalText, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_personal_account, an_open_outing, an_outing

pytestmark = pytest.mark.django_db

EMAIL = "convidada@example.org"
PASSWORD = "contrasenya-de-proves-1954"  # noqa: S105 (dada inventada de proves)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def publish(*kinds):
    contents = {"privacy": "Política inventada.", guests.ADULT: guests.ADULT_PROPOSAL}
    for kind in kinds:
        LegalText.objects.create(kind=kind, version=1, content=contents[kind])


def url(activity):
    return reverse("activities:guest_enrol", args=[activity.pk])


def post_data(**fields):
    data = {"first_name": "Mar", "last_name": "Convidada", "contact_email": EMAIL,
            "adult_declared": "on", "accept_privacy": "on", **fields}  # fmt: skip
    return {k: v for k, v in data.items() if v is not None}


def test_t_m02_54_without_a_session_it_goes_to_log_in_and_comes_back(client, manager):
    """Decisió 108, C.1: apuntar-se com a no soci demana el compte personal. Cap formulari."""
    outing = an_open_outing(manager, open_to_non_members=True)
    response = client.get(url(outing))
    assert response.status_code == 302
    login = urlsplit(response["Location"])
    assert login.path == reverse("accounts:login")
    assert parse_qs(login.query)["next"] == [url(outing)]  # torna a l'activitat
    assert client.post(url(outing), post_data()).status_code == 405
    assert (
        not Enrolment.objects.exists() and not Person.objects.filter(contact_email=EMAIL).exists()
    )


def test_t_m02_54_after_logging_in_it_returns_to_the_activity(client, manager):
    outing = an_open_outing(manager, open_to_non_members=True)
    account = a_personal_account()
    account.set_password(PASSWORD)
    account.save()
    response = client.post(
        reverse("accounts:login"),
        {"login": account.login, "password": PASSWORD, "next": url(outing)},
    )
    assert response.status_code == 302 and response["Location"] == url(outing)
    enrol = reverse("activities:member_enrol", args=[outing.pk])
    assert client.get(url(outing))["Location"] == enrol


def test_t_m02_54_next_never_goes_outside(client, manager):
    account = a_personal_account()
    account.set_password(PASSWORD)
    account.save()
    response = client.post(
        reverse("accounts:login"),
        {"login": account.login, "password": PASSWORD, "next": "https://exemple.cat/"},
    )
    assert response.status_code == 302 and "exemple.cat" not in response["Location"]


def test_t_m02_54_with_a_session_it_goes_to_the_personal_area(login_as, manager):
    outing = an_open_outing(manager, open_to_non_members=True)
    client = login_as(a_personal_account(), AREA_PERSONAL)
    response = client.get(url(outing))
    assert response["Location"] == reverse("activities:member_enrol", args=[outing.pk])


def test_ca_m02_10_a_non_public_activity_is_not_found(client, manager):
    draft = an_outing(manager, open_to_non_members=True)
    assert client.get(url(draft)).status_code == 404


def test_t_m02_14_in_person_the_desk_marks_the_boxes(login_as, manager):
    publish("privacy", guests.ADULT)
    outing = an_open_outing(manager, open_to_non_members=True)
    client = login_as(manager, AREA_ADMIN)
    detail = reverse("administration:activity_detail", args=[outing.pk])
    assert "Inscripció presencial d'un convidat" in html.unescape(
        client.get(detail).content.decode()
    )
    data = {f"presencial-{k}": v for k, v in post_data().items()}
    response = client.post(detail, {**data, "inscripcio_presencial": "1"})
    assert response.status_code == 303
    row = Enrolment.objects.get()
    assert row.channel == Enrolment.Channel.DESK
    assert set(Consent.objects.filter(person=row.person).values_list("channel", flat=True)) == {
        Consent.Channel.IN_PERSON
    }


def test_t_m02_14_the_desk_needs_ac5(login_as, make_admin, manager):  # noqa: F811
    publish("privacy", guests.ADULT)
    outing = an_open_outing(manager, open_to_non_members=True)
    client = login_as(make_admin(Role.Code.SECRETARY), AREA_ADMIN)
    detail = reverse("administration:activity_detail", args=[outing.pk])
    data = {f"presencial-{k}": v for k, v in post_data().items()}
    assert client.post(detail, {**data, "inscripcio_presencial": "1"}).status_code == 404
    assert not Enrolment.objects.exists()
