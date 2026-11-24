"""T-M08-02 (P-488, RN-M08-03): un text d'ajuda editable per a cada indicador del catàleg,
buit d'inici, a l'apartat «dashboard» dels ajustos. Els permisos de l'apartat
(`settings.section.dashboard`) i de la família (`settings.edit.dashboard.help_text`) són del
catàleg del nucli: fins llavors, l'apartat no surt a cap pantalla (`_section_or_404`).
La llista és una còpia fixa dels codis del catàleg d'aquest moment (una migració no importa el
codi de l'app); un indicador nou porta la seva clau en una migració nova."""

from django.db import migrations

CODES = [
    "active_members", "new_members", "unpaid_members", "free_places", "licences_to_renew",
    "equipment_to_review", "grants_closing", "activity_margin", "department_income",
    "department_expenses", "grants_granted", "expenses_without_invoice",
    "expenses_without_invoice_amount", "treasury_balances", "occupancy", "attendance",
    "weekly_enrolments", "equipment_in_use", "joins_and_leaves", "active_by_type", "retention",
    "signed_mandates", "confirmed_subscribers", "pending_contact_messages",
    "conference_attendees",
]  # fmt: skip


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for code in CODES:
        Setting.objects.get_or_create(
            key=f"dashboard.help_text.{code}",
            defaults={
                "module": "dashboard",
                "value_type": "text",
                "initial_value": "",
                "max_length": 300,
            },  # fmt: skip
        )


def unload(apps, schema_editor):
    """Els ajustos es queden: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("core", "0076_activities_reminder_days_permission")]

    operations = [migrations.RunPython(load, unload)]
