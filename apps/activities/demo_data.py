"""Dades inventades del mòdul 02 per a captures, demostracions i revisió (T-M02-25). Mai en
producció: les criden l'ordre `seed_activities_demo_data` i `seed_demo_data`, que es neguen fora
de desenvolupament. Portat de la branca aparcada i adaptat a `master` (llocs, agències).

Tot passa pels serveis, amb els comptes de prova del responsable i de l'instructor, perquè el
registre d'activitat quedi com quedaria de debò. Cap nom, preu ni nivell és real: tots porten
«de prova».

Què crea:

- una agència, dos nivells de titulació, dos cursos i una especialitat al catàleg (un curs amb
  un canvi de preu que encara ha d'entrar en vigor) i un projecte de medi ambient;
- dos llocs (una piscina i una cala amb preu de sortida);
- un curs en esborrany amb dues sessions i l'instructor de prova;
- una sortida oberta amb programa del dia i requisits;
- una sortida de medi ambient ja feta i una de cancel·lada, amb el motiu.

Les dates són relatives al dia que s'executa, perquè sempre hi hagi activitats per venir.

Amb quatre persones de prova (`participants`) hi afegeix inscrits a la sortida oberta (una
confirmada i una pendent de pagament) i un curs en marxa amb dos alumnes confirmats, la llista
passada, una avaluació de cada mena i el resultat: un apte amb el certificat emès. Els pagaments
són del mode de proves: es marquen amb el servei de la 00 i el 02 els confirma en rebre
l'esdeveniment `charge.paid`, com en producció.
"""

import datetime
from dataclasses import dataclass

from django.utils import timezone

from apps.core import audit, business_settings, charges, events
from apps.core.models import Event, Payment

from . import assessment, attendance, catalogue, certificates, services, sessions, states
from . import enrolment as enrolments
from .models import Activity, EnvironmentalSubtype, OutingType, Session, TrainingCatalogueEntry

K = TrainingCatalogueEntry.Kind
T = datetime.time
SYSTEM = audit.system("activities.demo_data")


@dataclass(frozen=True)
class Result:
    entries: int
    levels: int
    activities: int
    draft_course: Activity
    open_outing: Activity
    done_outing: Activity
    cancelled_outing: Activity
    running_course: Activity | None = None
    enrolments: int = 0


def _at(day: datetime.date, hour: int) -> datetime.datetime:
    return timezone.make_aware(datetime.datetime.combine(day, T(hour, 0)))


def _paid(row):
    """Pagament confirmat en mode de proves, i el lliurament de `charge.paid` que fa la cua."""
    charges.record_payment(
        row.charge,
        method=Payment.Method.CARD,
        origin="provider",
        by=SYSTEM,
        provider_status="prova",
        provider_reference=f"PROVA-{row.charge_id}",
    )
    for event in Event.objects.filter(name=events.CHARGE_PAID, payload__charge=row.charge_id):
        events.deliver(event.pk)
    row.refresh_from_db()
    return row


def _teachers(instructor, day) -> list:
    """RN-M02-26: amb el mode «bloqueig» (VC-46), l'instructor de prova només fa classe si és soci
    actiu amb llicència tècnica; si no, les sessions es creen sense instructor."""
    blocked = business_settings.get(sessions.INSTRUCTOR_MODE_KEY) == "block"
    return (
        []
        if blocked and sessions.instructor_problems(instructor.person, day)
        else [instructor.person]
    )


def _desk(activity, person, *, manager, now):
    return enrolments.enrol(activity, person, channel="desk", actor=manager, now=now)


