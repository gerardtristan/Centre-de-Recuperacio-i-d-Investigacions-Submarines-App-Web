"""Tasques de la cua del 07 (decisió 012). La lògica és als mòduls; aquí només hi ha la crida."""

from procrastinate.contrib.django import app

from . import contact


# Cada dia, de matinada: els missatges de contacte acabats fora de termini (RN-M07-07, CA-M07-12).
@app.periodic(cron="35 3 * * *")
@app.task(name="website.purge_contact_messages", queue="maintenance")
def purge_contact_messages(timestamp: int) -> None:
    contact.purge_finished()
