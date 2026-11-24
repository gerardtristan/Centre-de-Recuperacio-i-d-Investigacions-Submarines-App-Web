"""Titulacions d'una persona a l'administració (T-M02-52b; RN-M02-32; AC29, P-459; P-572): des de
la fitxa del soci, la llista, carregar i verificar. Només dades inventades."""

import pytest
from django.urls import reverse

from apps.activities import certification_records as records
from apps.activities.models import CertificationLevel, DiverCertification
from apps.activities.tests.helpers import a_member
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client

pytestmark = pytest.mark.django_db
R = Role.Code
S = DiverCertification.Source


@pytest.fixture
def person():
    return a_member("Bussejadora", account=False)


@pytest.fixture
def level():
    return CertificationLevel.objects.create(name="Nivell inventat", rank=999)


def url(person):
    return reverse("administration:person_certifications", args=[person.pk])


def test_rn_m02_32_the_secretary_loads_and_verifies_from_the_screen(person, level, make_admin):  # noqa: F811
    client = admin_client(make_admin(R.SECRETARY))
    data = {"accio": "carrega", "source": S.IMPORTED, "level": level.pk, "number": "B-77"}
    assert client.post(url(person), data).status_code == 303
    loaded = DiverCertification.objects.get(person=person)
    assert (loaded.source, loaded.number, loaded.is_verified) == (S.IMPORTED, "B-77", False)
    page = client.get(url(person)).content.decode()
    assert "Nivell inventat" in page and "sense verificar" in page and "Verifica" in page
    assert "Tria…" in page and "---------" not in page  # T-M02-49: desplegables en català
    response = client.post(url(person), {"accio": "verifica", "titulacio": loaded.pk})
    assert response.status_code == 303
    loaded.refresh_from_db()
    assert loaded.is_verified
    assert AuditEntry.objects.filter(action=records.VERIFIED).count() == 1


def test_an_invalid_load_shows_the_error_and_saves_nothing(person, make_admin):  # noqa: F811
    client = admin_client(make_admin(R.SECRETARY))
    response = client.post(url(person), {"accio": "carrega", "source": S.DECLARED})
    assert response.status_code == 200
    assert "Cal un nivell o una especialitat" in response.content.decode()
    assert not DiverCertification.objects.exists()


def test_the_board_only_reads(person, level, make_admin):  # noqa: F811
    DiverCertification.objects.create(person=person, level=level, source=S.DECLARED)
    client = admin_client(make_admin(R.BOARD))
    page = client.get(url(person)).content.decode()
    assert "Nivell inventat" in page
    assert "Carrega la titulació" not in page and ">Verifica<" not in page
    pending = DiverCertification.objects.get()
    assert (
        client.post(url(person), {"accio": "verifica", "titulacio": pending.pk}).status_code == 404
    )
    data = {"accio": "carrega", "source": S.DECLARED, "level": level.pk}
    assert client.post(url(person), data).status_code == 404
    assert (
        DiverCertification.objects.count() == 1 and not DiverCertification.objects.get().is_verified
    )


@pytest.mark.parametrize("role", [R.TREASURER, R.PRESIDENT, R.INSTRUCTOR])
def test_without_ac29_the_screen_is_not_found(person, make_admin, role):  # noqa: F811
    assert admin_client(make_admin(role)).get(url(person)).status_code == 404


def test_nobody_loads_or_verifies_their_own(level, make_admin):  # noqa: F811
    secretary = make_admin(R.SECRETARY)
    own = DiverCertification.objects.create(person=secretary.person, level=level, source=S.DECLARED)
    client = admin_client(secretary)
    page = client.get(url(secretary.person)).content.decode()
    assert "Carrega la titulació" not in page
    response = client.post(url(secretary.person), {"accio": "verifica", "titulacio": own.pk})
    assert response.status_code == 303
    own.refresh_from_db()
    assert not own.is_verified


def test_the_member_record_links_to_the_certifications_only_with_ac29(person, make_admin):  # noqa: F811
    member = person.member
    detail = reverse("administration:member_detail", args=[member.pk])
    page = admin_client(make_admin(R.SECRETARY)).get(detail).content.decode()
    assert url(person) in page
    page = admin_client(make_admin(R.TREASURER)).get(detail).content.decode()
    assert url(person) not in page
