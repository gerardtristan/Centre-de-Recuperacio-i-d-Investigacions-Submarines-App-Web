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
from django.db import transaction
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

from . import mandates, preferences
from .forms import MandateForm, RecentAuthForm
from .models import FeeMethod, SepaMandate

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


def _active(member) -> SepaMandate | None:
    mandates_ = SepaMandate.objects.select_related("bank_account")
    return mandates_.filter(member=member, status=SepaMandate.Status.ACTIVE).first()


@sensitive_post_parameters("iban", "password", "code")
@never_cache
@require_http_methods(["GET", "POST"])
def mandate_view(request):
    member, account = _own_member(request), request.user
    active = _active(member)
    signing = settings.MANDATE_SIGNING_ENABLED
    # Apagada, la pàgina només existeix per a qui té un mandat actiu, per poder-lo revocar (P-127).
    if not signing and active is None:
        raise Http404
    person = account.person
    text = consents.current_text(MANDATE_TEXT, language_for(person))
    creditor = settings.SEPA_CREDITOR_IDENTIFIER
    minutes = settings.MANDATE_REAUTH_MINUTES
    form = None
    # Amb un mandat actiu, el formulari (canviar l'IBAN) només surt quan el soci el demana.
    wanted = active is None or "canvia" in request.GET or request.method == "POST"
    if signing and text is not None and creditor and wanted:
        form = MandateForm(
            request.POST or None,
            has_totp=account.has_totp,
            ask_password=not reauth.is_recent(request, minutes),
            initial={"holder_name": f"{person.first_name} {person.last_name}".strip()},
        )
        if request.method == "POST" and form.is_valid():
            error = _reauth_error(request, form, minutes)
            if error is None:
                with transaction.atomic():
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
                    # Signar és triar la domiciliació amb aquest mandat (P-125, decisió 095).
                    preferences.set_preference(member, FeeMethod.DIRECT_DEBIT, by=account)
                    mandates.mail_member(mandates.SIGNED_TEMPLATE, mandate)
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
    context = {
        "active": active,
        "signing": signing and text is not None and bool(creditor),
        "form": form,
        "text": text,
        "creditor": creditor,
        "next_reference": mandates.next_reference(member),
        "reauth_minutes": minutes,
    }
    return render(request, "payments/mandate.html", context)


@sensitive_post_parameters("password", "code")
@never_cache
@require_http_methods(["GET", "POST"])
def revoke_view(request):
    """«Revoca el mandat» (T-M05a-10; P-M05a-C): confirmació i, si la sessió no és recent, la
    contrasenya (RN-M05a-12; CA-M05a-08). Funciona encara que la signatura estigui apagada
    (P-127). Sense mandat actiu no hi ha res a revocar."""
    member, account = _own_member(request), request.user
    after = "payments:mandate" if settings.MANDATE_SIGNING_ENABLED else "payments:fee_method"
    active = _active(member)
    if active is None:
        return redirect(after)
    minutes = settings.MANDATE_REAUTH_MINUTES
    form = RecentAuthForm(
        # Amb la sessió recent, el POST no porta cap camp: el formulari ha d'estar lligat igualment.
        request.POST if request.method == "POST" else None,
        has_totp=account.has_totp,
        ask_password=not reauth.is_recent(request, minutes),
    )
    if request.method == "POST" and form.is_valid():
        if _reauth_error(request, form, minutes) is None:
            mandates.revoke_mandate(member, by=account)
            messages.success(
                request,
                _(
                    "Mandat %(reference)s revocat. A partir d'ara pagaràs cada quota amb "
                    "targeta, Bizum o transferència quan es generi."
                )
                % {"reference": active.reference},
            )
            return redirect(after)
        form.data = form.data.copy()
        form.data.pop("code", None)
    return render(request, "payments/mandate_revoke.html", {"active": active, "form": form})
