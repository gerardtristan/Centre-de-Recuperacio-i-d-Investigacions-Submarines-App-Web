"""Pantalles de les activitats a l'administració (T-M02-06; P-M02-B; RN-M02-02, RN-M02-06 i
RN-M02-20; CA-M02-02 i CA-M02-03 per la pantalla; L-M02-05, la part de mostrar-ho).

Els permisos per ruta són a `test_route_permissions.py`. Només dades inventades.
"""

import datetime

import pytest
from django.urls import reverse

from apps.activities import forms, services, sessions, states
from apps.activities.models import (
    Activity,
    EnvironmentalSubtype,
    OutingType,
    ProgrammeBlock,
    Session,
)
from apps.core import roles
from apps.core.models import AuditEntry, OutgoingEmail
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import (
    BEFORE_DEADLINE,
    REASON,
    a_course,
    a_person,
    admin_with_mail,
    an_entry,
    an_outing,
    at,
    client_for,
)

pytestmark = pytest.mark.django_db

S = Activity.Status
LIST = reverse("administration:activities")
COURSE_ADD = reverse("administration:activity_course_add")
OUTING_ADD = reverse("administration:activity_outing_add")


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


@pytest.fixture
def client(manager):
    return client_for(manager)


def text(response):
    return response.content.decode()


def url(name, *args):
    return reverse(f"administration:{name}", args=args)


def common(manager, **fields):
    return {
        "title": "Activitat inventada de la pantalla",
        "starts_on": "2027-06-14",
        "ends_on": "2027-06-15",
        "registration_closes_at": "2027-06-10T20:00",
        "responsible": manager.person.pk,
        **fields,
    }


def outing_data(manager, **fields):
    data = {
        "outing_type": OutingType.objects.get(name="Immersió").pk,
        "max_places": "12",
        "price_member_cents": "45",
        "price_non_member_cents": "60",
    }
    return common(manager, **{**data, **fields})


def detail(client, activity):
    return text(client.get(url("activity_detail", activity.pk)))


# --- Llistat --------------------------------------------------------------------------------------


def test_the_list_shows_live_activities_by_default_and_filters(client, manager):
    live = an_outing(manager, title="Sortida viva inventada")
    course = a_course(manager, title="Curs viu inventat")
    done = an_outing(manager, title="Sortida feta inventada")
    Activity.objects.filter(pk=done.pk).update(status=S.DONE)
    page = text(client.get(LIST))
    assert live.title in page and course.title in page
    assert done.title not in page
    assert done.title in text(client.get(LIST, {"estat": "done"}))
    only_courses = text(client.get(LIST, {"classe": "course"}))
    assert course.title in only_courses and live.title not in only_courses
    everything = text(client.get(LIST, {"estat": ""}))
    assert done.title in everything and live.title in everything
    # Un filtre que no existeix no trenca res: es tracta com «totes».
    assert client.get(LIST, {"estat": "inventat", "classe": "x"}).status_code == 200


def test_an_empty_list_says_so(client):
    assert "Cap activitat coincideix amb els filtres" in text(client.get(LIST))


# --- Crear un curs --------------------------------------------------------------------------------


def test_a_new_course_copies_places_and_prices_from_the_entry(client, manager):
    entry = an_entry(manager, default_places=8)
    response = client.post(COURSE_ADD, common(manager, catalogue_entry=entry.pk))
    course = Activity.objects.get()
    assert (response.status_code, response["Location"]) == (
        303,
        url("activity_detail", course.pk),
    )
    assert (course.kind, course.status) == ("course", S.DRAFT)
    assert course.max_places == 8
    assert (course.price_member_cents, course.price_non_member_cents) == (4500, 6000)
    assert course.payment_window_hours == 72  # valor inicial del pla (VC-21)
    assert course.department == entry.department
    assert course.responsible == manager.person
    page = detail(client, course)
    assert "Activitat creada en esborrany" in page
    assert "Esborrany" in page
    assert not OutgoingEmail.objects.exists()


