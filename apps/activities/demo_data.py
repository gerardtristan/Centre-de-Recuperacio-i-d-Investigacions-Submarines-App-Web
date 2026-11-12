"""Dades inventades del mòdul 02 per a captures, demostracions i revisió (T-M02-25). Mai en
producció: les crida l'ordre `seed_demo_data`, que es nega fora de desenvolupament.

Tot passa pels serveis, amb els comptes de prova del responsable de cursos i sortides i de
l'instructor, perquè el registre d'activitat quedi com quedaria de debò. Cap nom, preu ni nivell
és real: tots porten «de prova».

Què crea:

- dos nivells de titulació, dos cursos i una especialitat al catàleg (un curs amb un canvi de
  preu que encara ha d'entrar en vigor) i un projecte de medi ambient;
- un curs en esborrany amb dues sessions i l'instructor de prova;
- una sortida oberta amb programa del dia i requisits;
- una sortida de medi ambient ja feta, amb els resultats registrats;
- una sortida cancel·lada, amb el motiu.

Les dates són relatives al dia que s'executa, perquè sempre hi hagi activitats per venir.

**Fora d'aquesta peça**, perquè encara no existeixen: inscrits, pagaments, assistència i
avaluacions (T-M02-11 i següents).
"""

import datetime
from dataclasses import dataclass

from django.utils import timezone

from . import catalogue, environment, services, sessions, states
from .models import Activity, EnvironmentalSubtype, OutingType, Session, TrainingCatalogueEntry

K = TrainingCatalogueEntry.Kind
T = datetime.time


@dataclass(frozen=True)
class Result:
    entries: int
    levels: int
    activities: int
    draft_course: Activity
    open_outing: Activity
    done_outing: Activity
    cancelled_outing: Activity


def _at(day: datetime.date, hour: int) -> datetime.datetime:
    return timezone.make_aware(datetime.datetime.combine(day, T(hour, 0)))


def create(*, manager, instructor, department, today=None) -> Result:
    """Crea les dades de prova del 02. `manager` té AC6, AC7 i AC14; `instructor`, el rol
    d'instructor; `department` és un departament actiu."""
    today = today or timezone.localdate()

    def days(n: int) -> datetime.date:
        return today + datetime.timedelta(days=n)

    level_1 = catalogue.create_level(by=manager, name="Nivell de prova 1", rank=10)
    level_2 = catalogue.create_level(by=manager, name="Nivell de prova 2", rank=20)
    beginners = catalogue.create_entry(
        by=manager,
        kind=K.COURSE,
        name="Curs de prova d'iniciació",
        level="Nivell de prova 1",
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
        level="Nivell de prova 2",
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
    responsible = manager.person
    environment_type = OutingType.objects.get(name="Medi ambient")
    cleaning = EnvironmentalSubtype.objects.get(name="Neteja")

    draft_course = services.create_course(
        by=manager,
        catalogue_entry=beginners,
        today=today,
        title="Curs de prova d'iniciació (grup de prova)",
        description="Activitat inventada, en esborrany.",
        starts_on=days(60),
        ends_on=days(62),
        registration_closes_at=_at(days(55), 20),
        location="Piscina de prova",
        responsible=responsible,
    )
    for offset, kind, practice in ((60, Session.Kind.THEORY, False), (61, Session.Kind.POOL, True)):
        sessions.add_session(
            draft_course,
            by=manager,
            kind=kind,
            starts_at=_at(days(offset), 18),
            ends_at=_at(days(offset), 20),
            location="Piscina de prova",
            is_practice=practice,
            instructors=[instructor.person],
        )

    open_outing = services.create_outing(
        by=manager,
        outing_type=OutingType.objects.get(name="Immersió"),
        today=today,
        title="Sortida de prova a una cala inventada",
        description="Sortida inventada, oberta a inscripcions.",
        starts_on=days(30),
        ends_on=days(30),
        registration_closes_at=_at(days(27), 20),
        location="Cala de prova",
        meeting_point="Moll de prova",
        max_places=12,
        price_member_cents=4500,
        price_non_member_cents=6000,
        open_to_non_members=True,
        licence_required=True,
        min_level=level_1,
        required_specialities=[night],
        responsible=responsible,
    )
    sessions.set_programme(
        open_outing,
        [
            {"starts_at": T(8, 0), "label": "Trobada", "location": "Moll de prova"},
            {"starts_at": T(8, 30), "ends_at": T(9, 0), "label": "Briefing"},
            {"starts_at": T(9, 30), "label": "Immersió", "responsible_label": "Cap d'immersió"},
            {"starts_at": T(13, 0), "label": "Tornada"},
        ],
        by=manager,
    )
    states.publish(open_outing, by=manager)

    done_outing = services.create_outing(
        by=manager,
        outing_type=environment_type,
        subtype=cleaning,
        project=project,
        today=today,
        title="Neteja de prova d'una cala inventada",
        description="Sortida de medi ambient inventada, ja feta.",
        starts_on=days(-20),
        ends_on=days(-20),
        registration_closes_at=_at(days(-23), 20),
        location="Cala de prova",
        max_places=20,
        price_member_cents=0,
        price_non_member_cents=0,
        min_level=level_2,
        responsible=responsible,
    )
    states.publish(done_outing, by=manager, now=_at(days(-40), 10))
    states.mark_done(done_outing, by=manager, now=_at(days(-20), 18))
    environment.record_results(
        done_outing,
        by=manager,
        waste_grams=12500,
        species="Espècie de prova 1\nEspècie de prova 2",
        observations="Observació inventada per a les captures.",
        now=_at(days(-19), 10),
    )

    cancelled_outing = services.create_outing(
        by=manager,
        outing_type=OutingType.objects.get(name="Immersió"),
        today=today,
        title="Sortida de prova cancel·lada",
        starts_on=days(10),
        ends_on=days(10),
        registration_closes_at=_at(days(7), 20),
        location="Cala de prova",
        max_places=10,
        price_member_cents=4500,
        price_non_member_cents=6000,
        responsible=responsible,
    )
    states.publish(cancelled_outing, by=manager)
    states.cancel(
        cancelled_outing, by=manager, reason="Dada de prova: cancel·lada per mostrar l'estat."
    )
    return Result(
        entries=3,
        levels=2,
        activities=4,
        draft_course=draft_course,
        open_outing=open_outing,
        done_outing=done_outing,
        cancelled_outing=cancelled_outing,
    )
