"""Pantalla de la prova de Cluber (T-M01-24; CA-M01-20, CA-20.1), alta presencial (T-M01-13),
llistat, fitxa i exportació de socis (T-M01-15) i altes pendents (T-M01-14), al final del fitxer.

Precisions: files de la T-M01-24 a docs/planning.md#ajustos-060-lectura (pantalla, recepció,
CSRF, registre de la prova i numeració).

- P18 es comprova abans de llegir el fitxer. La vista exterior és exempta de CSRF només perquè
  els gestors de pujada es puguin canviar abans que el CSRF llegeixi el POST (patró documentat
  de Django); `_protected` sí que està protegida.
- Un sol gestor de pujada, en memòria, que compta els bytes rebuts: mai cap fitxer temporal.
  Exactament un fitxer al camp `fitxer`. Si el cos declarat supera 1 MiB + 64 KiB, es rebutja
  abans de llegir-lo (413, sense registre: encara no s'ha comprovat el CSRF).
- Una entrada al registre per intent autoritzat i amb CSRF vàlid. L'empremta, només amb el
  fitxer complet i si no s'ha rebutjat per IBAN. La pantalla només fa servir `summary()`.
"""

from collections import Counter

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.uploadhandler import MemoryFileUploadHandler, StopUpload
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.http.multipartparser import MultiPartParserError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts import personal_reset
from apps.core import audit, charges, persons
from apps.core.models import Charge
from apps.core.permissions import (
    has_perm,
    permission_required,
    request_permissions,
    require_perm,
)
from apps.members import (
    admissions,
    cards,
    fees,
    instalments,
    join,
    member_edit,
    member_requests,
    roster,
    services,
)
from apps.members import birth_date as birth_date_rules
from apps.members.fee_rules import local_today
from apps.members.forms import LEGAL_LABELS, JoinForm
from apps.members.imports import cluber
from apps.members.models import AnnualFee, Member, MemberRequest
from apps.members.services import OwnMemberChange
from apps.members.views.public import PREVIEW, render_preview

FIELD = "fitxer"
# Marge per a les capçaleres del multipart: no amplia el límit del CSV (cluber.MAX_BYTES).
BODY_CEILING = cluber.MAX_BYTES + 64 * 1024

RECEPTION_MESSAGES = {
    "too_large": cluber.MESSAGES["too_large"],
    "no_file": _("No s'ha rebut cap fitxer. Tria un fitxer CSV i torna-ho a provar."),
    "too_many_files": _("Cal enviar exactament un fitxer CSV, al camp del formulari."),
    "unreadable": _("No s'ha pogut llegir la pujada. Torna-ho a provar."),
}
RELATION = _("Relació entre el document i el número")
WHOLE_ROW = _("Tot el registre")


class _OneFileInMemory(MemoryFileUploadHandler):
    """Un sol fitxer al camp previst, només en memòria, amb els bytes comptats en arribar."""

    def __init__(self, request=None):
        super().__init__(request)
        self.problem = None
        self.files = 0
        self.received = 0

    def handle_raw_input(self, *args, **kwargs):
        # Sempre en memòria, sigui quina sigui la mida declarada: no hi ha cap gestor de disc.
        self.activated = True

    def new_file(self, field_name, *args, **kwargs):
        self.files += 1
        if field_name != FIELD or self.files > 1:
            self.problem = "too_many_files"
            raise StopUpload(connection_reset=False)
        super().new_file(field_name, *args, **kwargs)

    def receive_data_chunk(self, raw_data, start):
        self.received += len(raw_data)
        if self.received > cluber.MAX_BYTES:
            self.problem = "too_large"
            raise StopUpload(connection_reset=False)
        return super().receive_data_chunk(raw_data, start)


def _declared_length(request) -> int:
    try:
        return int(request.META.get("CONTENT_LENGTH") or 0)
    except ValueError:
        return 0