def test_ca_m02_02_a_price_different_from_the_catalogue_needs_a_note_and_warns_the_treasurer(
    client,
    manager,
    make_admin,  # noqa: F811
):
    """CA-M02-02: sense nota es rebutja; amb nota es desa i el tresorer rep l'avís per correu.
    L'avís a l'app espera la safata d'avisos de la 00."""
    admin_with_mail(make_admin, "treasurer", "tresoreria@example.org")
    admin_with_mail(make_admin, "board", "junta@example.org")
    entry = an_entry(manager)
    data = common(manager, catalogue_entry=entry.pk, price_member_cents="40")
    response = client.post(COURSE_ADD, data)
    assert response.status_code == 200
    assert "cal escriure&#x27;n el motiu" in text(response)
    assert not Activity.objects.exists()
    assert not OutgoingEmail.objects.exists()

    response = client.post(COURSE_ADD, {**data, "price_override_note": REASON})
    assert response.status_code == 303
    course = Activity.objects.get()
    assert (course.price_member_cents, course.price_override_note) == (4000, REASON)
    (email,) = OutgoingEmail.objects.all()
    assert (email.template, email.to_address) == ("avis-preu-activitat", "tresoreria@example.org")
    assert "45,00" in email.body_text and "40,00" in email.body_text
    assert REASON in email.body_text and course.title in email.body_text
    notice = AuditEntry.objects.get(action=services.PRICE_NOTICE_SENT)
    assert notice.details == {"recipients": 1}
    page = detail(client, course)
    assert "Preu diferent del catàleg" in page and REASON in page


def test_ca_m02_02_editing_the_price_away_from_the_catalogue_warns_too(client, manager, make_admin):  # noqa: F811
    admin_with_mail(make_admin, "treasurer", "tresoreria@example.org")
    course = a_course(manager)
    edit = url("activity_edit", course.pk)
    form = text(client.get(edit))
    assert 'name="catalogue_entry"' not in form  # la fitxa no es canvia mai
    data = common(
        manager,
        title=course.title,
        max_places="8",
        price_member_cents="45",
        price_non_member_cents="70",
        payment_window_hours="72",
        requirements_mode="warn",
        specialities_rule="all",
        department=course.department.pk,
        responsible=course.responsible.pk,
    )
    response = client.post(edit, data)
    assert response.status_code == 200
    assert "cal escriure&#x27;n el motiu" in text(response)
    assert not OutgoingEmail.objects.exists()
    response = client.post(edit, {**data, "price_override_note": REASON})
    assert response.status_code == 303
    course.refresh_from_db()
    assert course.price_non_member_cents == 7000
    assert OutgoingEmail.objects.filter(template="avis-preu-activitat").count() == 1
    # Un canvi que no toca el preu no torna a avisar.
    client.post(edit, {**data, "price_override_note": REASON, "title": "Títol nou inventat"})
    assert OutgoingEmail.objects.count() == 1


# --- Crear una sortida: CA-M02-03 per la pantalla -------------------------------------------------


def test_a_new_outing_is_a_draft_with_its_own_prices(client, manager):
    response = client.post(OUTING_ADD, outing_data(manager, price_member_cents="0"))
    assert response.status_code == 303
    outing = Activity.objects.get()
    assert (outing.kind, outing.status) == ("outing", S.DRAFT)
    assert (outing.price_member_cents, outing.price_non_member_cents) == (0, 6000)
    assert outing.department == outing.outing_type.default_department


def test_ca_m02_03_the_subtype_rule_is_enforced_from_the_screen(client, manager):
    """CA-M02-03: medi ambient sense subtipus, rebutjada; immersió amb subtipus, rebutjada."""
    environment = OutingType.objects.get(name="Medi ambient").pk
    cleaning = EnvironmentalSubtype.objects.get(name="Neteja").pk
    response = client.post(OUTING_ADD, outing_data(manager, outing_type=environment))
    assert response.status_code == 200
    assert "ha de tenir subtipus" in text(response)
    response = client.post(OUTING_ADD, outing_data(manager, subtype=cleaning))
    assert response.status_code == 200
    assert "Només les sortides de medi ambient" in text(response)
    assert not Activity.objects.exists()
    response = client.post(
        OUTING_ADD, outing_data(manager, outing_type=environment, subtype=cleaning)
    )
    assert response.status_code == 303
    assert Activity.objects.get().subtype.name == "Neteja"


WRONG = {
    "sense títol": ({"title": ""}, "Aquest camp és obligatori"),
    "sense places": ({"max_places": ""}, "Aquest camp és obligatori"),
    "sense preu": ({"price_member_cents": ""}, "Aquest camp és obligatori"),
    "acaba abans de començar": ({"ends_on": "2027-06-13"}, "no pot ser anterior"),
    "límit després de l'inici": (
        {"registration_closes_at": "2027-06-15T10:00"},
        "no pot passar del dia",
    ),
    "data mal escrita": ({"starts_on": "demà"}, "Escriu una data vàlida"),
    "previsió sense https": ({"forecast_url": "http://example.org"}, "https://"),
}


