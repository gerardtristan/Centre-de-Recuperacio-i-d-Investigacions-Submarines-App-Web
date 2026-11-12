"""Permisos del 02, Activitats (T-M02-33): les cel·les editables de la matriu inicial de la 059
(«02 Activitats», AC5 a AC20), amb una versió nova de la matriu (060: mai editant la 0003).

Còpia fixa de la configuració inicial del catàleg en aquesta data; una prova comprova que la base
de dades coincideix amb `permission_catalog.editable_initial_cells()`. C3 és protegit i no té fila.
"""

from django.db import migrations
from django.db.models import Max

MANAGERS = ("administrator", "courses_manager", "president", "treasurer")
WITHOUT_TREASURER = ("administrator", "courses_manager", "president")


def _all(code, roles=MANAGERS):
    return [(role, code, "all") for role in roles]


# (rol, permís, abast)
CELLS = [
    *_all("activities.enrol_in_person"),  # AC5
    *_all("activities.catalogue.manage"),  # AC6
    *_all("activities.manage"),  # AC7
    *_all("activities.participants.view"),  # AC8
    ("instructor", "activities.participants.view", "own_sessions"),
    ("equipment_manager", "activities.participants.view", "read"),
    *_all("activities.attendance.record", WITHOUT_TREASURER),  # AC9
    ("instructor", "activities.attendance.record", "own_sessions"),
    ("instructor", "activities.assessment.record", "own_sessions"),  # AC10a
    ("instructor", "activities.reinforcement.propose", "own_sessions"),  # AC10b
    *_all("activities.reinforcement.decide", WITHOUT_TREASURER),  # AC11
    ("instructor", "activities.outcome.record", "own_sessions"),  # AC12
    *_all("activities.certificate.issue", WITHOUT_TREASURER),  # AC13
    *_all("activities.environment.manage", WITHOUT_TREASURER),  # AC14
    ("board", "activities.environment.manage", "read"),
    *_all("activities.message.send"),  # AC15
    *_all("activities.waitlist.manage"),  # AC16
    *_all("activities.refund.propose"),  # AC17
    ("treasurer", "activities.refund.execute", "all"),  # AC18
    ("treasurer", "activities.income.view", "all"),  # AC19
    ("administrator", "activities.income.view", "all"),
    ("courses_manager", "activities.income.view", "read"),
    *_all("activities.reports.view"),  # AC20
    ("instructor", "activities.reports.view", "own_sessions"),
    ("equipment_manager", "activities.reports.view", "read"),
    ("board", "activities.reports.view", "read"),
]
NOTE = "Permisos del mòdul 02, Activitats: AC5 a AC20 (configuració inicial de la decisió 059)."


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    roles = {role.code: role for role in Role.objects.all()}
    diff = []
    for role, code, scope in CELLS:
        _cell, created = RolePermission.objects.get_or_create(
            role=roles[role], permission_code=code, defaults={"scope": scope}
        )
        if created:
            diff.append({"role": role, "permission": code, "before": None, "after": scope})
    if diff:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    apps.get_model("core", "RolePermission").objects.filter(
        permission_code__startswith="activities."
    ).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0028_p22_exempt_fee"),
    ]

    operations = [migrations.RunPython(load, unload)]
