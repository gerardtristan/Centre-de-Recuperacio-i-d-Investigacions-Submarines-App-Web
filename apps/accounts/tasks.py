"""Tasques de la cua dels comptes (decisió 012). La lògica és als serveis; aquí només hi ha la
crida."""

from procrastinate.contrib.django import app

from . import limits


# Cada dia, de matinada: les peticions d'enllaços de més de 24 hores ja no compten per a cap
# límit (RN-M01-58) i no es guarden més.
@app.periodic(cron="25 3 * * *")
@app.task(name="accounts.purge_email_link_requests", queue="maintenance")
def purge_email_link_requests(timestamp: int) -> None:
    limits.purge_old()