@csrf_exempt
@never_cache
@require_http_methods(["GET", "POST"])
@permission_required("members.cluber_import.run")
def cluber_preview_view(request):
    handler = _OneFileInMemory(request)
    request.upload_handlers = [handler]  # abans que res llegeixi el POST
    if request.method == "POST" and _declared_length(request) > BODY_CEILING:
        return _page(request, reception="too_large", status=413)
    try:
        return _protected(request, handler)
    except MultiPartParserError:
        return _page(request, reception="unreadable", status=400)


@csrf_protect
def _protected(request, handler):
    if request.method == "GET":
        return _page(request)
    files = request.FILES.getlist(FIELD)
    problem = handler.problem
    if problem is None and len(files) != 1:
        problem = "no_file" if not files else "too_many_files"
    if problem:
        _record(request, problem)
        status = 413 if problem == "too_large" else 400
        return _page(request, reception=problem, status=status, recorded=True)

    data = files[0].read()
    summary = cluber.preview(data).summary()
    rejected = summary["rejected"]
    # 079 (A-26, P-65 punt 1): l'empremta registrada és la canònica de les columnes llegides,
    # calculada sense la d'IBAN; mai la del fitxer tal com arriba, que depèn de l'IBAN.
    _record(request, rejected, summary["counts"], summary["fingerprint"] or None)
    return _page(request, summary=summary, recorded=True)


def _record(request, rejected, counts=None, sha256=None):
    details = {"rejected": rejected, "counts": counts or {}}
    if sha256:
        details["file_sha256"] = sha256
    audit.record(audit.Action.CLUBER_PREVIEW, actor=request.user, details=details, request=request)


def _page(request, *, summary=None, reception=None, status=200, recorded=False):
    context = {
        "summary": summary,
        "reception": RECEPTION_MESSAGES.get(reception),
        "recorded": recorded,
    }
    if summary:
        context.update(_display(summary))
    return render(request, "members/cluber_preview.html", context, status=status)


def _display(summary):
    """Textos per a la pantalla, només a partir del resum segur (codis, files i columnes)."""
    messages = cluber.MESSAGES
    problems = []
    pending = Counter()
    filled = Counter()
    types = Counter()
    for row in summary["rows"]:
        filled.update(row["fields"])
        if row["member_type"]:
            types[row["member_type"], row["member_type_by"]] += 1
        for kind, codes in ((_("Error"), row["errors"]), (_("Advertiment"), row["warnings"])):
            columns = row["error_columns"] if codes is row["errors"] else [""] * len(codes)
            for code, column in zip(codes, columns, strict=True):
                if column:
                    label = column
                elif code == "identity_conflict":
                    label = RELATION
                else:
                    label = WHOLE_ROW
                problems.append((row["row"], label, kind, messages[code]))
        pending.update(row["pending"])
    return {
        "rejection": messages.get(summary["rejected"]) if summary["rejected"] else None,
        "file_warnings": [messages[code] for code in summary["warnings"]],
        "problems": problems,
        "pending": [(messages[code], count) for code, count in sorted(pending.items())],
        # Llista per a la secretaria (072, Q-071): només els números de registre, cap valor.
        "left_rows": [row["row"] for row in summary["rows"] if row.get("left_in_cluber")],
        "omitted": sorted(summary["catalogue_omitted"].items()),
        "encoding": cluber.ENCODING_LABELS.get(summary["encoding"]),
        "format": summary["format"],
        "would_import": [(label, filled[target]) for target, label in cluber.FIELD_LABELS.items()],
        "types": [
            (summary["type_names"][code], cluber.TYPE_BY_LABELS[by], count)
            for (code, by), count in sorted(types.items())
        ],
    }


# --- Alta presencial (T-M01-13; P2; P-M01-A pas 3b) --------------------------------------------
# El mateix formulari i el mateix servei que la web; consentiment presencial amb el compte que el
# registra (CA-17.1). Si hi ha un possible duplicat o una alta pendent, només ho diu a qui també
# pot consultar les sol·licituds (P3a), on ho veurà igualment; si no, la resposta és neutra.

