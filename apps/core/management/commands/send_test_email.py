"""Posa a la cua un correu de prova (plantilla `emails/prova`) per comprovar l'enviament.

En local va a la bústia de proves (Mailpit); a producció serveix per comprovar el proveïdor i
el domini remitent (checklist G1). Només surt quan la cua el processa
(`python manage.py procrastinate worker`). Fes-lo servir només amb adreces inventades o pròpies.
"""

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email

from apps.core import mail


class Command(BaseCommand):
    help = "Posa a la cua un correu de prova cap a l'adreça indicada."

    def add_arguments(self, parser):
        parser.add_argument("address", help="Adreça de destí (inventada o pròpia).")

    def handle(self, *args, address, **options):
        try:
            validate_email(address)
        except ValidationError:
            raise CommandError(f"Adreça no vàlida: {address}") from None
        email = mail.queue_email("prova", to=address)
        self.stdout.write(f"Correu de prova {email.pk} a la cua.")
