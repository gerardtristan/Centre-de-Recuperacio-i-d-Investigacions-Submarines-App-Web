"""Tasques de la cua del M01 (decisió 012). La lògica és als serveis; aquí només hi ha la crida."""

from procrastinate.contrib.django import app

from . import fees


# Cada dia al matí: primer es generen les quotes que vencen aviat i després s'envien els
# recordatoris que toquen (T-M01-18; 070 i Q-061 de la 072).
@app.periodic(cron="0 6 * * *")
@app.task(name="members.daily_fees", queue="maintenance")
def daily_fees(timestamp: int) -> None:
    fees.generate_due_fees()
    fees.send_due_reminders()
