"""Pantalles d'inscripció d'un convidat: el formulari públic i la inscripció presencial (T-M02-14 i
T-M02-34; RN-M02-35; CA-M02-10, 11 i 37; P-458). El servei té les seves proves a
`test_guests.py`. Només dades inventades."""

import html

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities import guests
from apps.activities.models import Enrolment
from apps.core.models import Consent, GuestLink, LegalText, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import an_open_outing, an_outing

pytestmark = pytest.mark.django_db

EMAIL = "convidada@example.org"


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


def test_ca_m02_11_a_guest_enrols_from_the_web_and_gets_the_link(client, manager):
    publish("privacy", guests.ADULT)
    outing = an_open_outing(manager, open_to_non_members=True)
    page = html.unescape(client.get(url(outing)).content.decode())
    assert "Soc major d'edat" in page and guests.ADULT_PROPOSAL in page
    response = client.post(url(outing), post_data())
    assert response.status_code == 303 and response["Location"] == url(outing)
    row = Enrolment.objects.get()
    assert (row.channel, row.person.contact_email) == (Enrolment.Channel.GUEST, EMAIL)
    assert GuestLink.objects.filter(person=row.person).exists()
    assert "Inscripció enviada" in client.get(url(outing)).content.decode()


def test_ca_m02_37_without_the_adult_box_nobody_is_enrolled(client, manager):
    publish("privacy", guests.ADULT)
    outing = an_open_outing(manager, open_to_non_members=True)
    response = client.post(url(outing), post_data(adult_declared=None))
    assert response.status_code == 200 and not Person.objects.filter(contact_email=EMAIL).exists()
    assert "major d'edat" in html.unescape(response.content.decode())


def test_p_458_without_the_published_adult_text_the_form_rejects(client, manager):
    """A producció, fins que la junta validi el text (P-458): cap inscripció de convidat."""
    publish("privacy")
    outing = an_open_outing(manager, open_to_non_members=True)
    assert "Inscriu-me" not in client.get(url(outing)).content.decode()
    response = client.post(url(outing), post_data())
    assert response.status_code == 200 and not Enrolment.objects.exists()
    assert not Person.objects.filter(contact_email=EMAIL).exists()


def test_ca_m02_10_members_only_and_non_public_activities(client, manager):
    publish("privacy", guests.ADULT)
    members_only = an_open_outing(manager)
    page = html.unescape(client.get(url(members_only)).content.decode())
    assert "només per a socis" in page and "Inscriu-me" not in page
    assert client.post(url(members_only), post_data()).status_code == 200
    assert not Enrolment.objects.exists()
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