@pytest.mark.parametrize(("fields", "message"), WRONG.values(), ids=WRONG.keys())
def test_a_wrong_outing_is_shown_with_its_error_and_nothing_is_saved(
    client, manager, fields, message
):
    response = client.post(OUTING_ADD, outing_data(manager, **fields))
    assert response.status_code == 200
    assert message in text(response)
    assert not Activity.objects.exists()


def test_the_responsible_is_chosen_only_among_who_can_manage_activities(
    client,
    manager,
    make_admin,  # noqa: F811
):
    """Minimització: la llista no ofereix tot el cens, i una persona que no hi surt no es pot
    enviar a mà."""
    other_manager = make_admin("treasurer")  # també gestiona activitats (059)
    secretary = make_admin("secretary")
    stranger = a_person("Desconeguda")
    offered = set(forms.responsible_people())
    assert offered == {manager.person, other_manager.person}
    form = text(client.get(OUTING_ADD))
    assert f'value="{stranger.pk}"' not in form
    for person in (stranger, secretary.person):
        response = client.post(OUTING_ADD, outing_data(manager, responsible=person.pk))
        assert response.status_code == 200
        assert "Trieu una opció vàlida" in text(response) or "opció vàlida" in text(response)
    assert not Activity.objects.exists()


# --- Editar ---------------------------------------------------------------------------------------


def test_editing_saves_the_changes_with_the_previous_value(client, manager):
    outing = an_outing(manager)
    edit = url("activity_edit", outing.pk)
    data = outing_data(
        manager,
        title="Títol nou inventat",
        payment_window_hours="72",
        requirements_mode="warn",
        specialities_rule="all",
        department=outing.department.pk,
        responsible=outing.responsible.pk,
    )
    response = client.post(edit, data)
    assert response.status_code == 303
    outing.refresh_from_db()
    assert outing.title == "Títol nou inventat"
    change = AuditEntry.objects.get(action=services.ACTIVITY_UPDATED, field="title")
    assert change.old_value == "Activitat inventada de proves"
    assert "Canvis desats" in detail(client, outing)
    client.post(edit, data)
    assert "No hi havia cap canvi per desar" in detail(client, outing)


@pytest.mark.parametrize("status", [S.DONE, S.CANCELLED])
def test_a_finished_or_cancelled_activity_has_no_edit_screen(client, manager, status):
    outing = an_outing(manager)
    Activity.objects.filter(pk=outing.pk).update(status=status, cancellation_reason=REASON)
    for name in ("activity_edit",):
        response = client.get(url(name, outing.pk))
        assert response.status_code == 303
    page = detail(client, outing)
    assert "ja no es pot editar" in page
    assert "Afegeix una sessió" not in page and "Edita el programa" not in page
    # I el servei ho rebutja igual si s'envia el formulari a mà.
    response = client.post(url("session_add", outing.pk), {"kind": "sea", **WHEN})
    assert response.status_code == 200
    assert "ja no es pot editar" in text(response)
    assert not Session.objects.exists()


def test_an_activity_that_does_not_exist_is_not_found(client):
    for name in ("activity_detail", "activity_edit", "activity_cancel", "activity_programme"):
        assert client.get(url(name, 999_999)).status_code == 404
    assert client.post(url("activity_step", 999_999), {"pas": "publica"}).status_code == 404


# --- Passos d'estat -------------------------------------------------------------------------------


def step(client, activity, name):
    return client.post(url("activity_step", activity.pk), {"pas": name})


def test_publish_close_and_reopen_from_the_detail(client, manager):
    outing = an_outing(manager)
    assert ">Publica<" in detail(client, outing)
    assert step(client, outing, "publica").status_code == 303
    outing.refresh_from_db()
    assert outing.status == S.OPEN
    page = detail(client, outing)
    assert "Activitat publicada" in page and "Tanca les inscripcions" in page
    assert ">Publica<" not in page

    step(client, outing, "tanca")
    outing.refresh_from_db()
    assert outing.status == S.REGISTRATION_CLOSED
    assert "Reobre les inscripcions" in detail(client, outing)

    reopen = url("activity_reopen", outing.pk)
    assert "Data límit actual" in text(client.get(reopen))
    response = client.post(reopen, {"closes_at": "2027-06-20T10:00"})  # passa del dia d'inici
    assert response.status_code == 200
    assert "no pot passar del dia" in text(response)
    assert client.post(reopen, {"closes_at": "2027-06-12T20:00"}).status_code == 303
    outing.refresh_from_db()
    assert (outing.status, outing.registration_closes_at) == (S.OPEN, at(2027, 6, 12, 20))


