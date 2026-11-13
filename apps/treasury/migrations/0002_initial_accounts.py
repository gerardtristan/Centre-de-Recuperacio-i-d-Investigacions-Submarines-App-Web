"""Comptes inicials (CA-T01.1; VT-01): «Caixa» i «Banc principal». Reversible: en desfer-la
s'esborren només si continuen sent els inicials."""

from django.db import migrations

INITIAL = [("Caixa", "cash"), ("Banc principal", "bank")]


def create_initial_accounts(apps, schema_editor):
    account = apps.get_model("treasury", "TreasuryAccount")
    for name, kind in INITIAL:
        account.objects.get_or_create(name=name, defaults={"kind": kind})


def delete_initial_accounts(apps, schema_editor):
    account = apps.get_model("treasury", "TreasuryAccount")
    for name, kind in INITIAL:
        account.objects.filter(name=name, kind=kind, last4__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("treasury", "0001_treasury_accounts")]

    operations = [migrations.RunPython(create_initial_accounts, delete_initial_accounts)]
