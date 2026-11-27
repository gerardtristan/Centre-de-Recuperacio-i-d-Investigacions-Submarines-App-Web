"""Tasques de la cua del 07 (decisió 012). La lògica és als mòduls; aquí només hi ha la crida."""

from procrastinate.contrib.django import app

from . import contact, newsletter, schedule


# Cada dia, de matinada: els missatges de contacte acabats fora de termini (RN-M07-07, CA-M07-12).
@app.periodic(cron="35 3 * * *")
@app.task(name="website.purge_contact_messages", queue="maintenance")
def purge_contact_messages(timestamp: int) -> None:
    contact.purge_finished()


# Un lot del butlletí (T-M07-14): els correus van a la cua de la 00 amb la prioritat del butlletí.
@app.task(name="website.send_newsletter_batch", queue="maintenance")
def send_newsletter_batch(delivery_ids: list[int]) -> None:
    newsletter.send_batch(delivery_ids)


# Cada minut: les publicacions i retirades programades que han vençut (RN-M07-17, CA-M07-26).
@app.periodic(cron="* * * * *")
@app.task(name="website.run_scheduled_actions", queue="maintenance")
def run_scheduled_actions(timestamp: int) -> None:
    schedule.run_due()
