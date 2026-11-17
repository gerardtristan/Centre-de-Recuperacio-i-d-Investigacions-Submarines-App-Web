"""Tasques de la cua de la base comuna (decisió 012). Procrastinate les descobreix pel nom del
mòdul. La lògica és als serveis; aquí només hi ha la crida."""

from django.conf import settings
from procrastinate import RetryStrategy
from procrastinate.contrib.django import app

from . import events, files, locked_data, mail


# Reintents espaiats: 4, 16, 64, 256… segons. Qui decideix quan s'atura és `mail.deliver`, amb
# el seu comptador; aquest límit només és una xarxa de seguretat.
@app.task(
    name="core.send_email",
    queue="email",
    retry=RetryStrategy(max_attempts=settings.EMAIL_MAX_ATTEMPTS, exponential_wait=4),
)
def send_email(email_id: int) -> None:
    mail.deliver(email_id)


# Cada hora: els correus ajornats pel límit diari tornen a la cua quan hi ha lloc, que és
# l'endemà (CA-A4, CA-A5). Cada hora i no a una hora fixa perquè el dia del comptador és el de
# l'hora local i el rellotge de la cua no en sap res; mentre el límit és ple no fa res.
@app.periodic(cron="5 * * * *")
@app.task(name="core.release_deferred_emails", queue="maintenance")
def release_deferred_emails(timestamp: int) -> None:
    mail.release_deferred()


# Cada dia, de matinada: destrueix les dades bloquejades amb el termini de conservació vençut
# (CA-19.5, RN-90; decisió 085, G-1). Els registres econòmics no es toquen.
@app.periodic(cron="45 3 * * *")
@app.task(name="core.destroy_expired_locked_data", queue="maintenance")
def destroy_expired_locked_data(timestamp: int) -> None:
    locked_data.destroy_expired()


# Cada dia, de matinada: esborra les exportacions RGPD caducades (V-08).
@app.periodic(cron="15 3 * * *")
@app.task(name="core.purge_expired_files", queue="maintenance")
def purge_expired_files(timestamp: int) -> None:
    files.purge_expired()


# 049 (T-M05b-21): lliura un esdeveniment als subscriptors, com a mínim una vegada. Reintents
# espaiats (4, 16, 64… segons); els subscriptors que ja l'han rebut no es tornen a executar.
@app.task(
    name="core.deliver_event",
    queue="events",
    retry=RetryStrategy(max_attempts=events.MAX_ATTEMPTS, exponential_wait=4),
)
def deliver_event(event_id: int) -> None:
    events.deliver(event_id)
