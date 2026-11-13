"""Tasques de la cua dels pagaments (decisió 012). La lògica és a `processing`; aquí només hi ha
la crida."""

from procrastinate.contrib.django import app

from . import processing


# P-M05b-D, pas 3: l'endpoint desa la notificació, respon i la posa a la cua.
@app.task(name="payments.process_notification", queue="payments")
def process_notification(event_id: int) -> None:
    processing.process_notification(event_id)


# Cada dia, de matinada: la xarxa de seguretat (M05b-3; L-M05b-01).
@app.periodic(cron="30 4 * * *")
@app.task(name="payments.safety_net", queue="maintenance")
def safety_net(timestamp: int) -> None:
    processing.safety_net()
