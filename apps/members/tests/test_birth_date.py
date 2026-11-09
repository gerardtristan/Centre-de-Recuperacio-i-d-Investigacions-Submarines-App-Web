"""Data de naixement a la fitxa i al llistat de socis (T-M01-33; 058, RN-M01-48, RN-M01-55,
CA-M01-38).

Amb C1 (secretaria i administrador, protegit): la data a la fitxa i el filtre «sense data de
naixement». Sense C1: «major d'edat», «menor d'edat» o «edat desconeguda», i el filtre no
existeix ni amb una petició manipulada. Mai la data al llistat ni a l'exportació.
Només dades inventades.
"""

from datetime import date
from html import unescape

import pytest
from django.urls import reverse

from apps.core.models import AuditEntry, Role, RolePermission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.tests.test_roster import (
    DETAIL,
    EXPORTED,
    FORMATS,
    LIST,
    admin_client,
    as_text,
    export,
    make_member,
)

ADULT_BIRTH = date(1988, 10, 8)
ADULT_TEXTS = ("08/10/1988", "1988-10-08", "8 d'octubre")
FILTER_LABEL = "Només els que no tenen data de naixement"
MISSING = "Sense data de naixement"
C1_ROLES = ["secretary", "administrator"]


@pytest.fixture
def adult(db):
    return make_member(427, "Marta", "Puig", birth_date=ADULT_BIRTH)


@pytest.fixture
def without_date(db):
    return make_member(870, "Albert", "Gil")  # com un soci importat de Cluber (RN-M01-55)


def detail(client, member):
    return unescape(client.get(reverse(DETAIL, args=[member.pk])).content.decode())


def listed(client, **params):
    return unescape(client.get(reverse(LIST), params).content.decode())


# --- Fitxa (CA-M01-38) ----------------------------------------------------------------------


@pytest.mark.parametrize("role", C1_ROLES)
def test_c1_sees_the_birth_date(make_admin, adult, role):  # noqa: F811
    text = detail(admin_client(make_admin(role)), adult)
    assert "Data de naixement" in text and "08/10/1988" in text
    assert "Major d'edat" not in text


@pytest.mark.parametrize("role", C1_ROLES)
def test_c1_sees_that_the_date_is_missing(make_admin, without_date, role):  # noqa: F811
    text = detail(admin_client(make_admin(role)), without_date)
    assert MISSING in text and "Edat desconeguda" not in text


def test_treasurer_sees_only_the_age_band(make_admin, adult):  # noqa: F811
    text = detail(admin_client(make_admin("treasurer")), adult)
    assert "Major d'edat" in text
    assert "naixement" not in text.lower()
    for value in ADULT_TEXTS:
        assert value not in text


@pytest.mark.parametrize(
    ("birth", "band"),
    [(date(2012, 5, 1), "Menor d'edat"), (None, "Edat desconeguda")],
)
def test_treasurer_sees_minor_or_unknown(make_admin, birth, band):  # noqa: F811
    member = make_member(501, "Biel", "Rap", type_code="supporter", birth_date=birth)
    text = detail(admin_client(make_admin("treasurer")), member)
    assert band in text and "naixement" not in text.lower()


def test_roles_without_p4_still_get_not_found(make_admin, adult):  # noqa: F811
    # L'instructor veurà la franja d'edat a les seves sessions (02, T-M02-32), no la fitxa.
    client = admin_client(make_admin("instructor"))
    assert client.get(reverse(DETAIL, args=[adult.pk])).status_code == 404


# --- Llistat i filtre «sense data de naixement» (RN-M01-55) --------------------------------


@pytest.mark.parametrize("role", C1_ROLES)
def test_c1_list_marks_missing_dates_but_never_shows_one(make_admin, adult, without_date, role):  # noqa: F811
    text = listed(admin_client(make_admin(role)))
    assert FILTER_LABEL in text
    assert text.count(MISSING) == 1  # només Albert, que no en té
    for value in ADULT_TEXTS:
        assert value not in text


@pytest.mark.parametrize("role", C1_ROLES)
def test_c1_filters_members_without_birth_date(make_admin, adult, without_date, role):  # noqa: F811
    text = listed(admin_client(make_admin(role)), sense_data="on")
    assert "Albert Gil" in text and "Marta Puig" not in text


def test_forced_filter_without_c1_does_nothing(make_admin, adult, without_date):  # noqa: F811
    text = listed(admin_client(make_admin("treasurer")), sense_data="on")
    assert "Albert Gil" in text and "Marta Puig" in text
    assert FILTER_LABEL not in text and MISSING not in text


# --- Exportació: el filtre sí, la data mai (RN-M01-71) ------------------------------------


@pytest.mark.parametrize("fmt", FORMATS)
def test_export_applies_the_filter_without_the_date(make_admin, adult, without_date, fmt):  # noqa: F811
    response = export(admin_client(make_admin("secretary")), fmt, sense_data="True")
    text = as_text(response, fmt)
    assert "Albert Gil" in text and "Marta Puig" not in text
    assert "naixement" not in text.lower()
    entry = AuditEntry.objects.get(action=EXPORTED)
    assert entry.details["filters"]["without_birth_date"] is True


def test_export_without_c1_ignores_a_forced_filter(make_admin, adult, without_date):  # noqa: F811
    treasurer = Role.objects.get(code="treasurer")
    RolePermission.objects.create(role=treasurer, permission_code="members.export", scope="all")
    response = export(admin_client(make_admin("treasurer")), "csv", sense_data="True")
    text = as_text(response, "csv")
    assert "Albert Gil" in text and "Marta Puig" in text
    for value in ADULT_TEXTS:
        assert value not in text
    entry = AuditEntry.objects.get(action=EXPORTED)
    assert entry.details["filters"]["without_birth_date"] is False


def test_c1_cannot_be_granted_to_the_treasurer(make_admin, adult):  # noqa: F811
    # C1 és protegit (058): una fila a la base de dades no el dona a cap altre rol.
    treasurer = Role.objects.get(code="treasurer")
    RolePermission.objects.create(
        role=treasurer, permission_code="members.field.birth_date", scope="all"
    )
    text = detail(admin_client(make_admin("treasurer")), adult)
    assert "08/10/1988" not in text and "Major d'edat" in text
