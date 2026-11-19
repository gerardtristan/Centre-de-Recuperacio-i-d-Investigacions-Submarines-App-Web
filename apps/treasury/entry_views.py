"""Pantalles de tresoreria que mouen diners (T-M04-15, tercer tall; C3, C4 i C7 de M04-3; P-M04-C,
P-M04-D i P-M04-F). Sense wireframe propi (`admin.html` només té l'extracte): segueixen les
pantalles de tresoreria que ja hi ha.

- Traspàs (T6, `services.record_transfer`), arqueig (T7, `services.record_cash_count`) i anul·lar
  un moviment amb motiu (T5, `services.reverse`): permís amb edició al servidor (també el
  torna a comprovar el servei); sense, «no trobat».
- Tot el que mou diners es fa en dos passos: el primer POST mostra què passarà (els comptes,
  l'import, el saldo calculat i la diferència) i el segon ho fa. Un error del servei no desa res
  i surt al formulari.
- Liquidacions del proveïdor (T1 per veure-les; T4 per confirmar una de «rebuda»,
  `settlements.confirm`, també en dos passos). Els motius de les «a revisar», amb el codi del
  problema i la referència del cobrament, sense cap nom.
- Imports en euros amb coma («12,50»), convertits a cèntims abans de cridar el servei.
- Pagament a mà d'un càrrec pendent (P-12; M14 i P10, `services.record_manual_payment`), en dos
  passos: el compte on entra i el motiu; després, l'import i qui paga. El segon pas desa
  exactament el que s'ha mostrat: un testimoni signat (per compte i càrrec, 15 minuts), no els
  camps del formulari. S'hi arriba des de la fitxa del soci i hi torna.
"""

from datetime import date
from decimal import Decimal

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core import signing
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core import charges
from apps.core.charges import euros
from apps.core.models import Charge
from apps.core.permissions import has_perm, permission_required, require_perm
from apps.members.roster import FEES

from . import services, settlements
from .balances import balance
from .models import Movement, ProviderSettlement, TreasuryAccount

VIEW = "treasury.view"  # T1
OWN = (TreasuryAccount.Kind.BANK, TreasuryAccount.Kind.CASH)
# Els que una persona pot anul·lar (P-114, P-115, CA-T06.2); la resta es corregeix d'altra manera.
# Els que la pantalla deixa anul·lar: els mateixos que `services.reverse` accepta a mà. Dins un
# període tancat, el servei respon `PeriodClosed` i surt al formulari (RN-T30; T-M04-15d).
REVERSIBLE = (
    Movement.Kind.FEE,
    Movement.Kind.REFUND,
    Movement.Kind.RETURN,
    Movement.Kind.CASH_ADJUSTMENT,
    Movement.Kind.EXPENSE,
    Movement.Kind.OTHER_INCOME,
)
PROBLEMS = {
    "unknown_payment": _("Cap cobrament amb aquesta referència"),
    "repeated_line": _("Línia repetida a la liquidació"),
    "no_income": _("El cobrament no té l'ingrés al trànsit del proveïdor"),
    "amount_mismatch": _("L'import no és el del cobrament"),
    "refunded": _("El cobrament té devolucions o un retorn"),
    "already_settled": _("El cobrament ja és en una altra liquidació"),
}


def problems_of(settlement):
    """(referència, problema) de cada línia d'una liquidació «a revisar» (CA-T11.2)."""
    return [
        (note.get("reference", ""), PROBLEMS.get(note.get("problem"), note.get("problem")))
        for note in settlement.review_notes
    ]


def _euros(label, minimum):
    return forms.DecimalField(
        label=label, min_value=Decimal(minimum), max_digits=11, decimal_places=2, localize=True
    )


def _cents(value: Decimal) -> int:
    return int(value * 100)


def _date(label):
    return forms.DateField(
        label=label, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
    )


class TransferForm(forms.Form):
    source = forms.ModelChoiceField(
        TreasuryAccount.objects.filter(active=True, kind__in=OWN).order_by("name"),
        label=_("Des del compte"),
    )
    destination = forms.ModelChoiceField(
        TreasuryAccount.objects.filter(active=True, kind__in=OWN).order_by("name"),
        label=_("Cap al compte"),
    )
    amount = _euros(_("Import (€)"), "0.01")
    value_date = _date(_("Data de valor"))
    concept = forms.CharField(label=_("Concepte"), max_length=140)