JOIN_DONE_KEY = "members_join_in_person_done"


@never_cache
@require_http_methods(["GET", "POST"])
@permission_required("members.create_in_person")
def join_in_person_view(request):
    texts = join.current_texts()
    if texts is None:
        return render(request, "members/join_in_person.html", {"unavailable": True}, status=503)
    done = request.session.pop(JOIN_DONE_KEY, None) if request.method == "GET" else None
    form = JoinForm(request.POST or None, texts=texts, in_person=True)
    if request.method == "POST" and request.POST.get(PREVIEW):
        return render_preview(request, form)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            outcome = join.submit(
                form.cleaned_data,
                channel=MemberRequest.Channel.IN_PERSON,
                by=request.user,
                request=request,
            )
        can_see = has_perm(request.user, "members.requests.view")
        request.session[JOIN_DONE_KEY] = {
            "duplicate": can_see and outcome.duplicate,
            "already_pending": can_see and outcome.request is None,
        }
        response = redirect("administration:join_in_person")
        response.status_code = 303
        return response
    context = {"form": form, "texts": texts, "done": done}
    return render(request, "members/join_in_person.html", context)


# --- Llistat, fitxa i exportació de socis (T-M01-15; P4, P11; RN-M01-71, CA-M01-64) -----------
# Només lectura. El permís es comprova abans que el mètode: sense permís, sempre «no trobat».
# Què veu cada compte: `apps/members/roster.py`.

PER_PAGE = 50


def _filters(request, vis):
    form = roster.MemberFilterForm(
        request.GET or None,
        can_search_document=vis.identity,
        can_see_birth_date=vis.birth_date,
    )
    data = {}
    if form.is_bound:
        form.is_valid()  # els camps vàlids filtren; un valor manipulat no filtra
        data = form.cleaned_data
    return form, data


@never_cache
@permission_required(roster.LIST)
@require_GET
def members_list_view(request):
    perms = request_permissions(request)
    vis = roster.visibility_for(request.user, perms)
    form, data = _filters(request, vis)
    members = roster.filtered_members(
        data, can_search_document=vis.identity, can_see_birth_date=vis.birth_date
    )
    if vis.fees:
        members = roster.with_fee_data(members)
    page = Paginator(members, PER_PAGE).get_page(request.GET.get("pagina"))
    rows = [(m, roster.fee_state(m) if vis.fees else None) for m in page]
    context = {
        "form": form,
        "page": page,
        "rows": rows,
        "vis": vis,
        "no_members": not Member.objects.exists(),
        "can_export": has_perm(request.user, roster.EXPORT, permissions=perms),
        "export_formats": roster.ExportForm.base_fields["format"].choices,
        "can_import": has_perm(request.user, "members.cluber_import.run", permissions=perms),
        "can_join": has_perm(request.user, "members.create_in_person", permissions=perms),
    }
    return render(request, "members/member_list.html", context)


def _fee_rows(member):
    """Les quotes del soci per a la fitxa (T-M01-40), de la més recent a la més antiga."""
    rows = []
    for fee in (
        AnnualFee.objects.filter(member=member)
        .select_related("charge", "exemption")
        .order_by("-period", "-sequence", "-pk")
    ):
        rows.append(
            {
                "fee": fee,
                "amount": charges.euros(fee.charge.amount_cents),
                "open": fee.charge.status == Charge.Status.PENDING,
                "annual": fee.kind == AnnualFee.Kind.ANNUAL,
                "exemption": getattr(fee, "exemption", None),
            }
        )
    return rows


