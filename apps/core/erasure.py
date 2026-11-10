"""Sol·licitud d'esborrat de les dades d'una persona (P-M01-F, pas 3; peça mínima de la T-M01-22,
074 punt 20). Només la crea; atendre-la, anonimitzar i desactivar són de la resta de la T-M01-22.

La reautenticació (RN-M01-57, `accounts.reauth.require_recent_auth` amb `minutes=0`) la fa la
vista que crida aquest servei, a la mateixa petició.
"""

from django.db import transaction

from . import audit
from .models import ErasureRequest, Person


def pending_request(person) -> ErasureRequest | None:
    return person.erasure_requests.filter(status=ErasureRequest.Status.PENDING).first()


def request_erasure(person, *, by, request=None) -> tuple[ErasureRequest, bool]:
    """Crea la sol·licitud pendent de la persona i la registra. Si ja n'hi ha una de pendent, la
    torna sense crear-ne cap altra. Torna (sol·licitud, creada)."""
    with transaction.atomic():
        # Dues peticions alhora de la mateixa persona: la segona espera i troba la primera.
        Person.objects.select_for_update().filter(pk=person.pk).first()
        existing = pending_request(person)
        if existing is not None:
            return existing, False
        created = ErasureRequest.objects.create(
            person=person, requested_by=by, channel=ErasureRequest.Channel.WEB
        )
        audit.record(
            audit.Action.ERASURE_REQUESTED,
            actor=by,
            target=created,
            details={"channel": created.channel},
            request=request,
        )
    return created, True