def _with_people(*, manager, instructor, beginners, pool, open_outing, participants, days):
    """Inscrits, assistència, avaluacions i resultat (només amb quatre persones de prova)."""
    first, second, third, fourth = participants[:4]
    today = days(0)
    _paid(_desk(open_outing, first, manager=manager, now=_at(today, 9)))
    _desk(open_outing, second, manager=manager, now=_at(today, 9))

    running = services.create_course(
        by=manager,
        catalogue_entry=beginners,
        today=days(-40),
        title="Curs de prova d'iniciació (en marxa)",
        description="Activitat inventada, amb alumnes, assistència i avaluacions.",
        starts_on=days(-2),
        ends_on=days(5),
        registration_closes_at=_at(days(-5), 20),
        place=pool,
        responsible=manager.person,
    )
    practice = sessions.add_session(
        running,
        by=manager,
        kind=Session.Kind.POOL,
        starts_at=_at(days(-2), 18),
        ends_at=_at(days(-2), 20),
        place=pool,
        is_practice=True,
        instructors=_teachers(instructor, days(-2)),
    )
    states.publish(running, by=manager, now=_at(days(-30), 10))
    students = [
        _paid(_desk(running, person, manager=manager, now=_at(days(-20), 10)))
        for person in (third, fourth)
    ]
    states.advance_by_clock(now=_at(today, 8))
    practice.refresh_from_db()
    for row in students:
        attendance.mark(row, practice, present=True, by=manager, today=today)
    if practice.instructors.exists():  # avalua i posa el resultat qui hi fa classe
        for row, result, notes in (
            (students[0], "achieved", "Observació de prova."),
            (students[1], "needs_reinforcement", "Observació de prova: li cal més pràctica."),
        ):
            assessment.assess(practice, row, result=result, notes=notes, by=instructor, today=today)
        certificates.record_outcome(students[0], result="pass", by=instructor)
        certificates.issue(students[0], by=manager, today=today)
    running.refresh_from_db()
    return running


