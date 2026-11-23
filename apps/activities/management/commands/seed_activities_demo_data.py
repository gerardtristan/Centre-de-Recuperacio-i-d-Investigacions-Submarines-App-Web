"""Carrega les dades inventades del 02 (T-M02-25) a una base que ja té les de `seed_demo_data`.
Mai en producció: les mateixes condicions que aquella ordre (desenvolupament o proves amb
`DEBUG`, base local) i, a més, cap activitat a la base.

Fa servir els comptes de prova `admin-demo` (com a responsable) i `instructor-demo`, i les
quatre primeres persones de prova que no són de cap compte d'administració."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from apps.accounts.models import Account
from apps.activities import demo_data
from apps.activities.models import Activity
from apps.core.management.commands.seed_demo_data import ALLOWED_SETTINGS, LOCAL_HOSTS
from apps.core.models import Department, Person


def check_can_run() -> None:
    if settings.SETTINGS_MODULE not in ALLOWED_SETTINGS or not settings.DEBUG:
        raise CommandError(
            "Només s'executa en desenvolupament o proves, amb DEBUG actiu. Mai en producció."
        )
    if connection.settings_dict["HOST"] not in LOCAL_HOSTS:
        raise CommandError("Només s'executa amb una base de dades local.")
    if Activity.objects.exists():
        raise CommandError("La base ja té activitats: les dades del 02 només es carreguen un cop.")


class Command(BaseCommand):
    help = "Crea les dades inventades del 02 (catàleg, llocs, activitats, inscrits i avaluacions)."

    def handle(self, *args, **options):
        check_can_run()
        try:
            manager = Account.objects.get(login="admin-demo")
            instructor = Account.objects.get(login="instructor-demo")
        except Account.DoesNotExist as missing:
            raise CommandError("Primer cal executar seed_demo_data.") from missing
        admins = Account.objects.filter(kind=Account.Kind.ADMIN).values("person")
        people = Person.objects.filter(status=Person.Status.ACTIVE).exclude(pk__in=admins)
        with transaction.atomic():
            result = demo_data.create(
                manager=manager,
                instructor=instructor,
                department=Department.objects.get(name=Department.GENERAL),
                participants=list(people.order_by("pk")[:4]),
            )
        self.stdout.write(
            f"Mòdul 02: {result.entries} fitxes del catàleg, {result.activities} "
            f"activitats i {result.enrolments} inscripcions."
        )
