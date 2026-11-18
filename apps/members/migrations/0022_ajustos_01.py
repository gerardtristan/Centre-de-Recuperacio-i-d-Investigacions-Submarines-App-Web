"""T-M01-32: els valors del 01 com a ajustos (addenda de la 055 i ampliació de la 091). VC-01: el
preu de cada tipus, amb data d'entrada en vigor, que comença amb el preu del tipus (3500 i 9000
cèntims). VC-02 (llista, d'1 a 10 valors de -90 a 90), VC-03, VC-04 i VC-53. Els permisos són a
`core/0046`."""

from django.db import migrations

CARD_BACK = "Carnet personal i intransferible. Si el trobes, escriu a cris@cris.es."
SETTINGS = [
    # clau, tipus, valor inicial, mínim, màxim, longitud màxima (a la llista, nombre de valors)
    ("members.fee_reminder_offsets", "integer_list", [-15, -1, 0, 15, 30], -90, 90, 10),
    ("members.type_change_supplement_due_days", "integer", 7, 1, 30, None),
    ("members.card_back_text", "text", CARD_BACK, None, None, 300),
    ("members.classic_member_years", "integer", 0, 0, 60, None),
]


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key, kind, initial, low, high, length in SETTINGS:
        Setting.objects.get_or_create(
            key=key,
            defaults={"module": "members", "value_type": kind, "initial_value": initial,
                      "min_value": low, "max_value": high, "max_length": length},
        )  # fmt: skip
    for membership_type in apps.get_model("members", "MembershipType").objects.all():
        Setting.objects.get_or_create(
            key=f"members.annual_fee_cents.{membership_type.code}",
            defaults={"module": "members", "value_type": "cents",
                      "initial_value": membership_type.annual_fee_cents, "min_value": 1,
                      "affects_money": True, "effective_dated": True},
        )  # fmt: skip


def unload(apps, schema_editor):
    """Els ajustos es queden, com els de pagaments: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0046_settings_members_permissions"),
        ("members", "0021_member_request_renewal_fee"),
    ]

    operations = [migrations.RunPython(load, unload)]