def test_rn_m02_20_marking_done_too_early_is_refused_from_the_screen(client, manager):
    outing = an_outing(manager)
    states.publish(outing, by=manager, now=BEFORE_DEADLINE)
    page = detail(client, outing)
    assert "Marca com a feta" not in page  # encara no toca: el botó no hi surt
    assert "Es podrà marcar com a feta a partir del 15/06/2027" in page
    step(client, outing, "feta")  # i enviat a mà, el servei ho rebutja
    outing.refresh_from_db()
    assert outing.status == S.OPEN
    assert "No es pot marcar com a feta abans" in detail(client, outing)


def test_an_activity_whose_day_has_passed_is_marked_done(client, manager):
    past = an_outing(
        manager,
        starts_on=datetime.date(2026, 1, 10),
        ends_on=datetime.date(2026, 1, 10),
        registration_closes_at=at(2026, 1, 8, 20),
    )
    Activity.objects.filter(pk=past.pk).update(status=S.OPEN)
    assert "Marca com a feta" in detail(client, past)
    step(client, past, "feta")
    past.refresh_from_db()
    assert past.status == S.DONE
    page = detail(client, past)
    assert "Activitat marcada com a feta" in page
    assert "Cancel·la l'activitat" not in page and ">Edita<" not in page


def test_a_step_that_does_not_exist_or_does_not_apply_changes_nothing(client, manager):
    outing = an_outing(manager)
    for name in ("tanca", "feta", "tanca-economicament", ""):
        assert step(client, outing, name).status_code == 303
        outing.refresh_from_db()
        assert outing.status == S.DRAFT
    assert client.get(url("activity_step", outing.pk)).status_code == 405


def test_cancelling_needs_a_reason(client, manager):
    outing = an_outing(manager)
    cancel = url("activity_cancel", outing.pk)
    assert "ja no es pot editar ni tornar a obrir" in text(client.get(cancel))
    response = client.post(cancel, {"reason": "   "})
    assert response.status_code == 200
    assert "Cal escriure el motiu" in text(response)
    outing.refresh_from_db()
    assert outing.status == S.DRAFT
    assert client.post(cancel, {"reason": REASON}).status_code == 303
    outing.refresh_from_db()
    assert (outing.status, outing.cancellation_reason) == (S.CANCELLED, REASON)
    page = detail(client, outing)
    assert "Motiu de la cancel·lació" in page and REASON in page
    # Una activitat cancel·lada no es torna a cancel·lar.
    response = client.post(cancel, {"reason": REASON})
    assert response.status_code == 200
    assert 'role="alert"' in text(response)


# --- Sessions -------------------------------------------------------------------------------------

WHEN = {"starts_at": "2027-06-14T09:00", "ends_at": "2027-06-14T11:00"}


def test_a_session_is_added_with_its_instructors(client, manager, make_admin):  # noqa: F811
    course = a_course(manager)
    teacher = make_admin("instructor").person
    add = url("session_add", course.pk)
    assert str(teacher) in text(client.get(add))
    response = client.post(
        add, {"kind": "pool", "location": "Piscina inventada", "instructors": [teacher.pk], **WHEN}
    )
    assert response.status_code == 303
    session = Session.objects.get()
    assert (session.kind, session.starts_at, session.location) == (
        "pool",
        at(2027, 6, 14, 9),
        "Piscina inventada",
    )
    assert list(session.instructors.all()) == [teacher]
    page = detail(client, course)
    assert "Sessió desada" in page and str(teacher) in page and "Piscina inventada" in page


def test_only_instructors_can_be_chosen_for_a_session(client, manager, make_admin):  # noqa: F811
    course = a_course(manager)
    make_admin("instructor")
    stranger = a_person("Sense rol")
    form = text(client.get(url("session_add", course.pk)))
    assert f'value="{stranger.pk}"' not in form
    assert f'value="{manager.person.pk}"' not in form
    response = client.post(
        url("session_add", course.pk), {"kind": "pool", "instructors": [stranger.pk], **WHEN}
    )
    assert response.status_code == 200
    assert not Session.objects.exists()


