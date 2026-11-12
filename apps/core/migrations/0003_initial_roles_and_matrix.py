"""Configuració inicial de rols i permisos de la 00 i del 01 (059; T-RP-04).

Còpia fixa de la configuració inicial del catàleg en aquesta data. Una prova comprova que
coincideix amb `permission_catalog.editable_initial_cells()`. Els canvis posteriors de la
matriu es fan amb una migració nova revisada (060), mai editant aquesta.
"""

from django.db import migrations

ROLES = [
    ("instructor", "Instructor", True),
    ("secretary", "Secretaria", True),
    ("courses_manager", "Responsable de cursos i sortides", True),
    ("equipment_manager", "Responsable de material", True),
    ("treasurer", "Tresorer", True),
    ("history_department", "Departament d'Història", True),
    ("administrator", "Administrador", True),
    ("president", "President", True),
    ("board", "Junta", True),
    ("communications_manager", "Responsable de comunicació", True),
    ("shop_manager", "Responsable de botiga", True),
    ("member", "Soci", False),
    ("visitor", "Visitant", False),
    ("guest", "Participant no soci", False),
]

# (rol, permís, abast): només les cel·les editables; les protegides són al codi.
CELLS = [
    ("administrator", "core.audit.view", "all"),
    ("administrator", "core.cluber_import.run", "all"),
    ("administrator", "core.departments.manage", "all"),
    ("administrator", "core.gdpr.handle", "all"),
    ("administrator", "core.guest_links.manage", "all"),
    ("administrator", "core.legal_texts.publish", "all"),
    ("administrator", "core.people.manage", "all"),
    ("administrator", "members.audit.view", "all"),
    ("administrator", "members.cluber_import.run", "all"),
    ("administrator", "members.create_in_person", "all"),
    ("administrator", "members.edit", "all"),
    ("administrator", "members.edit_join_date", "all"),
    ("administrator", "members.export", "all"),
    ("administrator", "members.fees.generate", "all"),
    ("administrator", "members.fees.view", "all"),
    ("administrator", "members.field.identity", "all"),
    ("administrator", "members.gdpr.handle", "all"),
    ("administrator", "members.licence_record.manage", "all"),
    ("administrator", "members.list", "all"),
    ("administrator", "members.requests.approve_join", "all"),
    ("administrator", "members.requests.resolve_change", "all"),
    ("administrator", "members.requests.view", "all"),
    ("courses_manager", "members.licence_record.manage", "read"),
    ("president", "members.requests.approve_join", "all"),
    ("president", "members.requests.resolve_change", "all"),
    ("president", "members.requests.view", "all"),
    ("secretary", "core.people.manage", "all"),
    ("secretary", "members.create_in_person", "all"),
    ("secretary", "members.edit", "all"),
    ("secretary", "members.edit_join_date", "all"),
    ("secretary", "members.export", "all"),
    ("secretary", "members.fees.view", "all"),
    ("secretary", "members.field.identity", "all"),
    ("secretary", "members.licence_record.manage", "all"),
    ("secretary", "members.list", "all"),
    ("secretary", "members.requests.approve_join", "all"),
    ("secretary", "members.requests.resolve_change", "all"),
    ("secretary", "members.requests.view", "all"),
    ("treasurer", "core.bank_statement.import", "all"),
    ("treasurer", "members.fees.generate", "all"),
    ("treasurer", "members.fees.view", "all"),
    ("treasurer", "members.licence_record.manage", "read"),
    ("treasurer", "members.list", "read_minimal"),
    ("treasurer", "members.requests.approve_join", "all"),
    ("treasurer", "members.requests.resolve_change", "all"),
    ("treasurer", "members.requests.view", "all"),
    ("treasurer", "members.unpaid.mark", "all"),
]


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    roles = {
        code: Role.objects.create(code=code, name=name, is_management=management)
        for code, name, management in ROLES
    }
    RolePermission.objects.bulk_create(
        RolePermission(role=roles[role], permission_code=code, scope=scope)
        for role, code, scope in CELLS
    )
    PermissionMatrixVersion.objects.create(
        number=1,
        note="Configuració inicial de la 00 i del 01 (decisió 059).",
        diff=[
            {"role": role, "permission": code, "before": None, "after": scope}
            for role, code, scope in CELLS
        ],
    )


def unload(apps, schema_editor):
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(number=1).delete()
    apps.get_model("core", "RolePermission").objects.all().delete()
    apps.get_model("core", "Role").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_roles_and_permissions"),
    ]

    operations = [migrations.RunPython(load, unload)]
