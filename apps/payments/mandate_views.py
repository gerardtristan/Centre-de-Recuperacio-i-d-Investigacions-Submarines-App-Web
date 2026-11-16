"""`/socis/pagaments/mandat/`: signar el mandat SEPA des del compte personal (T-M05a-09; P-M05a-B;
RN-M05a-02 a 07 i 12; CA-M05a-02, 03 i 08; wireframe `socis.html#pagaments-mandat`).

- Apagada per defecte (`MANDATE_SIGNING_ENABLED`): sense l'aprovació de la junta del text
  (T-M05a-01) la ruta respon «no trobat». Sense text publicat o sense identificador de
  creditor, no es signa.
- Només el soci de la sessió (cap identificador a la ruta) i amb número de soci.
- L'IBAN: el valida el formulari; si és invàlid o falla una altra cosa, el camp torna buit. No surt
  mai sencer a la resposta, al registre d'activitat ni als informes d'error
  (`sensitive_post_parameters`).
- Reautenticació (RN-M05a-12): si l'última autenticació té més de `MANDATE_REAUTH_MINUTES`.
"""

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from apps.accounts import reauth
from apps.accounts.security import WRONG_CODE, WRONG_PASSWORD
from apps.core import consents
from apps.core.persons import language_for
from apps.members.models import Member

from . import mandates
from .forms import MandateForm
from .models import SepaMandate

MANDATE_TEXT = "sepa_mandate"


def _own_member(request) -> Member:
    member = Member.objects.filter(
        person=request.user.person,
        status__in=[Member.Status.ACTIVE, Member.Status.UNPAID],
        member_number__isnull=False,
    ).first()
    if member is None:
        raise Http404
    return member


def _reauth_error(request, form, minutes):
    """None si la sessió és recent o les credencials són bones; si no, l'error, que queda al
    formulari (RN-M05a-12)."""
    if "password" in form.fields and "password" not in request.POST:
        # La sessió ha caducat amb la pàgina oberta: es demana sense comptar cap intent (P-126).
        error, field = _("Torna a escriure la contrasenya."), "password"
    else:
        error = reauth.require_recent_auth(
            request,
            minutes,
            password=form.cleaned_data.get("password", ""),
            code=form.cleaned_data.get("code", ""),
        )
        field = {WRONG_PASSWORD: "password", WRONG_CODE: "code"}.get(error)
    if error:
        form.add_error(field, error)
    return error


@sensitive_post_parameters("iban", "password", "code")
@never_cache
@require_http_methods(["GET", "POST"])
def mandate_view(request):
    if not settings.MANDATE_SIGNING_ENABLED:
        raise Http404
    member, account = _own_member(request), request.user
    person = account.person
    text = consents.current_text(MANDATE_TEXT, language_for(person))
    creditor = settings.SEPA_CREDITOR_IDENTIFIER
    minutes = settings.MANDATE_REAUTH_MINUTES
    form = None
    if text is not None and creditor:
        form = MandateForm(
            request.POST or None,
            has_totp=account.has_totp,
            ask_password=not reauth.is_recent(request, minutes),
            initial={"holder_name": f"{person.first_name} {person.last_name}".strip()},
        )
        if request.method == "POST" and form.is_valid():
            error = _reauth_error(request, form, minutes)
            if error is None:
                mandate = mandates.create_mandate(
                    member,
                    iban=form.cleaned_data["iban"],
                    holder_name=form.cleaned_data["holder_name"],
                    holder_is_member=not form.cleaned_data["other_holder"],
                    legal_text=text,
                    account=account,
                    creditor_identifier=creditor,
                    evidence={"channel": "web", "text_version": text.version},
                )
                messages.success(
                    request,
                    _("Mandat signat. La referència és %(reference)s.")
                    % {"reference": mandate.reference},
                )
                return redirect("payments:mandate")
        if form.is_bound:
            # Ni l'IBAN ni el codi no tornen mai a la pantalla (RN-M05a-06).
            form.data = form.data.copy()
            for name in ("iban", "code"):
                form.data.pop(name, None)
    active = (
        SepaMandate.objects.select_related("bank_account")
        .filter(member=member, status=SepaMandate.Status.ACTIVE)
        .first()
    )
    context = {
        "active": active,
        "form": form,
        "text": text,
        "creditor": creditor,
        "next_reference": mandates.next_reference(member),
        "reauth_minutes": minutes,
    }
    return render(request, "payments/mandate.html", context)
