from django.contrib.auth.decorators import login_not_required
from django.http import Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import webhooks
from .providers import get_provider
from .providers.base import ProviderNotConfigured


@csrf_exempt  # Servidor a servidor: l'autenticació és la firma del proveïdor, no una sessió.
@login_not_required  # Ruta pública declarada (RN-40; M05a-8).
@require_POST
def provider_notification(request, provider_code: str):
    try:
        provider = get_provider()
    except ProviderNotConfigured:
        raise Http404 from None
    if provider.code != provider_code:
        raise Http404
    return HttpResponse(status=webhooks.receive(provider, request).http_status)