@never_cache
@permission_required(roster.LIST)
@require_GET
def member_detail_view(request, pk):
    perms = request_permissions(request)
    vis = roster.visibility_for(request.user, perms)
    members = Member.objects.select_related("person", "type")
    if vis.fees:
        members = roster.with_fee_data(members)
    member = get_object_or_404(members, pk=pk)
    history = member.status_changes.select_related(
        "from_type", "to_type", "actor_account"
    ).order_by("-created_at", "-id")
    consents = []
    if vis.identity:
        latest = {}
        for consent in member.person.consents.select_related("legal_text"):
            latest[consent.legal_text.kind] = consent  # ordenats per data: queda l'última
        consents = [
            (LEGAL_LABELS.get(kind, kind), latest[kind]) for kind in sorted(latest)
        ]  # (nom del text, últim consentiment), com a l'àrea del soci
    today = local_today()
    years = None
    if vis.full and member.joined_on:  # Q-075: sense data, sense antiguitat
        joined = member.joined_on
        years = today.year - joined.year - ((today.month, today.day) < (joined.month, joined.day))
    context = {
        "member": member,
        "person": member.person,
        "vis": vis,
        "fee": roster.fee_state(member, today) if vis.fees else None,
        "years": years,
        "history": history,
        "consents": consents,
        "document": roster.document_label(member.person) if vis.identity else "",
        # Sense C1, només la franja d'edat; la data no arriba a la plantilla (RN-M01-48).
        "birth_date": member.person.birth_date if vis.birth_date else None,
        "age_band": None if vis.birth_date else persons.age_band(member.person, today),
        # Decisió 081, punt 16: declarada o comprovada, i l'acció per marcar-la (P5 amb C1).
        "birth_date_checked_at": member.person.birth_date_checked_at if vis.birth_date else None,
        "can_check_birth_date": vis.birth_date
        and member.person.birth_date is not None
        and member.person.birth_date_checked_at is None
        and member.person_id != request.user.person_id
        and birth_date_rules.can_check(request.user, perms),
        # Decisió 081, punt 24 (P-52): restablir en persona el doble factor del compte personal.
        "can_reset_totp": member.person_id != request.user.person_id
        and personal_reset.can_reset(request.user, perms)
        and personal_reset.personal_account_with_totp(member.person) is not None,
        # T-M01-15b: enllaços i historial de la data d'alta. Els serveis ho tornen a comprovar.
        "can_edit": bool(member_edit.editable_fields(request.user, perms)),
        "can_correct_join_date": member_edit.can_correct_join_date(request.user, perms),
        # 079 (RN-M01-87): tornar a enviar la invitació del compte personal (M2 i P4).
        "can_invite": admissions.can_invite(request.user, member, perms),
        # 079 (A-21, RN-M01-92): el carnet vigent i, amb P21, revocar-lo amb motiu.
        "card": cards.active_card(member),
        "can_revoke_card": cards.can_revoke(request.user, perms),
        # T-M01-40: les quotes del soci (P10) i, amb P22, eximir-ne o anul·lar-ne una. Els
        # serveis tornen a comprovar el permís, el motiu i el conflicte d'interès.
        "fee_rows": _fee_rows(member) if vis.fees else [],
        "can_exempt": vis.fees
        and member.person_id != request.user.person_id
        and fees.can_exempt(request.user, perms),
        # P-12: el pagament a mà d'una quota pendent (M14), a la pantalla de tresoreria.
        "can_record_payment": vis.fees
        and member.person_id != request.user.person_id
        and has_perm(request.user, charges.MANUAL_PAYMENT, write=True, permissions=perms),
        # T-M01-17: «Crea una baixa» (P7 amb escriptura); el servei ho torna a comprovar.
        "can_create_leave": member.status != Member.Status.LEFT
        and has_perm(
            request.user, member_requests.RESOLVE_PERMISSION, write=True, permissions=perms
        )
        and not member_requests.open_leaves(member).exists(),
        "join_date_changes": (
            member.join_date_changes.select_related("actor_account").order_by("-created_at", "-id")
            if vis.full
            else []
        ),
    }
    for row in context["fee_rows"]:  # M14 amb el càrrec (nivell d'objecte)
        row["can_pay"] = (
            context["can_record_payment"]
            and row["open"]
            and has_perm(
                request.user,
                charges.MANUAL_PAYMENT,
                row["fee"].charge,
                write=True,
                permissions=perms,
            )
        )
    return render(request, "members/member_detail.html", context)


