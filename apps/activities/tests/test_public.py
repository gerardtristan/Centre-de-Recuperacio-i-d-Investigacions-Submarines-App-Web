"""Dades públiques i calendari descarregable (T-M02-08, la part de serveis; AC1; CA-M02-05;
RN-M02-24, 25 i 45; CA-M02-48). Les pàgines públiques i la ruta del calendari van amb les vistes
del 02. Només dades inventades.
"""

import datetime

import pytest
from django.utils import timezone

from apps.activities import catalogue, ics, public, sessions
from apps.activities.models import Activity
from apps.core.models import Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_course, a_place, an_outing
from .helpers import moment as at

pytestmark = pytest.mark.django_db

S = Activity.Status
TODAY = datetime.date(2027, 6, 1)
NOW = timezone.make_aware(datetime.datetime(2027, 5, 1, 12))
REASON = "Motiu inventat de proves"
T = datetime.time


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def publish(activity, status=S.OPEN):
    Activity.objects.filter(pk=activity.pk).update(status=status)
    activity.refresh_from_db()
    return activity


def lines_of(text):
    return text.replace("\r\n ", "").split("\r\n")


# --- Què és públic (CA-M02-05) --------------------------------------------------------------------


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
def test_ca_m02_05_only_published_and_unfinished_activities_are_public(manager, status, is_public):
    outing = an_outing(manager)
    Activity.objects.filter(pk=outing.pk).update(status=status, cancellation_reason=REASON)
    assert [a.pk for a in public.public_list(today=TODAY)] == ([outing.pk] if is_public else [])
    if is_public:
        assert public.get_activity(outing.pk, today=TODAY).title == outing.title
    else:
        with pytest.raises(public.NotFound):
            public.get_activity(outing.pk, today=TODAY)


def test_a_missing_activity_answers_like_a_hidden_one():
    with pytest.raises(public.NotFound):
        public.get_activity(999_999, today=TODAY)


def test_the_list_is_ordered_filters_by_kind_and_drops_past_activities(manager):
    late = publish(
        an_outing(manager, starts_on=datetime.date(2027, 6, 20), ends_on=datetime.date(2027, 6, 20))
    )
    course = publish(a_course(manager))
    outing = publish(an_outing(manager))
    assert [a.pk for a in public.public_list(today=TODAY)] == [course.pk, outing.pk, late.pk]
    assert [a.pk for a in public.public_list(kind="course", today=TODAY)] == [course.pk]
    assert [a.pk for a in public.public_list(today=datetime.date(2027, 6, 16))] == [late.pk]


# --- Mínim de dades i lloc (RN-M02-45, CA-M02-48) -------------------------------------------------


def test_ca_m02_48_the_place_shows_its_name_and_nothing_else(manager, make_admin):  # noqa: F811
    place = a_place(manager)
    catalogue.update_place(place, by=manager, name=place.name, notes="Nota interna inventada.")
    teacher = make_admin(Role.Code.INSTRUCTOR).person
    Person.objects.filter(pk=teacher.pk).update(first_name="Instructora", last_name="Inventada")
    outing = an_outing(manager, place=place, meeting_point="Moll inventat")
    Activity.objects.filter(pk=outing.pk).update(material_cost_cents=1234)
    sessions.add_session(
        outing,
        by=manager,
        kind="sea",
        starts_at=at(2027, 6, 14, 9),
        ends_at=at(2027, 6, 14, 11),
        place=place,
        instructors=[teacher],
    )
    sessions.set_programme(
        outing, [{"starts_at": T(8, 0), "label": "Trobada", "responsible_label": "Cap"}], by=manager
    )
    data = public.get_activity(publish(outing).pk, today=TODAY)
    assert (data.place, data.meeting_point) == (place.name, "Moll inventat")
    assert data.sessions[0].place == place.name
    assert data.blocks[0].place == place.name  # el bloc sense lloc mostra el de l'activitat
    text = repr(data) + ics.build(outing, outing.sessions.all(), now=NOW)
    for forbidden in ("Nota interna", "12,34", "1234", "Instructora", "Inventada", "Responsable"):
        assert forbidden not in text
    assert "standard" not in repr(data) and "material" not in repr(data)


