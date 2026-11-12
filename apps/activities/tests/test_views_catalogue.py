"""Pantalles dels catàlegs a l'administració (T-M02-05; P-M02-A; RN-M02-01 i RN-M02-05; CA-M02-01 i
CA-M02-26, amb l'avís del canvi de preu).

Els permisos per ruta són a `test_route_permissions.py`. Aquí es prova que cada pantalla fa el que
toca amb el permís: desa pels serveis, mostra els errors sense desar res i avisa qui ha d'avisar.
Només dades inventades.
"""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.activities import catalogue
from apps.activities.forms import EuroField
from apps.activities.models import (
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    TrainingCatalogueEntry,
)
from apps.core.models import AuditEntry, OutgoingEmail
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import REASON, admin_with_mail, an_entry, an_outing, client_for, general

pytestmark = pytest.mark.django_db

K = TrainingCatalogueEntry.Kind
COURSES = reverse("administration:catalogue_courses")
SPECIALITIES = reverse("administration:catalogue_specialities")


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


@pytest.fixture
def client(manager):
    return client_for(manager)


def text(response):
    return response.content.decode()


def entry_data(**fields):
    return {
        "name": "Curs inventat de la pantalla",
        "default_places": "8",
        "price_member_cents": "45",
        "price_non_member_cents": "60,50",
        "department": general().pk,
        **fields,
    }


# --- Imports en euros -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("written", "cents"),
    [("45", 4500), ("45,5", 4550), ("45.50", 4550), ("0", 0), (" 1 200,00 € ", 120000)],
)
def test_amounts_are_written_in_euros_and_stored_in_cents(written, cents):
    assert EuroField().clean(written) == cents


@pytest.mark.parametrize("written", ["-1", "45,555", "quaranta", "45,50,1", "1e3", "4.5.0"])
def test_wrong_amounts_are_rejected(written):
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        EuroField().clean(written)


def test_an_amount_is_shown_back_with_two_decimals():
    assert EuroField().prepare_value(4550) == "45,50"
    assert EuroField(required=False).clean("") is None


# --- RN-M02-01: dues pantalles separades ----------------------------------------------------------


def test_rn_m02_01_courses_and_specialities_have_separate_screens(client, manager):
    an_entry(manager, name="Curs de la primera pantalla")
    an_entry(manager, kind=K.SPECIALITY, name="Especialitat de la segona pantalla")
    courses, specialities = text(client.get(COURSES)), text(client.get(SPECIALITIES))
    assert "Catàleg de cursos" in courses
    assert "Curs de la primera pantalla" in courses
    assert "Especialitat de la segona pantalla" not in courses
    assert "Catàleg d&#x27;especialitats" in specialities
    assert "Especialitat de la segona pantalla" in specialities
    assert "Curs de la primera pantalla" not in specialities


def test_an_empty_catalogue_says_so(client):
    assert "Encara no hi ha cap fitxa" in text(client.get(COURSES))


# --- Afegir i editar una fitxa --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("route", "kind", "back"),
    [
        ("administration:catalogue_course_add", K.COURSE, COURSES),
        ("administration:catalogue_speciality_add", K.SPECIALITY, SPECIALITIES),
    ],
)
def test_adding_an_entry_saves_it_in_its_catalogue(client, manager, route, kind, back):
    response = client.post(reverse(route), entry_data(reinforcement_price_cents="30"))
    assert (response.status_code, response["Location"]) == (303, back)
    entry = TrainingCatalogueEntry.objects.get()
    assert entry.kind == kind
    assert (entry.price_member_cents, entry.price_non_member_cents) == (4500, 6050)
    assert entry.reinforcement_price_cents == 3000
    assert entry.prices.count() == 1  # la primera versió dels preus
    page = text(client.get(back))
    assert "Fitxa desada" in page
    assert "Curs inventat de la pantalla" in page
    assert "45,00\xa0€" in page or "45,00 €" in page
    created = AuditEntry.objects.get(action=catalogue.ENTRY_CREATED)
    assert created.actor_account == manager


WRONG_ENTRIES = {
    "sense nom": ({"name": ""}, "Aquest camp és obligatori"),
    "zero places": ({"default_places": "0"}, "més gran o igual"),
    "preu amb lletres": ({"price_member_cents": "barat"}, "Escriu l&#x27;import en euros"),
    "preu negatiu": ({"price_non_member_cents": "-5"}, "Escriu l&#x27;import en euros"),
    "sense departament": ({"department": ""}, "Aquest camp és obligatori"),
}


