"""Tasques de la cua del 06 (decisió 012). La lògica és als mòduls; aquí només hi ha la crida."""

from procrastinate.contrib.django import app

from . import day, events, reminders


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


# Cada dia, al matí: el resum de cada tram a qui tramita i els avisos als titulars en lots
# (RN-M06-12; CA-M06-08, 09, 24 i 26).
@app.periodic(cron="0 8 * * *")
@app.task(name="licences.send_reminders", queue="maintenance")
def send_reminders(timestamp: int) -> None:
    for days_before, licence_ids in reminders.plan():
        send_reminder_batch.defer(days_before=days_before, licence_ids=licence_ids)


@app.task(name="licences.send_reminder_batch", queue="maintenance")
def send_reminder_batch(days_before: int, licence_ids: list[int]) -> None:
    reminders.send_batch(days_before, licence_ids)
