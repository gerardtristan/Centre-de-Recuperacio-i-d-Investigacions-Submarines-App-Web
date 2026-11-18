"""T-M00-08d (097; especificació a planning.md#M00-textos-editables; P-380): els textos dels
correus passen a una àrea per apartat. Cada àrea és un apartat d'ajustos amb «Cons.» (veure) i
«Sí» (veure i editar). Ara tots els correus editables són de l'àrea de socis: l'apartat
`texts` passa a ser `texts-members` (claus, mòdul i cel·les) i l'administrador hi té «Sí»
(matriu inicial de la 097), amb una versió nova de la matriu (060).

Les versions dels textos no es toquen (van per la clau primària de l'ajust). Les entrades
antigues del registre d'activitat conserven la clau d'abans. Enrere, es torna al nom antic,
l'administrador torna a «Cons.» i també queda una versió nova de la matriu: la història de la
matriu mai no perd files (RN-RP-08)."""

from django.db import migrations
from django.db.models import Max, Value
from django.db.models.functions import Concat, Substr

OLD, NEW = "texts", "texts-members"
OLD_CODE, NEW_CODE = f"settings.section.{OLD}", f"settings.section.{NEW}"
NOTE = "Textos dels correus per àrees: àrea de socis; l'administrador hi edita (T-M00-08d)."
NOTE_BACK = "Desfeta la T-M00-08d: els textos tornen a un sol apartat; l'administrador, «Cons.»."


def _move(apps, old, new, old_code, new_code, admin_scope, note):
    Setting = apps.get_model("core", "Setting")
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    # Només les claus amb el prefix de l'apartat; qualsevol altra es deixa com és.
    Setting.objects.filter(module=old, key__startswith=f"{old}.").update(
        key=Concat(Value(new), Substr("key", len(old) + 1)), module=new
    )
    changes = {}  # (rol, permís) -> [abast inicial, abast final]: una sola entrada per cel·la

    def record(role, permission, before, after):
        changes.setdefault((role, permission), [before, after])[1] = after

    for cell in RolePermission.objects.filter(permission_code=old_code).select_related("role"):
        # Es reanomena la cel·la; si la nova ja hi era, hi passa l'abast de la vigent i l'antiga
        # s'esborra (la restricció `rolepermission_unique` no es trenca mai).
        target = RolePermission.objects.filter(role=cell.role, permission_code=new_code).first()
        record(cell.role.code, old_code, cell.scope, None)
        record(cell.role.code, new_code, target.scope if target else None, cell.scope)
        if target is None:
            cell.permission_code = new_code
            cell.save(update_fields=["permission_code"])
        else:
            target.scope = cell.scope
            target.save(update_fields=["scope"])
            cell.delete()
    admin = Role.objects.get(code="administrator")
    current = RolePermission.objects.filter(role=admin, permission_code=new_code).first()
    if current is None or current.scope != admin_scope:
        RolePermission.objects.update_or_create(
            role=admin, permission_code=new_code, defaults={"scope": admin_scope}
        )
        record("administrator", new_code, current.scope if current else None, admin_scope)
    diff = [
        {"role": role, "permission": permission, "before": before, "after": after}
        for (role, permission), (before, after) in changes.items()
        if before != after
    ]
    if diff:
        Version = apps.get_model("core", "PermissionMatrixVersion")
        last = Version.objects.aggregate(n=Max("number"))["n"] or 0
        Version.objects.create(number=last + 1, note=note, diff=diff)


def load(apps, schema_editor):
    _move(apps, OLD, NEW, OLD_CODE, NEW_CODE, "all", NOTE)


def unload(apps, schema_editor):
    _move(apps, NEW, OLD, NEW_CODE, OLD_CODE, "read", NOTE_BACK)


class Migration(migrations.Migration):
    dependencies = [("core", "0049_legal_text_note_and_more_texts")]

    operations = [migrations.RunPython(load, unload)]
