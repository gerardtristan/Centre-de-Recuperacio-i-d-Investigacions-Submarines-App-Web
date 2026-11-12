"""Tasques de la cua del M02 (decisió 012). La lògica és als serveis; aquí només hi ha la crida."""

from procrastinate.contrib.django import app

from . import states


# Cada 10 minuts: tanca les inscripcions que han arribat a la data límit i posa «en curs» els
# cursos que han començat (RN-M02-02). Idempotent: només actua sobre el que toca.
@app.periodic(cron="*/10 * * * *")
@app.task(name="activities.advance_by_clock", queue="maintenance")
def advance_by_clock(timestamp: int) -> None:
    states.advance_by_clock()
