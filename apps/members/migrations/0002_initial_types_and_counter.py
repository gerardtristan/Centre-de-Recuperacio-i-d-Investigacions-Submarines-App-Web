"""Dades inicials del M01 (T-M01-11): els dos tipus de soci amb els preus de VC-01 (3500 i
9000 cèntims, validats pel responsable del projecte el 03/11/2026) i la fila única del
comptador de números, a zero. La importació final de Cluber hi posarà el número més alt
importat (RN-M01-32).

Desfer-la esborra aquestes files; només es pot si encara no hi ha cap soci que faci servir
els tipus (PROTECT).
"""

from django.db import migrations

TYPES = [("supporter", "Simpatitzant", 3500), ("full", "Ple dret", 9000)]


def create(apps, schema_editor):
    MembershipType = apps.get_model("members", "MembershipType")
    for code, name, cents in TYPES:
        MembershipType.objects.create(code=code, name=name, annual_fee_cents=cents)
    apps.get_model("members", "MembershipNumberCounter").objects.create(id=1, last_number=0)


def remove(apps, schema_editor):
    apps.get_model("members", "MembershipNumberCounter").objects.filter(id=1).delete()
    apps.get_model("members", "MembershipType").objects.filter(
        code__in=[code for code, _, _ in TYPES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("members", "0001_initial")]

    operations = [migrations.RunPython(create, remove)]
