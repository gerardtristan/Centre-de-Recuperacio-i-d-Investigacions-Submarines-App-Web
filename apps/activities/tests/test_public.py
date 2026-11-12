"""Llistat i detall públics i fitxer de calendari (T-M02-08; AC1; CA-M02-05; RN-M02-24 i
RN-M02-25; M02-12, «mínim de dades»).

Només dades inventades.
"""

import dataclasses
import datetime

import pytest
from django.test import Client
from django.urls import reverse

from apps.activities import ics, public, sessions, states
from apps.activities.models import Activity, Session
from apps.core.models import Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import BEFORE_DEADLINE, REASON, a_course, a_person, an_outing, at, client_for

pytestmark = pytest.mark.django_db

S = Activity.Status
T = datetime.time
TODAY = datetime.date(2027, 6, 1)
LIST = reverse("activities:list")


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


@pytest.fixture
def visitor():
    return Client()  # sense cap sessió


def detail_url(activity):
    return reverse("activities:detail", args=[activity.pk])


def published(manager, make=an_outing, **fields):
    activity = make(manager, **fields)
    states.publish(activity, by=manager, now=BEFORE_DEADLINE)
    return activity


def force(activity, status):
    Activity.objects.filter(pk=activity.pk).update(
        status=status, cancellation_reason=REASON if status == S.CANCELLED else ""
    )


# --- CA-M02-05 i què és públic --------------------------------------------------------------------


def test_ca_m02_05_a_visitor_does_not_find_a_draft(manager, visitor):
    """CA-M02-05: donat una activitat `draft`, quan un visitant en demana el detall, rep «no
    trobat». Tampoc surt al llistat."""
    draft = an_outing(manager, title="Esborrany inventat que no s'ha de veure")
    assert visitor.get(detail_url(draft)).status_code == 404
    assert draft.title not in visitor.get(LIST).content.decode()
    with pytest.raises(public.NotFound):
        public.get_activity(draft.pk, today=TODAY)
    # Un cop publicada, sí.
    states.publish(draft, by=manager, now=BEFORE_DEADLINE)
    assert visitor.get(detail_url(draft)).status_code == 200


@pytest.mark.parametrize(
    ("status", "is_public"),
    [
        (S.DRAFT, False),
        (S.OPEN, True),
        (S.REGISTRATION_CLOSED, True),
        (S.IN_PROGRESS, True),
        (S.DONE, False),
        (S.CLOSED, False),
        (S.CANCELLED, False),
    ],
)
def test_only_published_and_unfinished_activities_are_public(manager, visitor, status, is_public):
    activity = a_course(manager, title="Curs inventat de la prova pública")
    force(activity, status)
    listed = [a.pk for a in public.public_list(today=TODAY)]
    assert (activity.pk in listed) == is_public
    assert visitor.get(detail_url(activity)).status_code == (200 if is_public else 404)
    assert (activity.title in visitor.get(LIST).content.decode()) == is_public


def test_an_activity_that_does_not_exist_answers_like_one_that_is_hidden(manager, visitor):
    hidden = an_outing(manager)
    missing, private = (
        visitor.get(reverse("activities:detail", args=[999_999])),
        visitor.get(detail_url(hidden)),
    )
    assert missing.status_code == private.status_code == 404
    # La mateixa pàgina de «no trobat»: no es pot saber quina de les dues existeix.
    assert [t.name for t in missing.templates] == [t.name for t in private.templates]
    assert hidden.title not in private.content.decode()


def test_an_activity_whose_days_have_passed_leaves_the_list(manager):
    activity = published(manager)  # del 14 al 15 de juny de 2027
    assert public.public_list(today=datetime.date(2027, 6, 15))
    assert not public.public_list(today=datetime.date(2027, 6, 16))
    with pytest.raises(public.NotFound):
        public.get_activity(activity.pk, today=datetime.date(2027, 6, 16))


def test_the_list_is_ordered_by_date_and_filters_by_kind(manager, visitor):
    later = published(
        manager, title="Sortida inventada de més tard", starts_on=datetime.date(2027, 6, 15)
    )
    sooner = published(manager, make=a_course, title="Curs inventat de més aviat")
    assert [a.pk for a in public.public_list(today=TODAY)] == [sooner.pk, later.pk]
    assert [a.pk for a in public.public_list(kind="outing", today=TODAY)] == [later.pk]
    page = visitor.get(LIST, {"classe": "course"}).content.decode()
    assert sooner.title in page and later.title not in page
    assert visitor.get(LIST, {"classe": "inventada"}).status_code == 200


