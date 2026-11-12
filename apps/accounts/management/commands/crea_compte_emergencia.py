"""Crea un compte d'emergència des del servidor (T-M00-03; HU-10; 079, A-30).

Ús: python manage.py crea_compte_emergencia <nom-d-usuari>

La contrasenya es demana dues vegades sense mostrar-la i no surt mai a la sortida ni al registre.
El compte es lliga a una persona tècnica sense dades personals i rep el rol administrador; el
doble factor es dona d'alta en la primera entrada. Qui custodia les credencials: [A validar:
junta].
"""

from getpass import getpass

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.accounts import emergency


class Command(BaseCommand):
    help = "Crea un compte d'emergència lligat a una persona tècnica (T-M00-03)."

    def add_arguments(self, parser):
        parser.add_argument("username", help="Nom d'usuari del compte d'emergència.")

    def handle(self, *args, username, **options):
        password = getpass("Contrasenya: ")
        if password != getpass("Torna-la a escriure: "):
            raise CommandError("Les dues contrasenyes no coincideixen. No s'ha creat res.")
        try:
            account = emergency.create(username, password)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from None
        ready = emergency.ready_accounts().count()
        self.stdout.write(
            f"Compte d'emergència creat: {account.login}. Ha d'entrar a l'administració per "
            f"donar d'alta el doble factor i guardar els codis de recuperació fora de línia. "
            f"Comptes d'emergència a punt: {ready} de {emergency.MINIMUM}."
        )