def create(*, manager, instructor, department, today=None, participants=()) -> Result:
    """Crea les dades de prova del 02. `manager` té AC5 a AC7, AC13 i AC22 (el responsable de
    cursos i sortides o l'administrador); `instructor`, el rol d'instructor; `department` és un
    departament actiu."""
    today = today or timezone.localdate()

    def days(n: int) -> datetime.date:
        return today + datetime.timedelta(days=n)

    agency = catalogue.create_agency(by=manager, name="Agència de prova")
    level_1 = catalogue.create_level(by=manager, name="Nivell de prova 1", rank=10, agency=agency)
    level_2 = catalogue.create_level(by=manager, name="Nivell de prova 2", rank=20, agency=agency)
    beginners = catalogue.create_entry(
        by=manager,
        kind=K.COURSE,
        name="Curs de prova d'iniciació",
        level=level_1.name,
        description="Curs inventat per a les captures. No és cap curs real del club.",
        default_places=8,
        price_member_cents=12000,
        price_non_member_cents=15000,
        reinforcement_price_cents=3000,
        open_to_non_members=True,
        department=department,
        min_age=14,
        today=today,
    )
    advanced = catalogue.create_entry(
        by=manager,
        kind=K.COURSE,
        name="Curs de prova avançat",
        level=level_2.name,
        default_places=6,
        price_member_cents=18000,
        price_non_member_cents=22000,
        department=department,
        default_requirements_mode="block",
        today=today,
    )
    catalogue.change_prices(
        advanced,
        by=manager,
        price_member_cents=19500,
        price_non_member_cents=22000,
        valid_from=days(30),
        note="Dada de prova: canvi de preu que encara ha d'entrar en vigor.",
        today=today,
    )
    night = catalogue.create_entry(
        by=manager,
        kind=K.SPECIALITY,
        name="Especialitat de prova: immersió nocturna",
        default_places=6,
        price_member_cents=6000,
        price_non_member_cents=8000,
        department=department,
        today=today,
    )
    project = catalogue.create_project(
        by=manager,
        name="Projecte de prova: fons nets",
        objective="Projecte inventat per a les captures: retirar residus d'una cala de prova.",
        department=department,
    )
    pool = catalogue.create_place(by=manager, name="Piscina de prova")
    cove = catalogue.create_place(by=manager, name="Cala de prova", notes="Lloc inventat.")
    catalogue.change_place_price(
        cove,
        by=manager,
        price_member_cents=4500,
        price_non_member_cents=6000,
        valid_from=days(-60),
        note="Dada de prova: preu de sortida del lloc.",
        today=days(-60),
    )
    responsible = manager.person
    dive = OutingType.objects.get(name="Immersió")

    draft_course = services.create_course(
        by=manager,
        catalogue_entry=beginners,
        today=today,
        title="Curs de prova d'iniciació (grup de prova)",
        description="Activitat inventada, en esborrany.",
        starts_on=days(60),
        ends_on=days(62),
        registration_closes_at=_at(days(55), 20),
        place=pool,
        responsible=responsible,
    )
    for offset, kind, practice in ((60, Session.Kind.THEORY, False), (61, Session.Kind.POOL, True)):
        sessions.add_session(
            draft_course,
            by=manager,
            kind=kind,
            starts_at=_at(days(offset), 18),
            ends_at=_at(days(offset), 20),
            place=pool,
            is_practice=practice,
            instructors=_teachers(instructor, days(offset)),
        )

    open_outing = services.create_outing(
        by=manager,
        outing_type=dive,
        today=today,
        title="Sortida de prova a una cala inventada",
        description="Sortida inventada, oberta a inscripcions.",
        starts_on=days(30),
        ends_on=days(30),
        registration_closes_at=_at(days(27), 20),
        place=cove,
        meeting_point="Moll de prova",
        max_places=12,
        open_to_non_members=True,
        licence_required=True,
        requirements_mode="warn",  # les persones de prova no compleixen els requisits
        min_level=level_1,
        required_specialities=[night],
        responsible=responsible,
    )
    sessions.set_programme(
        open_outing,
        [
            {"starts_at": T(8, 0), "label": "Trobada", "place": cove},
            {"starts_at": T(8, 30), "ends_at": T(9, 0), "label": "Briefing"},
            {"starts_at": T(9, 30), "label": "Immersió", "responsible_label": "Cap d'immersió"},
            {"starts_at": T(13, 0), "label": "Tornada"},
        ],
        by=manager,
    )
    states.publish(open_outing, by=manager)

    done_outing = services.create_outing(
        by=manager,
        outing_type=OutingType.objects.get(name="Medi ambient"),
        subtype=EnvironmentalSubtype.objects.get(name="Neteja"),
        project=project,
        today=days(-45),
        title="Neteja de prova d'una cala inventada",
        description="Sortida de medi ambient inventada, ja feta.",
        starts_on=days(-20),
        ends_on=days(-20),
        registration_closes_at=_at(days(-23), 20),
        place=cove,
        max_places=20,
        price_member_cents=0,
        price_non_member_cents=0,
        price_override_note="Dada de prova: les neteges són gratuïtes.",
        min_level=level_2,
        responsible=responsible,
    )
    states.publish(done_outing, by=manager, now=_at(days(-40), 10))
    states.mark_done(done_outing, by=manager, now=_at(days(-20), 18))

    cancelled_outing = services.create_outing(
        by=manager,
        outing_type=dive,
        today=today,
        title="Sortida de prova cancel·lada",
        starts_on=days(10),
        ends_on=days(10),
        registration_closes_at=_at(days(7), 20),
        place=cove,
        max_places=10,
        responsible=responsible,
    )
    states.publish(cancelled_outing, by=manager)
    states.cancel(
        cancelled_outing, by=manager, reason="Dada de prova: cancel·lada per mostrar l'estat."
    )
    running_course = None
    if len(participants) >= 4:
        running_course = _with_people(
            manager=manager,
            instructor=instructor,
            beginners=beginners,
            pool=pool,
            open_outing=open_outing,
            participants=participants,
            days=days,
        )
    return Result(
        entries=3,
        levels=2,
        activities=5 if running_course else 4,
        running_course=running_course,
        enrolments=4 if running_course else 0,
        draft_course=draft_course,
        open_outing=open_outing,
        done_outing=done_outing,
        cancelled_outing=cancelled_outing,
    )
