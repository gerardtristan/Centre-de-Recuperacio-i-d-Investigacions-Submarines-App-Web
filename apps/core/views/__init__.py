from django.contrib.auth.decorators import login_not_required
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from .. import files
from ..models import PrivateFile


@require_GET
def home(request):
    return render(request, "core/home.html")


@login_not_required
@require_GET
def health(request):
    """Comprovació de salut per al proxy i el monitor. No diu res de l'estat intern."""
    return HttpResponse("ok", content_type="text/plain")


@require_GET
def private_file(request, file_id):
    """Comprova el compte i l'objecte i redirigeix a la URL signada (annex B, RN-B2)."""
    file = PrivateFile.objects.filter(pk=file_id).first()
    if file is None:
        raise Http404
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