@never_cache
@permission_required(roster.EXPORT)
@require_POST
def members_export_view(request):
    """.xlsx o CSV amb els filtres del llistat (RN-M01-71). Es genera en memòria i no es desa
    enlloc; el registre només guarda els filtres, el nombre de files i el format, mai el text de
    la cerca. Un format no vàlid es rebutja sense fitxer ni registre."""
    perms = request_permissions(request)
    require_perm(request, roster.LIST)  # s'exporta el que es pot llistar
    vis = roster.visibility_for(request.user, perms)
    form = roster.ExportForm(
        request.POST, can_search_document=vis.identity, can_see_birth_date=vis.birth_date
    )
    form.is_valid()  # un filtre manipulat no filtra, com al llistat
    if "format" in form.errors:
        return HttpResponseBadRequest(_("Format d'exportació no vàlid."))
    data = form.cleaned_data
    content_type, extension, write = roster.FORMATS[data["format"]]
    columns = roster.export_columns(vis)
    members = roster.filtered_members(
        data, can_search_document=vis.identity, can_see_birth_date=vis.birth_date
    )
    rows = [roster.export_row(member, columns) for member in members]
    response = HttpResponse(write([label for _key, label in columns], rows), content_type)
    response["Content-Disposition"] = (
        f'attachment; filename="socis-{local_today():%Y-%m-%d}.{extension}"'
    )
    audit.record(
        audit.Action.MEMBERS_EXPORTED,
        actor=request.user,
        details={
            "filters": {
                "type": data.get("tipus") or "",
                "status": data.get("estat") or "",
                "search": bool((data.get("q") or "").strip()),
                "without_birth_date": bool(data.get("sense_data")),
                "exempt_unchecked_birth_date": bool(data.get("sense_comprovar")),
            },
            "rows": len(rows),
            "format": data["format"],
        },
        request=request,
    )
    return response


# --- Altes pendents: aprovar i rebutjar (T-M01-14; P3a, P3, C1, C2; CA-M01-03 a 05) -----------
# Consultar amb P3a; aprovar i rebutjar amb P3. El servei torna a comprovar el permís i el
# conflicte d'interès: amagar un botó no és cap control. La data de naixement només arriba a la
# plantilla amb C1, i els documents (sol·licitant i representant), només amb C2.

REQUESTS_VIEW = "members.requests.view"


def _pending_joins():
    return (
        MemberRequest.objects.filter(
            kind=MemberRequest.Kind.JOIN, status=MemberRequest.Status.PENDING
        )
        .select_related("person", "requested_type", "person__member", "person__member__type")
        .order_by("created_at", "id")
    )