def test_l_m02_09_no_published_activity(visitor):
    assert "Ara no hi ha cap activitat oberta." in visitor.get(LIST).content.decode()


def test_the_public_pages_only_answer_to_get(manager, visitor):
    activity = published(manager)
    assert visitor.post(LIST).status_code == 405
    assert visitor.post(detail_url(activity)).status_code == 405


def test_the_public_pages_are_the_same_with_any_session(manager, make_admin):  # noqa: F811
    activity = published(manager)
    for account in (manager, make_admin("secretary")):
        assert client_for(account).get(detail_url(activity)).status_code == 200


# --- Mínim de dades -------------------------------------------------------------------------------


def test_the_public_data_carries_no_person(manager, make_admin, visitor):  # noqa: F811
    """Ni inscrits, ni instructors, ni la persona responsable: cap nom surt a les pàgines
    públiques ni a les dades que es donen als altres mòduls."""
    teacher = make_admin("instructor").person
    Person.objects.filter(pk=teacher.pk).update(first_name="Instructora", last_name="Inventada")
    responsible = a_person("Responsable")
    Person.objects.filter(pk=responsible.pk).update(last_name="Inventada Secreta")
    responsible.refresh_from_db()
    activity = published(manager, make=a_course, responsible=manager.person)
    Activity.objects.filter(pk=activity.pk).update(responsible=responsible)
    sessions.add_session(
        activity,
        by=manager,
        kind=Session.Kind.SEA,
        starts_at=at(2027, 6, 14, 9),
        ends_at=at(2027, 6, 14, 11),
        location="Port inventat",
        instructors=[teacher],
    )
    data = public.get_activity(activity.pk, today=TODAY)
    values = dataclasses.asdict(data)
    assert not any(isinstance(value, Person) for value in values.values())
    assert "responsible" not in values and "instructors" not in str(values)
    assert data.sessions[0].location == "Port inventat"
    for url in (LIST, detail_url(activity)):
        page = visitor.get(url).content.decode()
        assert "Inventada Secreta" not in page
        assert "Instructora" not in page
    assert "Port inventat" in visitor.get(detail_url(activity)).content.decode()


def test_cancelled_sessions_and_the_programme(manager, visitor):
    activity = published(manager)
    kept = sessions.add_session(
        activity, by=manager, kind="sea", starts_at=at(2027, 6, 14, 9), ends_at=at(2027, 6, 14, 11)
    )
    gone = sessions.add_session(
        activity, by=manager, kind="pool", starts_at=at(2027, 6, 15, 9), ends_at=at(2027, 6, 15, 11)
    )
    sessions.cancel_session(gone, by=manager, reason=REASON)
    sessions.set_programme(
        activity,
        [{"starts_at": T(8, 0), "label": "Trobada al port", "responsible_label": "Cap d'immersió"}],
        by=manager,
    )
    data = public.get_activity(activity.pk, today=TODAY)
    assert [s.starts_at for s in data.sessions] == [kept.starts_at]
    assert [(b.label, b.responsible_label) for b in data.blocks] == [
        ("Trobada al port", "Cap d'immersió")
    ]
    page = visitor.get(detail_url(activity)).content.decode()
    assert "Trobada al port" in page and "Piscina" not in page
    assert REASON not in page


def test_prices_and_who_can_enrol(manager, visitor):
    only_members = published(manager, title="Sortida inventada només per a socis")
    everyone = published(manager, title="Sortida inventada oberta", open_to_non_members=True)
    closed = visitor.get(detail_url(only_members)).content.decode()
    assert "Només socis del club" in closed and "Preu per als no socis" not in closed
    opened = visitor.get(detail_url(everyone)).content.decode()
    assert "Preu per als no socis" in opened
    data = public.get_activity(everyone.pk, today=TODAY)
    assert (data.price_member, data.max_places, data.registration_open) == (
        "45,00\xa0€",
        12,
        True,
    ) or data.price_member.startswith("45,00")
    states.close_registration(only_members, by=manager, now=BEFORE_DEADLINE)
    assert "Inscripcions tancades" in visitor.get(detail_url(only_members)).content.decode()


