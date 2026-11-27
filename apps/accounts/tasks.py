"""Tasques de la cua dels comptes (decisió 012). La lògica és als serveis; aquí només hi ha la
crida."""

from procrastinate import RetryStrategy
from procrastinate.contrib.django import app

from . import email_links, limits, signup


# T-M01-39b: «He oblidat la contrasenya». 3 reintents en menys d'un minut (als 7, 9 i 13 s);
# passat el retard màxim, la tasca caduca la petició i no envia res.
@app.task(
    name="accounts.send_password_reset",
    queue="email",
    retry=RetryStrategy(max_attempts=3, wait=5, exponential_wait=2),
)
def send_password_reset(request_id: int) -> None:
    email_links.process_password_reset(request_id)


# T-M01-56 (revisió G): l'enllaç per entrar sense contrasenya, com la recuperació.
@app.task(
    name="accounts.send_email_login",
    queue="email",
    retry=RetryStrategy(max_attempts=3, wait=5, exponential_wait=2),
)
def send_email_login(request_id: int) -> None:
    email_links.process_email_login(request_id)


# Cada 5 minuts (T-M01-39b; abans, cada dia): les peticions de més de 24 hores ja no compten per
# a cap límit (RN-M01-58) i no es guarden més; les de recuperació perden la IP als 30 minuts i,
# si encara són pendents passat el retard màxim, caduquen.
@app.periodic(cron="*/5 * * * *")
@app.task(name="accounts.purge_email_link_requests", queue="maintenance")
def purge_email_link_requests(timestamp: int) -> None:
    limits.purge_old()


# T-M01-53 (revisió A): cada dia, els comptes pendents de «Crea el compte» que no s'han confirmat
# en el termini de la verificació s'anonimitzen i l'adreça queda lliure.
@app.periodic(cron="20 3 * * *")
@app.task(name="accounts.purge_expired_signups", queue="maintenance")
def purge_expired_signups(timestamp: int) -> None:
    signup.purge_expired()
