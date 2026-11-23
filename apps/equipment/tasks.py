"""Tasques de la cua del 03 (decisió 012). La lògica és als mòduls; aquí només hi ha la crida."""

from procrastinate.contrib.django import app

from . import reviews


# Cada dia, al matí: avís al responsable de material de les revisions que vencen (CA-M03-11).
@app.periodic(cron="0 7 * * *")
@app.task(name="equipment.review_notices", queue="maintenance")
def review_notices(timestamp: int) -> None:
    reviews.send_due_notices()
