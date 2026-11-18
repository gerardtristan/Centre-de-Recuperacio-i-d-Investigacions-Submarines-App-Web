"""Tasques de la cua del M01 (decisió 012). La lògica és als serveis; aquí només hi ha la crida."""

import logging

from procrastinate.contrib.django import app

from . import fees, member_requests

logger = logging.getLogger(__name__)


# Cada dia al matí: l'avís previ de la renovació (abans de generar la quota; T-M01-43a), les
# quotes que vencen aviat i els recordatoris que toquen (T-M01-18; 070 i Q-061 de la 072). Tot
# idempotent.
@app.periodic(cron="0 6 * * *")
@app.task(name="members.daily_fees", queue="maintenance")
def daily_fees(timestamp: int) -> None:
    steps = (
        fees.send_renewal_notices,
        fees.generate_due_fees,
        fees.send_due_reminders,
    )
    failed = None
    for step in steps:  # un pas que falla no atura els altres
        try:
            step()
        except Exception as exc:
            logger.exception("Pas %s de members.daily_fees", step.__name__)
            failed = failed or exc
    if failed is not None:
        raise failed  # la feina queda fallida i es veu al seguiment


# Cada dia, abans de les quotes: aplica les baixes programades que vencen (RN-M01-74; 074).
# Idempotent: tornar-la a executar no aplica cap baixa dues vegades.
@app.periodic(cron="45 5 * * *")
@app.task(name="members.daily_leaves", queue="maintenance")
def daily_leaves(timestamp: int) -> None:
    member_requests.apply_due_leaves()