# --- RN-M02-24: la previsió marítima és només un enllaç -------------------------------------------


def test_rn_m02_24_the_forecast_is_only_a_link_and_only_for_outings(manager, visitor):
    url = "https://example.org/previsio-maritima"
    outing = published(manager, forecast_url=url)
    course = published(manager, make=a_course, forecast_url=url)
    page = visitor.get(detail_url(outing)).content.decode()
    assert f'href="{url}"' in page
    assert "<iframe" not in page and "example.org" not in page.replace(f'href="{url}"', "")
    assert public.get_activity(course.pk, today=TODAY).forecast_url == ""
    assert url not in visitor.get(detail_url(course)).content.decode()
    plain = published(manager, title="Sortida inventada sense previsió")
    assert "Previsió marítima" not in visitor.get(detail_url(plain)).content.decode()


# --- RN-M02-25: el fitxer de calendari ------------------------------------------------------------

NOW = at(2027, 5, 1, 12)


def lines_of(text):
    return text.split("\r\n")


def test_rn_m02_25_the_calendar_has_the_sessions_and_no_person(manager, make_admin):  # noqa: F811
    teacher = make_admin("instructor").person
    Person.objects.filter(pk=teacher.pk).update(first_name="Instructora", last_name="Inventada")
    course = a_course(manager, title="Curs inventat; amb, signes")
    first = sessions.add_session(
        course,
        by=manager,
        kind="sea",
        starts_at=at(2027, 6, 14, 9),
        ends_at=at(2027, 6, 14, 11),
        location="Port inventat",
        instructors=[teacher],
    )
    cancelled = sessions.add_session(
        course, by=manager, kind="pool", starts_at=at(2027, 6, 15, 9), ends_at=at(2027, 6, 15, 11)
    )
    sessions.cancel_session(cancelled, by=manager, reason=REASON)
    text = ics.build(course, course.sessions.all(), now=NOW)
    lines = lines_of(text)
    assert lines[:3] == ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:{ics.PRODID}"]
    assert text.endswith("END:VCALENDAR\r\n")
    assert text.count("BEGIN:VEVENT") == text.count("END:VEVENT") == 1  # la cancel·lada no hi és
    assert f"UID:activitat-{course.pk}-sessio-{first.pk}@cris1954.cat" in lines
    # Hora d'estiu de la península: les 9:00 són les 7:00 UTC.
    assert "DTSTART:20270614T070000Z" in lines and "DTEND:20270614T090000Z" in lines
    assert "DTSTAMP:20270501T100000Z" in lines
    assert "SUMMARY:Curs inventat\\; amb\\, signes (Mar)" in lines
    assert "LOCATION:Port inventat" in lines
    for forbidden in ("ATTENDEE", "ORGANIZER", "Inventada", "Instructora", "@example"):
        assert forbidden not in text


def test_an_activity_without_sessions_is_a_whole_day_event(manager):
    outing = an_outing(manager, meeting_point="Moll inventat")  # del 14 al 15 de juny
    lines = lines_of(ics.build(outing, now=NOW))
    assert "DTSTART;VALUE=DATE:20270614" in lines
    assert "DTEND;VALUE=DATE:20270616" in lines  # el final és exclusiu
    assert f"UID:activitat-{outing.pk}@cris1954.cat" in lines
    assert "LOCATION:Moll inventat" in lines


def test_long_lines_are_folded_at_75_octets(manager):
    title = "Sortida inventada amb un títol molt llarg, ple d'accents i de ç trencades, més de 75"
    outing = an_outing(manager, title=title)
    text = ics.build(outing, now=NOW)
    assert all(len(line.encode("utf-8")) <= 75 for line in lines_of(text))
    unfolded = text.replace("\r\n ", "")
    assert f"SUMMARY:{ics.escape(title)}" in unfolded.split("\r\n")


def test_escaping_of_calendar_text():
    assert ics.escape("a\\b;c,d\ne") == "a\\\\b\\;c\\,d\\ne"
    assert ics.fold("curt") == "curt"