class CashCountForm(forms.Form):
    account = forms.ModelChoiceField(
        TreasuryAccount.objects.filter(active=True, kind=TreasuryAccount.Kind.CASH).order_by(
            "name"
        ),
        label=_("Caixa"),
    )
    counted = _euros(_("Import comptat (€)"), "0")
    counted_on = _date(_("Data de l'arqueig"))
    adjustment_reason = forms.CharField(
        label=_("Motiu de l'ajust"),
        required=False,
        max_length=500,
        help_text=_(
            "Només si cal ajustar la diferència; sense motiu, l'arqueig no crea cap moviment."
        ),
    )


class ReasonForm(forms.Form):
    reason = forms.CharField(
        label=_("Motiu"), max_length=500, widget=forms.Textarea(attrs={"rows": 3})
    )


class ManualPaymentForm(forms.Form):
    account = forms.ModelChoiceField(
        services.manual_payment_accounts(), label=_("Compte on entra"), empty_label=None
    )
    reason = forms.CharField(
        label=_("Motiu"),
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("Queda al pagament i al registre d'activitat. No hi escriguis dades de salut."),
        error_messages={"required": _("Cal el motiu.")},
    )
    paid_on = _date(_("Data de cobrament"))

    def clean_paid_on(self):
        paid_on = self.cleaned_data["paid_on"]
        if paid_on > timezone.localdate():
            raise ValidationError(_("La data de cobrament no pot ser futura."))
        return paid_on


def _two_steps(request, form, template, extra, act, done):
    """El primer POST valida i mostra la confirmació; el segon (`confirm=1`) crida `act`. Un
    `ValidationError` del servei surt al formulari i no desa res."""
    confirm = False
    if request.method == "POST" and form.is_valid():
        if request.POST.get("confirm") == "1":
            try:
                act(form.cleaned_data)
            except ValidationError as error:
                form.add_error(None, error)
            else:
                messages.success(request, done)
                return redirect("administration:treasury_movements")
        else:
            confirm = True
    return render(request, template, {"form": form, "confirm": confirm, **extra(form)})


@never_cache
@permission_required(services.TRANSFER, write=True)
@require_http_methods(["GET", "POST"])
def transfer_view(request):
    form = TransferForm(request.POST or None, initial={"value_date": timezone.localdate()})

    def act(data):
        services.record_transfer(
            data["source"],
            data["destination"],
            _cents(data["amount"]),
            value_date=data["value_date"],
            concept=data["concept"],
            by=request.user,
        )

    def extra(form):
        amount = form.cleaned_data.get("amount") if form.is_valid() else None
        return {"amount": euros(_cents(amount)) if amount else None}

    return _two_steps(request, form, "treasury/transfer.html", extra, act, _("Traspàs registrat."))


@never_cache
@permission_required(services.CASH_COUNT, write=True)
@require_http_methods(["GET", "POST"])
def cash_count_view(request):
    form = CashCountForm(request.POST or None, initial={"counted_on": timezone.localdate()})

    def act(data):
        services.record_cash_count(
            data["account"],
            _cents(data["counted"]),
            counted_on=data["counted_on"],
            by=request.user,
            adjustment_reason=data["adjustment_reason"],
        )

    def extra(form):
        if not form.is_valid() or form.cleaned_data["counted_on"] > timezone.localdate():
            return {}
        data = form.cleaned_data
        computed = balance(data["account"], data["counted_on"])
        difference = _cents(data["counted"]) - computed
        return {
            "computed": euros(computed),
            "counted": euros(_cents(data["counted"])),
            "difference": euros(difference) if difference >= 0 else f"−{euros(-difference)}",
            "has_difference": bool(difference),
        }

    return _two_steps(
        request, form, "treasury/cash_count.html", extra, act, _("Arqueig registrat.")
    )


@never_cache
@permission_required(services.REVERSE, write=True)
@require_http_methods(["GET", "POST"])
def reverse_view(request, movement_id):
    movement = get_object_or_404(
        Movement.objects.with_reversal().select_related("account"), pk=movement_id
    )
    form = ReasonForm(request.POST or None)

    def act(data):
        services.reverse(movement, reason=data["reason"], by=request.user)

    def extra(form):
        sign = "+" if movement.direction == Movement.Direction.IN else "−"
        return {
            "movement": movement,
            "amount": f"{sign}{euros(movement.amount_cents)}",
            "reversible": movement.kind in REVERSIBLE and not movement.is_reversed,
        }

    return _two_steps(request, form, "treasury/reverse.html", extra, act, _("Moviment anul·lat."))


