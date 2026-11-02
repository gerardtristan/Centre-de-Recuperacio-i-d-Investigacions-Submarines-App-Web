"""Tasques de la cua de la base comuna (decisió 012). Procrastinate les descobreix pel nom del
mòdul. La lògica és als serveis; aquí només hi ha la crida."""

from django.conf import settings
from procrastinate import RetryStrategy
from procrastinate.contrib.django import app

from . import mail


# Reintents espaiats: 4, 16, 64, 256… segons. Qui decideix quan s'atura és `mail.deliver`, amb
# el seu comptador; aquest límit només és una xarxa de seguretat.
@app.task(
    name="core.send_email",
    queue="email",
    retry=RetryStrategy(max_attempts=settings.EMAIL_MAX_ATTEMPTS, exponential_wait=4),
)
def send_email(email_id: int) -> None:
    mail.deliver(email_id)
