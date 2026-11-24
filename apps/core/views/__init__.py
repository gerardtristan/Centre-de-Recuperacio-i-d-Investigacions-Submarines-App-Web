import datetime

from django.contrib.auth.decorators import login_not_required
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import content_disposition_header
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .. import files
from ..models import OutgoingEmail, PrivateFile


@require_GET
def home(request):
    return render(request, "core/home.html")


@login_not_required
@require_GET
def health(request):
    """Comprovació de salut per al proxy i el monitor. No diu res de l'estat intern."""
    return HttpResponse("ok", content_type="text/plain")


QUEUE_ALERT_AGE = datetime.timedelta(minutes=2)


@login_not_required
@never_cache
@require_GET
def queue_health(request):
    """Comprovació de la cua per al monitor (T-M01-39b; 011): error (503) si una petició de «He
    oblidat la contrasenya» o un correu fa més de 2 minuts que esperen, o si cap worker no ha
    donat senyals de vida en 2 minuts. Pública declarada i sense cap dada: «ok» o «error».
    A part de `health`, perquè el proxy no tregui l'aplicació de servei si s'atura la cua."""
    from procrastinate.contrib.django.models import ProcrastinateWorker

    from apps.accounts.models import EmailLinkRequest

    limit = timezone.now() - QUEUE_ALERT_AGE
    stuck = (
        EmailLinkRequest.objects.filter(
            status=EmailLinkRequest.Status.PENDING, created_at__lt=limit
        ).exists()
        or OutgoingEmail.objects.filter(
            status=OutgoingEmail.Status.QUEUED, created_at__lt=limit
        ).exists()
        or not ProcrastinateWorker.objects.filter(last_heartbeat__gte=limit).exists()
    )
    if stuck:
        return HttpResponse("error", status=503, content_type="text/plain")
    return HttpResponse("ok", content_type="text/plain")


@require_GET
def private_file(request, file_id):
    """Comprova el compte i l'objecte i redirigeix a la URL signada (annex B, RN-B2). Un fitxer
    xifrat no surt mai per URL signada: es desxifra aquí, amb el registre (T-M09-25a)."""
    file = PrivateFile.objects.filter(pk=file_id).first()
    if file is None:
        raise Http404
    if file.kind in files.ENCRYPTED_KINDS:
        content = files.open_decrypted(request.user, file, request=request)
        response = HttpResponse(content, content_type=file.content_type)
        # Les imatges, en línia (per a un <img>); la resta, com a descàrrega.
        response["Content-Disposition"] = content_disposition_header(
            not file.content_type.startswith("image/"), file.download_name
        )
        response["X-Content-Type-Options"] = "nosniff"
    else:
        response = redirect(files.signed_url(request.user, file, request=request))
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response


@login_not_required
@require_GET
def local_private_file(request, token):
    """Fa el paper de Scaleway fora de producció: l'enllaç signat és la credencial i, caducat
    o manipulat, es rebutja (CA-B5). La ruta només existeix si l'emmagatzematge és local."""
    try:
        file, handle = files.open_local(token)
    except files.LinkRejected:
        return HttpResponseForbidden()
    response = FileResponse(
        handle, content_type=file.content_type, as_attachment=True, filename=file.download_name
    )
    response["Cache-Control"] = "no-store"
    return response
