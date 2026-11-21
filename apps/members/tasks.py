"""Tasques de la cua del M01 (decisió 012). La lògica és als serveis; aquí només hi ha la crida."""

import logging

from procrastinate.contrib.django import app

from . import fees, licence_copy, member_requests

logger = logging.getLogger(__name__)


# Cada dia al matí: el pas a simpatitzant que renova avui (073), l'avís previ de la renovació
# (abans de generar la quota; T-M01-43), les quotes que vencen aviat i els recordatoris que toquen
# (T-M01-18; 070 i Q-061 de la 072). Tot idempotent.
@app.periodic(cron="0 6 * * *")
@app.task(name="members.daily_fees", queue="maintenance")
def daily_fees(timestamp: int) -> None:
    steps = (
        member_requests.apply_due_downgrades,
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


# Cada dia, després de les tasques del 06 (03:20 i 03:25): la còpia de la llicència contra el 06
# (T-M01-31b; RN-M01-41). A quina hora: 054 [A validar: informàtica].
@app.periodic(cron="45 3 * * *")
@app.task(name="members.licence_check", queue="maintenance")
def licence_check(timestamp: int) -> None:
    licence_copy.daily_check()
