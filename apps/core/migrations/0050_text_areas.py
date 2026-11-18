"""T-M00-08d (097; especificació a planning.md#M00-textos-editables; P-380): els textos dels
correus passen a una àrea per apartat. Cada àrea és un apartat d'ajustos amb «Cons.» (veure) i
«Sí» (veure i editar). Ara tots els correus editables són de l'àrea de socis: l'apartat
`texts` passa a ser `texts-members` (claus, mòdul i cel·les) i l'administrador hi passa de
«Cons.» a «Sí» (matriu inicial de la 097), amb una versió nova de la matriu (060).

Les versions dels textos no es toquen (van per la clau primària de l'ajust). Les entrades
antigues del registre d'activitat conserven la clau d'abans."""

from django.db import migrations
from django.db.models import Max

OLD, NEW = "texts", "texts-members"
OLD_CODE, NEW_CODE = f"settings.section.{OLD}", f"settings.section.{NEW}"
NOTE = "Textos dels correus per àrees: àrea de socis; l'administrador hi edita (T-M00-08d)."


def _move(apps, old, new, old_code, new_code, admin_scope):
    Setting = apps.get_model("core", "Setting")
    RolePermission = apps.get_model("core", "RolePermission")
    for setting in Setting.objects.filter(module=old):
        setting.key = new + setting.key.removeprefix(old)
        setting.module = new
        setting.save(update_fields=["key", "module"])
    diff = []
    for cell in RolePermission.objects.filter(permission_code=old_code).select_related("role"):
        scope = admin_scope if cell.role.code == "administrator" else cell.scope
        RolePermission.objects.create(role=cell.role, permission_code=new_code, scope=scope)
        diff.append({"role": cell.role.code, "permission": old_code, "before": cell.scope,
                     "after": None})  # fmt: skip
        diff.append({"role": cell.role.code, "permission": new_code, "before": None,
                     "after": scope})  # fmt: skip
        cell.delete()
    return diff


def load(apps, schema_editor):
    diff = _move(apps, OLD, NEW, OLD_CODE, NEW_CODE, "all")
    if diff:
        Version = apps.get_model("core", "PermissionMatrixVersion")
        last = Version.objects.aggregate(n=Max("number"))["n"] or 0
        Version.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    _move(apps, NEW, OLD, NEW_CODE, OLD_CODE, "read")
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0049_legal_text_note_and_more_texts")]

    operations = [migrations.RunPython(load, unload)]