def test_a_wrong_session_is_shown_with_its_error(client, manager):
    course = a_course(manager)
    add = url("session_add", course.pk)
    response = client.post(
        add, {"kind": "pool", "starts_at": WHEN["starts_at"], "ends_at": "2027-06-14T08:00"}
    )
    assert "ha d&#x27;acabar després de començar" in text(response)
    response = client.post(add, {"kind": "barca", **WHEN})
    assert response.status_code == 200
    response = client.post(add, {"kind": "pool", "starts_at": "ahir", "ends_at": "demà"})
    assert "Escriu el dia i l&#x27;hora" in text(response)
    assert not Session.objects.exists()


def test_a_session_is_edited_and_cancelled_with_a_reason(client, manager, make_admin):  # noqa: F811
    course = a_course(manager)
    teacher, other = make_admin("instructor").person, make_admin("instructor").person
    session = sessions.add_session(
        course,
        by=manager,
        kind="pool",
        starts_at=at(2027, 6, 14, 9),
        ends_at=at(2027, 6, 14, 11),
        instructors=[teacher],
    )
    edit = url("session_edit", course.pk, session.pk)
    assert "checked" in text(client.get(edit))
    data = {
        "kind": "sea",
        "instructors": [other.pk],
        "starts_at": "2027-06-14T10:00",
        "ends_at": "2027-06-14T12:00",
    }
    assert client.post(edit, data).status_code == 303
    session.refresh_from_db()
    assert (session.kind, session.starts_at) == ("sea", at(2027, 6, 14, 10))
    assert list(session.instructors.all()) == [other]
    client.post(edit, data)
    assert "No hi havia cap canvi per desar" in detail(client, course)

    cancel = url("session_cancel", course.pk, session.pk)
    assert client.post(cancel, {"reason": ""}).status_code == 200
    assert client.post(cancel, {"reason": REASON}).status_code == 303
    session.refresh_from_db()
    assert (session.cancelled, session.cancellation_reason) == (True, REASON)
    page = detail(client, course)
    assert "Cancel·lada" in page and REASON in page
    assert Session.objects.count() == 1  # no s'esborra


def test_a_session_is_only_reached_through_its_own_activity(client, manager):
    """Per objecte: amb l'identificador d'una altra activitat, «no trobat», i res no canvia."""
    course, other = a_course(manager), a_course(manager, title="Un altre curs inventat")
    session = sessions.add_session(
        course, by=manager, kind="pool", starts_at=at(2027, 6, 14, 9), ends_at=at(2027, 6, 14, 11)
    )
    for name in ("session_edit", "session_cancel"):
        assert client.get(url(name, other.pk, session.pk)).status_code == 404
        assert client.post(url(name, other.pk, session.pk), {"reason": REASON}).status_code == 404
        assert client.get(url(name, course.pk, 999_999)).status_code == 404
    session.refresh_from_db()
    assert session.cancelled is False


# --- L-M02-05: les sessions sense instructor surten marcades --------------------------------------


def test_l_m02_05_sessions_left_without_instructor_are_marked_to_the_manager(
    client,
    manager,
    make_admin,  # noqa: F811
):
    """L-M02-05 (decisió 086), la part de la pantalla: quan l'instructor perd el rol, la sessió
    futura surt marcada «Sense instructor» a la fitxa de l'activitat."""
    admin = make_admin("administrator")
    teacher = make_admin("instructor")
    course = a_course(manager)
    sessions.add_session(
        course,
        by=manager,
        kind="sea",
        starts_at=at(2027, 6, 14, 9),
        ends_at=at(2027, 6, 14, 11),
        instructors=[teacher.person],
    )
    page = detail(client, course)
    assert "Sense instructor" not in page and str(teacher.person) in page
    roles.remove_role(teacher, "instructor", by=admin)
    page = detail(client, course)
    assert "Hi ha sessions sense instructor" in page
    assert "Sense instructor" in page
    assert str(teacher.person) not in page


# --- Programa del dia -----------------------------------------------------------------------------


def test_the_programme_is_saved_in_the_order_of_the_rows(client, manager):
    outing = an_outing(manager)
    programme = url("activity_programme", outing.pk)
    assert "Bloc 1" in text(client.get(programme))
    data = {
        "starts_at_0": "08:00",
        "label_0": "Trobada",
        "location_0": "Port inventat",
        # la fila 1 es deixa en blanc: no compta
        "starts_at_2": "08:30",
        "ends_at_2": "09:00",
        "label_2": "Briefing",
        "responsible_label_2": "Cap d'immersió",
    }
    assert client.post(programme, data).status_code == 303
    assert list(outing.programme_blocks.values_list("order", "label")) == [
        (1, "Trobada"),
        (2, "Briefing"),
    ]
    page = detail(client, outing)
    assert "Programa desat" in page and "Briefing" in page and "Cap d&#x27;immersió" in page
    # Buidar les files treu els blocs.
    assert client.post(programme, {}).status_code == 303
    assert not ProgrammeBlock.objects.exists()