@pytest.mark.parametrize(("fields", "message"), WRONG_ENTRIES.values(), ids=WRONG_ENTRIES.keys())
def test_a_wrong_entry_is_shown_with_its_error_and_nothing_is_saved(client, fields, message):
    response = client.post(reverse("administration:catalogue_course_add"), entry_data(**fields))
    assert response.status_code == 200
    assert message in text(response)
    assert not TrainingCatalogueEntry.objects.exists()


def test_a_repeated_name_is_explained_by_the_service(client, manager):
    an_entry(manager, name="Curs inventat de la pantalla")
    response = client.post(reverse("administration:catalogue_course_add"), entry_data())
    assert response.status_code == 200
    assert 'role="alert"' in text(response)
    assert TrainingCatalogueEntry.objects.count() == 1
    # El mateix nom a l'altre catàleg sí que es pot (RN-M02-01).
    response = client.post(reverse("administration:catalogue_speciality_add"), entry_data())
    assert response.status_code == 303


def test_editing_an_entry_never_touches_its_prices(client, manager):
    entry = an_entry(manager)
    url = reverse("administration:catalogue_entry_edit", args=[entry.pk])
    form = text(client.get(url))
    assert 'name="description"' in form
    assert 'name="price_member_cents"' not in form  # els preus tenen la seva pantalla
    data = entry_data(name=entry.name, description="Descripció inventada.", price_member_cents="1")
    response = client.post(url, data)
    assert response.status_code == 303
    entry.refresh_from_db()
    assert entry.description == "Descripció inventada."
    assert entry.price_member_cents == 4500
    assert entry.prices.count() == 1
    changed = AuditEntry.objects.get(action=catalogue.ENTRY_UPDATED)
    assert (changed.field, changed.old_value) == ("description", "")
    # Sense canvis, ho diu i no deixa res al registre.
    client.post(url, data)
    assert "No hi havia cap canvi per desar" in text(client.get(COURSES))
    assert AuditEntry.objects.filter(action=catalogue.ENTRY_UPDATED).count() == 1


def test_an_entry_that_does_not_exist_is_not_found(client):
    for name in ("catalogue_entry_edit", "catalogue_entry_prices"):
        assert client.get(reverse(f"administration:{name}", args=[999_999])).status_code == 404


# --- Preus: CA-M02-01 i CA-M02-26 -----------------------------------------------------------------


def price_data(**fields):
    return {
        "price_member_cents": "50",
        "price_non_member_cents": "60",
        "valid_from": (timezone.localdate() + datetime.timedelta(days=30)).isoformat(),
        "note": REASON,
        **fields,
    }


def test_ca_m02_26_a_price_change_warns_the_treasurer_and_the_board(client, manager, make_admin):  # noqa: F811
    """CA-M02-26: canvi de 45 a 50 amb data d'entrada en vigor. El tresorer i la junta reben el
    correu amb el preu anterior i el nou; qui no és ni l'un ni l'altre, no."""
    admin_with_mail(make_admin, "treasurer", "tresoreria@example.org")
    admin_with_mail(make_admin, "board", "junta@example.org")
    admin_with_mail(make_admin, "secretary", "secretaria@example.org")
    entry = an_entry(manager)
    url = reverse("administration:catalogue_entry_prices", args=[entry.pk])
    assert "Canvia els preus" in text(client.get(url))

    response = client.post(url, price_data())
    assert (response.status_code, response["Location"]) == (303, COURSES)
    today = timezone.localdate()
    later = today + datetime.timedelta(days=30)
    assert catalogue.price_on(entry, today).member_cents == 4500
    assert catalogue.price_on(entry, later).member_cents == 5000
    emails = OutgoingEmail.objects.filter(template="avis-canvi-diners")
    assert sorted(emails.values_list("to_address", flat=True)) == [
        "junta@example.org",
        "tresoreria@example.org",
    ]
    body = emails.first().body_text
    assert "45,00" in body and "50,00" in body
    assert entry.name in body and REASON in body
    # La llista diu el preu d'avui i el que vindrà.
    page = text(client.get(COURSES))
    assert "Preus desats" in page
    assert f"Des del {later:%d/%m/%Y}" in page
    # L'historial només s'hi afegeix.
    history = text(client.get(url))
    assert "Encara no vigent" in history
    assert REASON in history


WRONG_PRICES = {
    "sense motiu": ({"note": "  "}, "Cal escriure el motiu del canvi de preu"),
    "data passada": ({"valid_from": "2020-01-01"}, "no pot ser passada"),
    "sense data": ({"valid_from": ""}, "Aquest camp és obligatori"),
    "el mateix preu": ({"price_member_cents": "45"}, "El preu és el mateix"),
    "import mal escrit": ({"price_member_cents": "cinquanta"}, "Escriu l&#x27;import en euros"),
}


