"""Tasques de la cua dels ajuts (decisió 012). La lògica és als mòduls; aquí només la crida."""

from procrastinate.contrib.django import app

from . import reminders


# Cada dia al matí: els avisos de tancament, resposta i justificació (RN-M09A-04 i 05).
@app.periodic(cron="0 8 * * *")
@app.task(name="grants.send_reminders", queue="maintenance")
def send_reminders(timestamp: int) -> None:
    reminders.send_due()
