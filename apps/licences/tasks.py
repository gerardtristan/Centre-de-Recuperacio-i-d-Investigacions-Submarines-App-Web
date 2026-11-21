"""Tasques de la cua del 06 (decisió 012). La lògica és als mòduls; aquí només hi ha la crida."""

from procrastinate.contrib.django import app

from . import day, events


# Cada dia, de matinada: les llicències d'un dia que no han arribat a vigents (RN-M06-20).
@app.periodic(cron="20 3 * * *")
@app.task(name="licences.lapse_overdue", queue="maintenance")
def lapse_overdue(timestamp: int) -> None:
    day.lapse_overdue()


# Cada dia, de matinada: `licence.expired` l'endemà del venciment (RN-M06-17).
@app.periodic(cron="25 3 * * *")
@app.task(name="licences.expire_due", queue="maintenance")
def expire_due(timestamp: int) -> None:
    events.expire_due()