@pytest.mark.parametrize(("fields", "message"), WRONG_PRICES.values(), ids=WRONG_PRICES.keys())
def test_a_wrong_price_change_saves_nothing_and_warns_nobody(
    client,
    manager,
    make_admin,  # noqa: F811
    fields,
    message,
):
    admin_with_mail(make_admin, "treasurer", "tresoreria@example.org")
    entry = an_entry(manager)
    url = reverse("administration:catalogue_entry_prices", args=[entry.pk])
    response = client.post(url, price_data(**fields))
    assert response.status_code == 200
    assert message in text(response)
    assert entry.prices.count() == 1
    assert not OutgoingEmail.objects.exists()


def test_ca_m02_01_an_existing_activity_keeps_its_price(client, manager):
    """CA-M02-01, per la pantalla: es canvia el preu del catàleg des d'avui i el curs que ja
    existia conserva el seu; el canvi queda al registre amb el valor anterior."""
    from .helpers import a_course

    entry = an_entry(manager)
    course = a_course(manager, entry)
    url = reverse("administration:catalogue_entry_prices", args=[entry.pk])
    client.post(url, price_data(valid_from=timezone.localdate().isoformat()))
    course.refresh_from_db()
    assert course.price_member_cents == 4500
    change = AuditEntry.objects.get(action=catalogue.PRICE_CHANGED, field="price_member_cents")
    assert (change.old_value, change.new_value, change.reason) == (4500, 5000, REASON)


# --- Activar i desactivar -------------------------------------------------------------------------


def test_an_entry_is_deactivated_and_activated_again_never_deleted(client, manager):
    entry = an_entry(manager)
    url = reverse("administration:catalogue_entry_active", args=[entry.pk])
    assert client.get(url).status_code == 405  # només POST
    assert client.post(url, {"actiu": "0"}).status_code == 303
    entry.refresh_from_db()
    assert entry.active is False
    page = text(client.get(COURSES))
    assert "Desactivat" in page and "Torna a activar" in page
    # Una fitxa desactivada no es pot triar per a un curs nou.
    assert entry.name not in text(client.get(reverse("administration:activity_course_add")))
    client.post(url, {"actiu": "1"})
    entry.refresh_from_db()
    assert entry.active is True
    assert TrainingCatalogueEntry.objects.count() == 1


# --- Tipus de sortida i subtipus ------------------------------------------------------------------

TYPES = reverse("administration:outing_types")


def test_types_and_subtypes_are_added_from_the_same_screen(client):
    page = text(client.get(TYPES))
    for name in ("Immersió", "Medi ambient", "Sèniors", "Jornada oberta", "Neteja"):
        assert name in page
    response = client.post(
        TYPES,
        {
            "form": "tipus",
            "tipus-name": "Tipus inventat",
            "tipus-is_environmental": "on",
            "tipus-default_department": general().pk,
        },
    )
    assert response.status_code == 303
    assert OutingType.objects.get(name="Tipus inventat").is_environmental is True
    response = client.post(TYPES, {"form": "subtipus", "subtipus-name": "Cens inventat"})
    assert response.status_code == 303
    assert EnvironmentalSubtype.objects.filter(name="Cens inventat", active=True).exists()


def test_a_repeated_type_or_subtype_is_rejected_on_its_own_form(client):
    response = client.post(TYPES, {"form": "subtipus", "subtipus-name": "Neteja"})
    assert response.status_code == 200
    assert "Ja n&#x27;hi ha un amb aquest nom" in text(response)
    response = client.post(TYPES, {"form": "subtipus", "subtipus-name": ""})
    assert "Aquest camp és obligatori" in text(response)
    response = client.post(
        TYPES,
        {"form": "tipus", "tipus-name": "Immersió", "tipus-default_department": general().pk},
    )
    assert "Ja n&#x27;hi ha un amb aquest nom" in text(response)
    assert OutingType.objects.count() == 4
    assert EnvironmentalSubtype.objects.count() == 1
    # Un formulari que no és cap dels dos no desa res.
    assert client.post(TYPES, {"form": "altres", "name": "X"}).status_code == 200
    assert OutingType.objects.count() == 4


def test_a_deactivated_type_or_subtype_cannot_be_chosen_for_a_new_outing(client):
    seniors = OutingType.objects.get(name="Sèniors")
    cleaning = EnvironmentalSubtype.objects.get(name="Neteja")
    client.post(reverse("administration:outing_type_active", args=[seniors.pk]), {"actiu": "0"})
    client.post(reverse("administration:outing_subtype_active", args=[cleaning.pk]), {"actiu": "0"})
    seniors.refresh_from_db()
    cleaning.refresh_from_db()
    assert (seniors.active, cleaning.active) == (False, False)
    form = text(client.get(reverse("administration:activity_outing_add")))
    assert ">Sèniors<" not in form and ">Neteja<" not in form
    assert ">Immersió<" in form