def test_cancelled_sessions_are_not_public(manager):
    course = a_course(manager)
    pool = a_place(manager, prices=None)
    kept = sessions.add_session(
        course,
        by=manager,
        kind="pool",
        starts_at=at(2027, 6, 14, 9),
        ends_at=at(2027, 6, 14, 11),
        place=pool,
    )
    gone = sessions.add_session(
        course,
        by=manager,
        kind="sea",
        starts_at=at(2027, 6, 15, 9),
        ends_at=at(2027, 6, 15, 11),
        place=pool,
    )
    sessions.cancel_session(gone, by=manager, reason=REASON)
    data = public.get_activity(publish(course).pk, today=TODAY)
    assert [s.starts_at for s in data.sessions] == [kept.starts_at]


def test_rn_m02_24_the_forecast_is_only_a_link_and_only_for_outings(manager):
    url = "https://example.org/previsio-maritima"
    outing = publish(an_outing(manager, forecast_url=url))
    course = publish(a_course(manager, forecast_url=url))
    assert public.get_activity(outing.pk, today=TODAY).forecast_url == url
    assert public.get_activity(course.pk, today=TODAY).forecast_url == ""


def test_rn_m02_24_an_outing_without_its_own_link_uses_the_setting(manager):
    outing = publish(an_outing(manager, forecast_url=""))
    assert public.get_activity(outing.pk, today=TODAY).forecast_url == "https://www.meteo.cat/"
    course = publish(a_course(manager, forecast_url=""))
    assert public.get_activity(course.pk, today=TODAY).forecast_url == ""  # un curs, mai


# --- Calendari (RN-M02-25) ------------------------------------------------------------------------


def test_rn_m02_25_the_calendar_has_the_sessions_and_no_person(manager, make_admin):  # noqa: F811
    teacher = make_admin(Role.Code.INSTRUCTOR).person
    course = a_course(manager, title="Curs inventat; amb, signes")
    port = a_place(manager, prices=None)
    first = sessions.add_session(
        course,
        by=manager,
        kind="sea",
        starts_at=at(2027, 6, 14, 9),
        ends_at=at(2027, 6, 14, 11),
        place=port,
        instructors=[teacher],
    )
    cancelled = sessions.add_session(
        course,
        by=manager,
        kind="pool",
        starts_at=at(2027, 6, 15, 9),
        ends_at=at(2027, 6, 15, 11),
        place=port,
    )
    sessions.cancel_session(cancelled, by=manager, reason=REASON)
    text = ics.build(course, course.sessions.all(), now=NOW)
    lines = lines_of(text)
    assert lines[:3] == ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:{ics.PRODID}"]
    assert text.endswith("END:VCALENDAR\r\n")
    assert text.count("BEGIN:VEVENT") == text.count("END:VEVENT") == 1
    assert f"UID:activitat-{course.pk}-sessio-{first.pk}@cris1954.cat" in lines
    assert "DTSTART:20270614T070000Z" in lines and "DTEND:20270614T090000Z" in lines
    assert "SUMMARY:Curs inventat\\; amb\\, signes (Mar)" in lines
    assert f"LOCATION:{ics.escape(port.name)}" in lines
    for forbidden in ("ATTENDEE", "ORGANIZER", "@example"):
        assert forbidden not in text


def test_an_activity_without_sessions_is_a_whole_day_event(manager):
    outing = an_outing(manager)  # del 14 al 15 de juny, sense punt de trobada
    lines = lines_of(ics.build(outing, now=NOW))
    assert "DTSTART;VALUE=DATE:20270614" in lines
    assert "DTEND;VALUE=DATE:20270616" in lines  # el final és exclusiu
    assert f"LOCATION:{ics.escape(outing.place.name)}" in lines


def test_long_lines_are_folded_at_75_octets(manager):
    title = "Sortida inventada amb un títol molt llarg, ple d'accents i de ç trencades, més de 75"
    text = ics.build(an_outing(manager, title=title), now=NOW)
    assert all(len(line.encode("utf-8")) <= 75 for line in text.split("\r\n"))
    assert f"SUMMARY:{ics.escape(title)}" in lines_of(text)


def test_escaping_of_calendar_text():
    assert ics.escape("a\\b;c,d\ne") == "a\\\\b\\;c\\,d\\ne"
    assert ics.fold("curt") == "curt"