@never_cache
@permission_required(REQUESTS_VIEW)
@require_GET
def join_requests_view(request):
    perms = request_permissions(request)
    can_resolve = has_perm(request.user, admissions.APPROVE_PERMISSION, permissions=perms)
    birth_date = has_perm(request.user, "members.field.birth_date", permissions=perms)
    identity = has_perm(request.user, "members.field.identity", permissions=perms)
    today = local_today()
    rows = []
    for join_request in _pending_joins():
        person = join_request.person
        rows.append(
            {
                "request": join_request,
                "person": person,
                "former": getattr(person, "member", None),
                "own": join_request.person_id == request.user.person_id,
                # Sense C2, una alta que demana comprovar el document no mostra cap casella
                # (075, CA-M01-86); el servei ho torna a comprovar.
                "blocker": admissions.approval_blocker(join_request)
                or admissions.document_blocker(join_request, identity),
                "identity_check": admissions.needs_identity_check(join_request),
                "guardian_check": admissions.needs_guardian_check(join_request),
                "new_contact": bool(
                    join_request.new_contact_email or join_request.new_contact_phone
                ),
                "matches": sorted({w.get("match") for w in join_request.duplicate_warning}),
                # 079 (A-15): persones amb el mateix nom, cognoms i data de naixement que un
                # menor sense document. Només el que cal per revisar-ho: si és soci i el número.
                "similar": [
                    getattr(other, "member", None)
                    for other in admissions.similar_minors(join_request)
                ],
                "birth_conflict": admissions.birth_date_conflict(join_request),
                "birth_date": join_request.birth_date if birth_date else None,
                # Sense C1, només la franja (CA-M01-45, RN-M01-48). `age_band` només llegeix
                # `birth_date`, que a l'alta és a la sol·licitud.
                "age_band": None if birth_date else persons.age_band(join_request, today),
                "document": roster.document_label(person) if identity else "",
                "guardian_document": (
                    f"{join_request.get_guardian_id_document_type_display()} "
                    f"{join_request.guardian_id_document_number}"
                    if identity and join_request.guardian_id_document_number
                    else ""
                ),
            }
        )
    context = {
        "rows": rows,
        "can_resolve": can_resolve,
        "show_birth_date": birth_date,
        "show_identity": identity,
    }
    return render(request, "members/join_requests.html", context)


def _back_to_requests():
    response = redirect("administration:join_requests")
    response.status_code = 303
    return response


def _resolve(request, pk, action):
    join_request = get_object_or_404(MemberRequest, pk=pk, kind=MemberRequest.Kind.JOIN)
    # T-M01-45 (1): l'error surt a dalt de la llista; diu de quina sol·licitud és amb el nom que
    # ja hi surt a la targeta (qui hi arriba té P3a i el veu igualment).
    failed = _("%(person)s: %(error)s")
    try:
        message = action(join_request)
    except OwnMemberChange as error:
        messages.error(request, failed % {"person": join_request.person, "error": error.args[0]})
    except ValidationError as error:
        text = " ".join(error.messages)
        messages.error(request, failed % {"person": join_request.person, "error": text})
    else:
        messages.success(request, message)
    return _back_to_requests()


@never_cache
@permission_required(admissions.APPROVE_PERMISSION)
@require_POST
def join_approve_view(request, pk):
    def approve(join_request):
        member = admissions.approve_join(
            join_request,
            by=request.user,
            identity_checked=request.POST.get("identitat_comprovada") == "1",
            guardian_checked=request.POST.get("representant_comprovat") == "1",
            update_contact=request.POST.get("actualitza_contacte") == "1",
            duplicates_reviewed=request.POST.get("duplicats_revisats") == "1",
            request=request,
        )
        if member.status == Member.Status.ACTIVE:
            text = _("Alta aprovada: %(person)s, soci número %(number)s, actiu i exempt per edat.")
        else:
            text = _(
                "Alta aprovada: %(person)s, soci número %(number)s, pendent fins que pagui "
                "la quota."
            )
        text = text % {"person": member.person, "number": member.member_number}
        # 079 (RN-M01-87): no es diu si ha estat una invitació o un avís a qui ja té compte.
        if member.access_mail_sent:
            return text + " " + _("Se li ha enviat el correu d'accés a l'àrea de socis.")
        return (
            text
            + " "
            + _("No se li ha enviat cap correu d'accés: és menor de 14 anys o no té correu propi.")
        )

    return _resolve(request, pk, approve)


@never_cache
@permission_required(admissions.APPROVE_PERMISSION)
@require_POST
def join_reject_view(request, pk):
    def reject(join_request):
        admissions.reject_join(
            join_request, by=request.user, reason=request.POST.get("motiu", ""), request=request
        )
        return _("Sol·licitud rebutjada. No s'ha creat cap soci.")

    return _resolve(request, pk, reject)


