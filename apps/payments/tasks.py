"""Tasques de la cua dels pagaments (decisió 012). La lògica és a `processing`; aquí només hi ha
la crida."""

from procrastinate.contrib.django import app

from apps.accounts.models import Account

from . import campaigns, checkout, expiry, processing, settlements, transfer_reminders
from .models import MandateCampaign


# P-M05b-D, pas 3: l'endpoint desa la notificació, respon i la posa a la cua.
@app.task(name="payments.process_notification", queue="payments")
def process_notification(event_id: int) -> None:
    processing.process_notification(event_id)


# Cada dia, de matinada: la xarxa de seguretat (M05b-3; L-M05b-01).
@app.periodic(cron="30 4 * * *")
@app.task(name="payments.safety_net", queue="maintenance")
def safety_net(timestamp: int) -> None:
    processing.safety_net()


# Cada dia, de matinada: caduca els mandats sense cobraments en 36 mesos (T-M05a-15; RN-M05a-08).
@app.periodic(cron="40 4 * * *")
@app.task(name="payments.expire_mandates", queue="maintenance")
def expire_mandates(timestamp: int) -> None:
    expiry.expire_mandates()


# Cada dia, de matinada: les liquidacions del proveïdor cap a la 04 (T-M05b-14; P-226).
@app.periodic(cron="50 4 * * *")
@app.task(name="payments.import_settlements", queue="maintenance")
def import_settlements(timestamp: int) -> None:
    settlements.import_settlements()


# Cada dia, de matinada: les quotes vençudes dels socis que paguen amb la targeta guardada
# (T-M05b-15; P-302). Després de la xarxa de seguretat.
@app.periodic(cron="0 5 * * *")
@app.task(name="payments.charge_saved_cards", queue="maintenance")
def charge_saved_cards(timestamp: int) -> None:
    checkout.charge_due_saved_cards()


# Cada dia al matí: les transferències que no han arribat (T-M05b-22c; RN-M05b-09).
@app.periodic(cron="15 9 * * *")
@app.task(name="payments.transfer_reminders", queue="maintenance")
def transfer_reminders_task(timestamp: int) -> None:
    transfer_reminders.send_due()


# P-M05a-E, pas 3: el tresorer confirma l'enviament i les invitacions surten per la cua.
@app.task(name="payments.send_campaign_invitations", queue="payments")
def send_campaign_invitations(campaign_id: int, account_id: int) -> None:
    campaign = MandateCampaign.objects.get(pk=campaign_id)
    campaigns.send_invitations(campaign, by=Account.objects.get(pk=account_id))


# Cada dia al matí: recordatoris de la campanya de mandats (RN-M05a-14).
@app.periodic(cron="30 9 * * *")
@app.task(name="payments.campaign_reminders", queue="maintenance")
def campaign_reminders(timestamp: int) -> None:
    campaigns.send_due_reminders()
