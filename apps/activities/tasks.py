"""Tasques de la cua del 02 (decisió 012). La lògica és als serveis; aquí només hi ha la crida."""

from procrastinate.contrib.django import app

from . import cancellation, deadlines, states


# Cada 10 minuts: tanca les inscripcions que han arribat a la data límit i posa «en curs» els
# cursos que han començat (RN-M02-02). Idempotent: només actua sobre el que toca.
@app.periodic(cron="*/10 * * * *")
@app.task(name="activities.advance_by_clock", queue="maintenance")
def advance_by_clock(timestamp: int) -> None:
    states.advance_by_clock()


# Cada 10 minuts: fa caducar les inscripcions sense pagar i les ofertes sense acceptar, i ofereix
# les places lliures (RN-M02-08 i 09). Idempotent.
@app.periodic(cron="*/10 * * * *")
@app.task(name="activities.run_deadlines", queue="maintenance")
def run_deadlines(timestamp: int) -> None:
    deadlines.run_deadlines()


# Cada 10 minuts: anul·la el càrrec de les inscripcions cancel·lades amb un pagament en curs quan
# l'intent acaba (RN-M02-37). Idempotent.
@app.periodic(cron="*/10 * * * *")
@app.task(name="activities.retry_pending_voids", queue="maintenance")
def retry_pending_voids(timestamp: int) -> None:
    cancellation.retry_pending_voids()