# --- Quotes i impagats (T-M01-18; P10 per veure-ho, P9 per marcar; RN-M01-09, 040) ----------
# La generació de quotes i els recordatoris no hi són: depenen de decisions obertes (fees.py).
# El servei torna a comprovar P9 i el conflicte d'interès, i en registra l'intent.


WITHOUT_ADDRESS_SHOWN = 20


@never_cache
@permission_required(fees.VIEW)
@require_GET
def fees_view(request):
    form = fees.FeeFilterForm(request.GET or None)
    data = form.cleaned_data if form.is_valid() else {}
    today = local_today()
    page = Paginator(fees.rows_for_review(data, today), PER_PAGE).get_page(
        request.GET.get("pagina")
    )
    to_review = []
    for fee in fees.payments_to_review():  # 079 (A-17, RN-M01-89)
        payments = charges.active_payments(fee.charge)
        to_review.append(
            {
                "fee": fee,
                "member": fee.member,
                "paid_at": max((p.paid_at for p in payments if p.paid_at), default=None),
                "amount": fees._euros(fee.charge.amount_cents),
                "own": fee.member.person_id == request.user.person_id,
            }
        )
    context = {
        "form": form,
        "page": page,
        "can_mark": has_perm(request.user, services.UNPAID_PERMISSION),
        "today": today,
        "to_review": to_review,
        "can_review": has_perm(request.user, fees.EDIT_PERMISSION, write=True),
        "can_list": has_perm(request.user, roster.LIST),
        # T-M01-49 (097, P-61 punt 2): només els candidats que surten en aquesta pàgina.
        "candidates": instalments.unpaid_candidates(today) & {m.pk for m, _fee in page},
    }
    if page.number == 1:  # T-M01-43d: només a la primera pàgina del llistat
        without_address = fees.renewal_notices_without_address(today)
        context["without_address"] = without_address[:WITHOUT_ADDRESS_SHOWN]
        context["without_address_more"] = len(without_address) - WITHOUT_ADDRESS_SHOWN
    return render(request, "members/fees.html", context)


@never_cache
@permission_required(fees.EDIT_PERMISSION, write=True)
@require_POST
def fee_payment_reviewed_view(request, pk):
    """079 (A-17, CA-M01-98): marca com a revisat el pagament d'un soci de baixa, amb una nota.
    P8 amb edició, a més de P10 per veure la pantalla; el servei ho torna a comprovar."""
    require_perm(request, fees.VIEW)
    fee = get_object_or_404(AnnualFee.objects.select_related("member__person"), pk=pk)
    try:
        fees.mark_payment_reviewed(
            fee, by=request.user, note=request.POST.get("nota", ""), request=request
        )
    except OwnMemberChange as error:
        messages.error(request, error.args[0])
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, _("Pagament marcat com a revisat."))
    response = redirect("administration:fees")
    response.status_code = 303
    return response


def _unpaid_action(request, pk, service, done):
    member = get_object_or_404(Member.objects.select_related("person"), pk=pk)
    try:
        service(
            member,
            by=request.user,
            effective_on=fees.parse_date(request.POST.get("data")),
            reason=request.POST.get("motiu", ""),
            request=request,
        )
    except OwnMemberChange as error:
        messages.error(request, error.args[0])
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, done % {"person": member.person})
    response = redirect("administration:fees")
    response.status_code = 303
    return response


@never_cache
@permission_required(services.UNPAID_PERMISSION)
@require_POST
def fee_mark_unpaid_view(request, pk):
    return _unpaid_action(
        request, pk, services.mark_unpaid, _("%(person)s queda marcat com a impagat.")
    )


@never_cache
@permission_required(services.UNPAID_PERMISSION)
@require_POST
def fee_unmark_unpaid_view(request, pk):
    return _unpaid_action(
        request, pk, services.unmark_unpaid, _("%(person)s ja no és impagat: torna a ser actiu.")
    )