@never_cache
@permission_required(VIEW)
@require_GET
def settlements_view(request):
    rows = [
        {
            "settlement": s,
            "gross": euros(s.gross_cents),
            "fees": euros(s.fees_cents),
            "net": euros(s.net_cents),
            "problems": problems_of(s),
        }
        for s in ProviderSettlement.objects.select_related("review_closure").order_by(
            "-settled_on", "-pk"
        )
    ]
    can_confirm = has_perm(request.user, settlements.RECONCILE, write=True)
    context = {"rows": rows, "can_confirm": can_confirm}
    return render(request, "treasury/settlements.html", context)


@never_cache
@permission_required(settlements.RECONCILE, write=True)
@require_http_methods(["GET", "POST"])
def settlement_confirm_view(request, settlement_id):
    settlement = get_object_or_404(ProviderSettlement, pk=settlement_id)
    if request.method == "POST":
        try:
            settlements.confirm(settlement, by=request.user)
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
        else:
            messages.success(request, _("Liquidació confirmada: comissions i traspàs al banc."))
        return redirect("administration:treasury_settlements")
    context = {
        "settlement": settlement,
        "net": euros(settlement.net_cents),
        "fees": euros(settlement.fees_cents),
        "items": settlement.items.count(),
    }
    return render(request, "treasury/settlement_confirm.html", context)


CONFIRM_MAX_AGE = 15 * 60  # segons que val el testimoni de la confirmació
# Cert sempre: sense rebut, el servei no desa res (`payments.transfers.on_payment_saved`).
MANUAL_DONE = _(
    "Pagament registrat: el càrrec és pagat, l'ingrés és a la tresoreria i hi ha rebut."
)


def _token_salt(request, charge) -> str:
    return f"treasury.manual_payment:{request.user.pk}:{charge.pk}"


@never_cache
@permission_required(charges.MANUAL_PAYMENT, write=True)
@require_http_methods(["GET", "POST"])
def manual_payment_view(request, charge_id):
    """P-12: registrar a mà el pagament d'un càrrec pendent. Si és una quota, també demana veure
    les quotes (P10), com l'enllaç de la fitxa. El servei torna a comprovar el permís amb el
    càrrec, el compte, el motiu, la data, l'estat, el pagament en curs i que el càrrec no sigui de
    qui el registra."""
    charge = get_object_or_404(Charge.objects.select_related("person"), pk=charge_id)
    fee = getattr(charge, "annual_fee", None)
    if fee is not None:
        require_perm(request, FEES)
    back = (
        reverse("administration:member_detail", args=[fee.member_id])
        if fee is not None
        else reverse("administration:treasury_movements")
    )
    token = request.POST.get("token")
    form = ManualPaymentForm(
        None if token else (request.POST or None),
        initial={"paid_on": timezone.localdate()},
    )
    confirmed = None  # el compte i el motiu que s'han mostrat al segon pas
    errors = []  # del segon pas: el formulari ja no hi és lligat
    if token:
        try:
            data = signing.loads(token, salt=_token_salt(request, charge), max_age=CONFIRM_MAX_AGE)
            account = services.manual_payment_accounts().get(pk=data["account"])
            services.record_manual_payment(
                charge,
                account=account,
                reason=data["reason"],
                paid_on=date.fromisoformat(data["paid_on"]),
                by=request.user,
                proof=request.FILES.get("proof"),  # P-12b: opcional
            )
        except (signing.BadSignature, TreasuryAccount.DoesNotExist):
            errors = [_("Torna a revisar el pagament: la confirmació no és vàlida.")]
        except ValidationError as error:
            errors = error.messages
        else:
            messages.success(request, MANUAL_DONE)
            return redirect(back)
    elif request.method == "POST" and form.is_valid():
        confirmed = form.cleaned_data
        token = signing.dumps(
            {
                "account": confirmed["account"].pk,
                "reason": confirmed["reason"],
                "paid_on": confirmed["paid_on"].isoformat(),
            },
            salt=_token_salt(request, charge),
        )
    context = {
        "form": form,
        "errors": errors or form.non_field_errors(),
        "confirmed": confirmed,
        "token": token if confirmed else None,
        "accounts": services.manual_payment_accounts().exists(),
        "charge": charge,
        "number": services.member_number(charge.person),
        "amount": euros(charge.amount_cents),
        "open": charge.status == Charge.Status.PENDING,
        "own": charge.person_id == request.user.person_id,
        "back": back,
        "max_mb": settings.UPLOAD_MAX_BYTES // (1024 * 1024),
    }
    return render(request, "treasury/manual_payment.html", context)