# --- Projectes ------------------------------------------------------------------------------------

PROJECTS = reverse("administration:projects")


def test_a_project_is_created_and_shows_its_outings(client, manager):
    assert "Encara no hi ha cap projecte" in text(client.get(PROJECTS))
    response = client.post(
        PROJECTS,
        {
            "name": "Projecte inventat",
            "objective": "Objectiu inventat.",
            "department": general().pk,
        },
    )
    assert response.status_code == 303
    project = EnvironmentalProject.objects.get()
    an_outing(
        manager,
        title="Neteja inventada del port",
        outing_type=OutingType.objects.get(name="Medi ambient"),
        subtype=EnvironmentalSubtype.objects.get(name="Neteja"),
        project=project,
    )
    an_outing(manager, title="Immersió inventada sense projecte")
    detail = text(client.get(reverse("administration:project_detail", args=[project.pk])))
    assert "Objectiu inventat." in detail
    assert "Neteja inventada del port" in detail
    assert "Immersió inventada sense projecte" not in detail
    assert client.get(reverse("administration:project_detail", args=[999_999])).status_code == 404


def test_a_project_needs_a_name_and_an_objective(client):
    response = client.post(PROJECTS, {"name": "Projecte", "objective": "", "department": ""})
    assert response.status_code == 200
    assert "Cal escriure l&#x27;objectiu del projecte" in text(response)
    assert not EnvironmentalProject.objects.exists()


# --- Nivells i mode per defecte (T-M02-29; addenda de la 058) -------------------------------------

LEVELS = reverse("administration:certification_levels")


def test_levels_are_added_and_deactivated_from_their_screen(client):
    from apps.activities.models import CertificationLevel

    assert "Encara no hi ha cap nivell" in text(client.get(LEVELS))
    assert client.post(LEVELS, {"name": "Nivell inventat B1", "rank": "10"}).status_code == 303
    assert client.post(LEVELS, {"name": "Nivell inventat B2", "rank": "20"}).status_code == 303
    response = client.post(LEVELS, {"name": "Un altre", "rank": "10"})
    assert response.status_code == 200
    assert "Ja hi ha un nivell amb aquest ordre" in text(response)
    assert "Aquest camp és obligatori" in text(client.post(LEVELS, {"name": "", "rank": ""}))
    assert list(CertificationLevel.objects.values_list("name", "rank")) == [
        ("Nivell inventat B1", 10),
        ("Nivell inventat B2", 20),
    ]
    level = CertificationLevel.objects.get(rank=10)
    toggle = reverse("administration:certification_level_active", args=[level.pk])
    assert client.post(toggle, {"actiu": "0"}).status_code == 303
    level.refresh_from_db()
    assert level.active is False
    # Un nivell desactivat no es pot triar per a una activitat nova.
    form = text(client.get(reverse("administration:activity_outing_add")))
    assert "Nivell inventat B2" in form and "Nivell inventat B1" not in form


def test_ca_m02_34_the_default_mode_of_a_type_is_changed_from_the_screen(client, manager):
    """CA-M02-34 per la pantalla: es posa «bloqueig» al tipus i la sortida nova hi neix."""
    seniors = OutingType.objects.get(name="Sèniors")
    url = reverse("administration:outing_type_mode", args=[seniors.pk])
    assert client.get(url).status_code == 405
    assert client.post(url, {"mode": "block"}).status_code == 303
    seniors.refresh_from_db()
    assert seniors.default_requirements_mode == "block"
    assert "Mode per defecte de «Sèniors» desat" in text(client.get(TYPES))
    client.post(url, {"mode": "inventat"})
    seniors.refresh_from_db()
    assert seniors.default_requirements_mode == "block"
    outing = an_outing(manager, outing_type=seniors)
    assert outing.requirements_mode == "block"
    client.post(url, {"mode": ""})
    seniors.refresh_from_db()
    assert seniors.default_requirements_mode == ""


def test_an_entry_keeps_its_default_mode_and_minimum_age(client):
    data = entry_data(default_requirements_mode="block", min_age="14")
    assert client.post(reverse("administration:catalogue_course_add"), data).status_code == 303
    entry = TrainingCatalogueEntry.objects.get()
    assert (entry.default_requirements_mode, entry.min_age) == ("block", 14)
    response = client.post(
        reverse("administration:catalogue_course_add"),
        entry_data(name="Un altre curs", min_age="150"),
    )
    assert response.status_code == 200
    assert TrainingCatalogueEntry.objects.count() == 1