def test_a_wrong_programme_saves_nothing(client, manager):
    outing = an_outing(manager)
    programme = url("activity_programme", outing.pk)
    cases = (
        ({"label_0": "Trobada"}, "Escriu l&#x27;hora de cada bloc"),
        ({"starts_at_0": "08:00"}, "ha de dir què s&#x27;hi fa"),
        ({"starts_at_0": "25:00", "label_0": "Trobada"}, "Escriu una hora vàlida"),
        (
            {"starts_at_0": "08:00", "label_0": "Trobada", "responsible_label_0": "a@example.org"},
            "sense correu ni telèfon",
        ),
    )
    for data, message in cases:
        response = client.post(programme, data)
        assert response.status_code == 200, data
        assert message in text(response), data
    assert not ProgrammeBlock.objects.exists()


# --- Què mostra la fitxa --------------------------------------------------------------------------


def test_the_detail_shows_no_personal_data_beyond_names(client, manager):
    """Minimització: de la persona responsable, només el nom. Cap correu, telèfon ni document."""
    person = manager.person
    person.contact_email = "responsable.inventada@example.org"
    person.save()
    outing = an_outing(manager, responsible=person, forecast_url="https://example.org/previsio")
    page = detail(client, outing)
    assert str(person) in page
    assert "responsable.inventada@example.org" not in page
    assert 'href="https://example.org/previsio"' in page  # només un enllaç (RN-M02-24)


# --- Requisits a la pantalla (T-M02-29 i T-M02-32) ------------------------------------------------


def test_requirements_are_set_on_the_form_and_shown_on_the_detail(client, manager):
    from apps.activities import catalogue
    from apps.activities.models import TrainingCatalogueEntry

    level = catalogue.create_level(by=manager, name="Nivell inventat B1", rank=10)
    first, second = (
        an_entry(manager, kind=TrainingCatalogueEntry.Kind.SPECIALITY, name=f"Especialitat {x}")
        for x in "AB"
    )
    course_entry = an_entry(manager, name="Curs que no és una especialitat")
    form = text(client.get(OUTING_ADD))
    assert "Especialitat A" in form and "Nivell inventat B1" in form
    assert (
        f'value="{course_entry.pk}"'
        not in form.split("Especialitats exigides")[1].split("</fieldset>")[0]
    )
    data = outing_data(
        manager,
        min_level=level.pk,
        required_specialities=[first.pk, second.pk],
        specialities_rule="any",
        min_age="16",
    )
    assert client.post(OUTING_ADD, data).status_code == 303
    outing = Activity.objects.get()
    assert (outing.min_level, outing.specialities_rule, outing.min_age) == (level, "any", 16)
    assert set(outing.required_specialities.all()) == {first, second}
    page = detail(client, outing)
    assert "Nivell inventat B1" in page and "Cal alguna d'aquestes especialitats" in page
    assert "16 anys" in page
    # Una fitxa de curs no es pot enviar com a especialitat.
    response = client.post(
        OUTING_ADD, outing_data(manager, title="Una altra", required_specialities=[course_entry.pk])
    )
    assert response.status_code == 200
    assert Activity.objects.count() == 1


def test_editing_keeps_and_changes_the_requirements(client, manager):
    from apps.activities import catalogue
    from apps.activities.models import TrainingCatalogueEntry

    level = catalogue.create_level(by=manager, name="Nivell inventat B1", rank=10)
    speciality = an_entry(
        manager, kind=TrainingCatalogueEntry.Kind.SPECIALITY, name="Especialitat A"
    )
    outing = an_outing(manager, min_level=level, required_specialities=[speciality], min_age=16)
    edit = url("activity_edit", outing.pk)
    form = text(client.get(edit))
    assert "checked" in form and "selected" in form
    data = outing_data(
        manager,
        title=outing.title,
        payment_window_hours="72",
        requirements_mode="block",
        specialities_rule="all",
        department=outing.department.pk,
        responsible=outing.responsible.pk,
        min_level=level.pk,
        min_age="",
    )
    assert client.post(edit, data).status_code == 303
    outing.refresh_from_db()
    assert (outing.requirements_mode, outing.min_age, outing.min_level) == ("block", None, level)
    assert not outing.required_specialities.exists()  # s'han desmarcat
