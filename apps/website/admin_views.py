"""Pantalles d'administració del contacte (WP5 i WP8; P-M07-D, RN-M07-07 i 14). S'inclouen a
`accounts/admin_urls.py` des de `admin_urls.py`.

- Safata (WP5, `website.contact`): els missatges dels motius que té algun rol del compte
  (`contact.visible_to`), filtrables per motiu; la fitxa, respondre i tancar amb motiu. Un missatge
  fora de l'abast és «no trobat», també en respondre'l o tancar-lo (ho tornen a mirar els serveis).
- Motius (WP8, `website.contact_reasons`): crear, canviar el nom, l'ordre i els rols que el reben,
  i activar-lo o desactivar-lo. No s'esborra: els missatges hi apunten (PROTECT). Cada canvi
  queda al registre amb el valor anterior.
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core import audit
from apps.core.models import Role
from apps.core.permissions import active_role_codes, has_perm, request_permissions, require_perm

from . import contact
from .models import ContactMessage, ContactReason

REASONS = "website.contact_reasons"  # WP8
ACTION_REASON = "website.contact_reason_changed"
INBOX = "administration:website_contact"
REASON_LIST = "administration:website_contact_reasons"


class ReplyForm(forms.Form):
    answer = forms.CharField(
        label=gettext_lazy("Resposta"), max_length=5000, widget=forms.Textarea(attrs={"rows": 6}),
        help_text=gettext_lazy("Surt per correu des de l'adreça del club."),
    )  # fmt: skip


class CloseForm(forms.Form):
    reason = forms.CharField(
        label=gettext_lazy("Motiu del tancament"), max_length=300,
        help_text=contact.CLOSE_REASON_HELP,
    )  # fmt: skip


class ReasonForm(forms.ModelForm):
    class Meta:
        model = ContactReason
        fields = ["name", "order", "roles", "active"]
        widgets = {"roles": forms.CheckboxSelectMultiple}
        help_texts = {
            "roles": gettext_lazy(
                "Els comptes d'aquests rols que poden veure el contacte reben l'avís i el veuen a "
                "la safata."
            ),
            "active": gettext_lazy("Un motiu inactiu no surt al formulari públic."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["roles"].queryset = Role.objects.filter(is_management=True).order_by("pk")


def _visible_reasons(account):
    roles = active_role_codes(account)
    return ContactReason.objects.filter(roles__code__in=roles).distinct()


@never_cache
@require_GET
def inbox_view(request):
    require_perm(request, contact.PERMISSION)
    reasons = list(_visible_reasons(request.user))
    found = contact.visible_to(request.user).select_related("reason")
    chosen = next((r for r in reasons if str(r.pk) == request.GET.get("motiu")), None)
    if chosen is not None:
        found = found.filter(reason=chosen)
    context = {"messages_list": found, "reasons": reasons, "chosen": chosen}
    context["can_manage_reasons"] = has_perm(request.user, REASONS)
    return render(request, "website/admin/contact_inbox.html", context)


def _message_page(request, message, *, reply_form=None, close_form=None):
    can_answer = message.status == ContactMessage.Status.NEW and has_perm(
        request.user, contact.PERMISSION, write=True, permissions=request_permissions(request)
    )
    context = {
        "message": message,
        "reply_form": (reply_form or ReplyForm()) if can_answer else None,
        "close_form": (close_form or CloseForm()) if can_answer else None,
    }
    return render(request, "website/admin/contact_message.html", context)


def _visible_or_404(request, pk):
    require_perm(request, contact.PERMISSION)
    return get_object_or_404(contact.visible_to(request.user).select_related("reason"), pk=pk)


@never_cache
@require_GET
def message_view(request, pk):
    return _message_page(request, _visible_or_404(request, pk))


def _act(request, pk, form_class, action, success):
    message = _visible_or_404(request, pk)
    require_perm(request, contact.PERMISSION, write=True)
    form = form_class(request.POST)
    if form.is_valid():
        try:
            action(message, form.cleaned_data)
        except ValidationError as error:  # ja respost o tancat (des d'una altra pestanya)
            messages.error(request, " ".join(error.messages))
            return redirect("administration:website_contact_message", message.pk)
        messages.success(request, success)
        return redirect(INBOX)
    key = "reply_form" if form_class is ReplyForm else "close_form"
    return _message_page(request, message, **{key: form})


@never_cache
@require_POST
def reply_view(request, pk):
    return _act(
        request, pk, ReplyForm,
        lambda message, data: contact.reply(message, actor=request.user, answer=data["answer"]),
        _("Resposta enviada."),
    )  # fmt: skip


@never_cache
@require_POST
def close_view(request, pk):
    return _act(
        request, pk, CloseForm,
        lambda message, data: contact.close(message, actor=request.user, reason=data["reason"]),
        _("Missatge tancat."),
    )  # fmt: skip


@never_cache
@require_GET
def reasons_view(request):
    require_perm(request, REASONS)
    context = {
        "reasons": ContactReason.objects.prefetch_related("roles"),
        "can_edit": has_perm(request.user, REASONS, write=True),
    }
    return render(request, "website/admin/contact_reasons.html", context)


def _snapshot(reason) -> dict:
    if reason.pk is None:
        return {}
    roles = sorted(reason.roles.values_list("code", flat=True))
    return {"name": reason.name, "order": reason.order, "active": reason.active, "roles": roles}


@never_cache
@require_http_methods(["GET", "POST"])
def reason_edit_view(request, pk=None):
    require_perm(request, REASONS, write=True)
    reason = get_object_or_404(ContactReason, pk=pk) if pk else ContactReason()
    form = ReasonForm(request.POST or None, instance=reason)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            before = _snapshot(reason)
            reason = form.save()
            audit.record(
                ACTION_REASON, actor=request.user, target=reason, request=request,
                details={"before": before, "after": _snapshot(reason)},
            )  # fmt: skip
        messages.success(request, _("Motiu desat."))
        return redirect(REASON_LIST)
    return render(
        request, "website/admin/contact_reason_form.html", {"form": form, "reason": reason}
    )
