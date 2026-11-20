"""RGPD del M01: exportació i anonimització (T-M01-22; contracte M01-8; P-M01-F; decisió 028;
CA-M01-18, CA-M01-19 i CA-M01-39).

Els crida la 00 (`apps.core.privacy`), on aquest mòdul es registra en carregar-se (`apps.py`).
L'anonimització rep `by`, el compte que aprova l'esborrat: tot canvi d'estat té autor
(RN-M01-08).

**Exportació** (`export_personal_data`): soci, historial, correccions de la data d'alta, quotes
amb els pagaments, carnets, llicències i sol·licituds amb les seves acceptacions. Cada camp es
tria un per un. No hi surten:
- cap testimoni ni empremta (`MemberCard.token_hash`) ni la llavor de l'avatar;
- dades d'altres persones: el pare, la mare o el tutor legal d'una alta, el compte que resol o
  registra, i les coincidències amb altres persones (`duplicate_warning`);
- el contacte nou d'una alta (`new_contact_*`): amb un document que ja existia, l'ha pogut
  escriure qualsevol;
- els textos lliures que no ha escrit la persona (motius de resolucions, de canvis d'estat, de
  revocacions i d'anul·lacions): poden parlar de tercers. La spec no en diu res: és una pregunta
  oberta a l'informe de la tasca. El motiu d'una sol·licitud feta per la web sí, perquè és seu.

**Anonimització** (`anonymise`), dins la transacció de la 00 i amb la persona ja anonimitzada:
- el soci que no és de baixa passa a «baixa» avui, amb un motiu fix, i el carnet es revoca;
- les sol·licituds pendents es cancel·len i una baixa programada es dona per aplicada;
- de totes les sol·licituds de la persona se'n buiden la data de naixement, el representant, el
  contacte nou i les coincidències, i els motius passen a ser la referència; la persona
  també desapareix de les coincidències de les sol·licituds d'altres;
- els motius anteriors de l'historial (`MemberStatusChange.reason`, amb l'excepció acotada del
  disparador de members/0018) i de les revocacions de carnets passen a ser la referència;
- l'identificador de Cluber es buida: és un identificador de la persona en un altre sistema.

**No es toca:** el número de soci, que queda reservat i lligat a la referència (039); el tipus i
les dates del soci; l'historial d'estats (només el motiu); les correccions de la data d'alta i
les acceptacions de l'alta (sense dades personals pròpies); els registres de llicència; i les
quotes, els recordatoris, els càrrecs i els pagaments, que queden **bloquejats** (028, punt 2).
"""

from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.core import audit

from . import cards, member_requests
from .models import AnnualFee, Member, MemberCard, MemberRequest, MemberStatusChange
from .services import _change_status

ERASURE_REASON = gettext_lazy("Esborrat de dades a petició de la persona (RGPD).")
K, RS = MemberRequest.Kind, MemberRequest.Status


def _member(person) -> Member | None:
    return Member.objects.select_related("type").filter(person=person).first()


# --- Exportació (CA-M01-18, CA-M01-39) ------------------------------------------------------


def _member_data(member) -> dict:
    return {
        "numero_de_soci": member.member_number,
        "tipus": member.type.name,
        "estat": member.get_status_display(),
        "data_d_alta": member.joined_on,
        "data_d_alta_aproximada": member.joined_on_is_approximate,
        "data_de_baixa": member.left_on,
        "identificador_de_cluber": member.cluber_id,
        "ultima_renovacio_a_cluber": member.cluber_renewed_on,
    }


def _history(member) -> list[dict]:
    changes = member.status_changes.select_related("from_type", "to_type").order_by(
        "created_at", "id"
    )
    return [
        {
            "estat_anterior": change.get_from_status_display(),
            "estat_nou": change.get_to_status_display(),
            "tipus_anterior": change.from_type.name if change.from_type else None,
            "tipus_nou": change.to_type.name,
            "data_efectiva": change.effective_on,
            "data": change.created_at,
        }
        for change in changes
    ]


def _fees(member) -> list[dict]:
    fees = (
        AnnualFee.objects.filter(member=member)
        .select_related("charge")
        .prefetch_related("charge__payments")
        .order_by("period", "sequence", "id")
    )
    return [
        {
            "periode": fee.period,
            "tipus": fee.get_kind_display(),
            "concepte": fee.charge.concept,
            "import_centims": fee.charge.amount_cents,
            "moneda": fee.charge.currency,
            "estat": fee.charge.get_status_display(),
            "venciment": fee.due_on,
            "pagaments": [
                {
                    "metode": payment.get_method_display(),
                    "import_centims": payment.amount_cents,
                    "data": payment.paid_at,
                }
                for payment in fee.charge.payments.all()
            ],
        }
        for fee in fees
    ]


def _requests(person) -> list[dict]:
    requests = (
        person.member_requests.select_related("requested_type")
        .prefetch_related("acceptances__legal_text")
        .order_by("created_at", "id")
    )
    return [
        {
            "tipus": item.get_kind_display(),
            "canal": item.get_channel_display(),
            "estat": item.get_status_display(),
            "tipus_demanat": item.requested_type.name if item.requested_type else None,
            "data": item.created_at,
            "resolta_el": item.resolved_at,
            "data_efectiva": item.effective_on,
            "data_de_naixement_declarada": item.birth_date,
            # Només el motiu que ha escrit la mateixa persona (sol·licitud feta per la web).
            "motiu": item.request_reason if item.channel == MemberRequest.Channel.WEB else "",
            "acceptacions": [
                {
                    "text": acceptance.legal_text.kind,
                    "versio": acceptance.legal_text.version,
                    "qui_accepta": acceptance.get_accepted_by_display(),
                    "data": acceptance.created_at,
                }
                for acceptance in item.acceptances.all()
            ],
        }
        for item in requests
    ]


def export_personal_data(person) -> dict:
    """Diccionari per a l'exportació RGPD (M01-8). Només dades de la persona."""
    member = _member(person)
    data = {
        "soci": None,
        "historial": [],
        "correccions_de_la_data_d_alta": [],
        "quotes": [],
        "carnets": [],
        "llicencies": [],
        "sollicituds": _requests(person),
    }
    if member is None:
        return data
    data["soci"] = _member_data(member)
    data["historial"] = _history(member)
    data["correccions_de_la_data_d_alta"] = [
        {
            "data_anterior": change.from_joined_on,
            "data_nova": change.to_joined_on,
            "data": change.created_at,
        }
        for change in member.join_date_changes.order_by("created_at", "id")
    ]
    data["quotes"] = _fees(member)
    data["carnets"] = [
        {"emes_el": card.issued_at, "revocat_el": card.revoked_at}
        for card in member.cards.order_by("issued_at", "id")
    ]
    data["llicencies"] = [
        {
            "tipus": record.licence_type,
            "data_d_alta": record.issued_on,
            "caducitat": record.expires_on,
            "caducitat_declarada_per_tu": record.expiry_declared,
            "origen": record.get_source_display(),
        }
        for record in member.licence_records.order_by("issued_on", "id")
    ]
    return data


# --- Notes de l'administració (T-M01-22c; 085, A-1) -----------------------------------------


def admin_notes(person) -> list[dict]:
    """Els textos lliures que ha escrit l'administració: motius de resolucions i de les
    sol·licituds que no ha escrit la persona, de canvis d'estat i de revocacions de carnets. No
    van a l'exportació fins que els revisa qui atén la sol·licitud (`core.privacy`)."""
    from apps.core.privacy import note

    found = []
    for item in person.member_requests.order_by("created_at", "id"):
        kind = item.get_kind_display()
        if item.request_reason and item.channel != MemberRequest.Channel.WEB:
            found.append(
                note(
                    f"members.request.{item.pk}.request_reason",
                    _("Motiu de la sol·licitud (%(kind)s), registrat per l'administració")
                    % {"kind": kind},
                    item.created_at,
                    item.request_reason,
                )
            )
        if item.resolution_reason:
            found.append(
                note(
                    f"members.request.{item.pk}.resolution_reason",
                    _("Motiu de la resolució de la sol·licitud (%(kind)s)") % {"kind": kind},
                    item.resolved_at or item.created_at,
                    item.resolution_reason,
                )
            )
    member = _member(person)
    if member is None:
        return found
    for change in member.status_changes.exclude(reason="").order_by("created_at", "id"):
        found.append(
            note(
                f"members.status_change.{change.pk}",
                _("Canvi d'estat: %(old)s → %(new)s")
                % {
                    "old": change.get_from_status_display() or "—",
                    "new": change.get_to_status_display(),
                },
                change.created_at,
                change.reason,
            )
        )
    for card in member.cards.exclude(revoked_reason="").order_by("issued_at", "id"):
        found.append(
            note(
                f"members.card.{card.pk}",
                _("Revocació del carnet"),
                card.revoked_at,
                card.revoked_reason,
            )
        )
    return found


# --- Resum per a qui aprova l'esborrat ------------------------------------------------------


def describe(person) -> list[str]:
    member = _member(person)
    if member is None:
        return []
    number = member.member_number or _("sense número")
    if member.status == Member.Status.LEFT:
        return [
            _("És soci de baixa (número %(number)s). El número continua reservat.")
            % {"number": number}
        ]
    return [
        _(
            "És soci (número %(number)s, estat «%(status)s»): passarà a «baixa» avui i se li "
            "revocarà el carnet. El número queda reservat."
        )
        % {"number": number, "status": member.get_status_display()}
    ]


# --- Anonimització (CA-M01-19, CA-M01-39) ---------------------------------------------------


def _close_open_requests(person, *, by, request) -> None:
    pending = MemberRequest.objects.select_for_update().filter(person=person, status=RS.PENDING)
    for item in pending:
        member_requests._close(
            item, RS.CANCELLED, by=by, reason=str(ERASURE_REASON), request=request
        )
    # Una baixa programada: la baixa ja s'ha fet avui i la tasca diària no l'ha de tornar a
    # aplicar.
    MemberRequest.objects.filter(
        person=person, kind=K.LEAVE, status=RS.APPROVED, applied_at__isnull=True
    ).update(applied_at=timezone.now())


def _scrub_requests(person) -> None:
    ref = person.anonymous_ref
    own = MemberRequest.objects.filter(person=person)
    own.exclude(request_reason="").update(request_reason=ref)
    own.exclude(resolution_reason="").update(resolution_reason=ref)
    own.update(
        birth_date=None,
        new_contact_email="",
        new_contact_phone="",
        duplicate_warning=[],
        guardian_first_name="",
        guardian_last_name="",
        guardian_id_document_type="",
        guardian_id_document_number="",
        guardian_email="",
        guardian_phone="",
    )
    # Les sol·licituds d'altres persones que la tenien com a possible duplicat.
    mention = [{"person_id": person.pk}]
    for other in MemberRequest.objects.filter(duplicate_warning__contains=mention):
        other.duplicate_warning = [
            warning for warning in other.duplicate_warning if warning.get("person_id") != person.pk
        ]
        other.save(update_fields=["duplicate_warning"])


def anonymise(person, *, by, request=None) -> None:
    """Fa la part del M01 de l'esborrat d'una persona ja anonimitzada (vegeu el docstring del
    mòdul). Qui crida ja ha comprovat el permís i el conflicte d'interès i és dins d'una
    transacció: si res falla, es desfà tot."""
    if not person.anonymous_ref:
        raise ValueError("La persona encara no està anonimitzada.")
    ref = person.anonymous_ref
    member = _member(person)
    old_reasons, old_revocations = [], []
    if member is not None:
        # Els motius d'abans de l'esborrat (text lliure); els que escriu l'esborrat són fixos.
        old_reasons = list(member.status_changes.exclude(reason="").values_list("pk", flat=True))
        old_revocations = list(member.cards.exclude(revoked_reason="").values_list("pk", flat=True))
        if member.status != Member.Status.LEFT:
            _change_status(
                member,
                Member.Status.LEFT,
                by=by,
                effective_on=timezone.localdate(),
                reason=str(ERASURE_REASON),
                request=request,
            )
        cards.revoke_card(member, by=by, reason=str(ERASURE_REASON), request=request)
    _close_open_requests(person, by=by, request=request)
    _scrub_requests(person)
    if member is None:
        return
    with audit.identity_substitution():
        # Sense el gestor del model, que rebutja `update`: l'excepció la decideix el disparador.
        QuerySet(MemberStatusChange).filter(pk__in=old_reasons).update(reason=ref)
    MemberCard.objects.filter(pk__in=old_revocations).update(revoked_reason=ref)
    Member.objects.filter(pk=member.pk).update(
        cluber_id=None, cluber_renewed_on=None, updated_at=timezone.now()
    )


def audit_targets(person) -> dict[str, list[int]]:
    """Objectes no econòmics de la persona al M01: la 00 substitueix els valors de les seves
    entrades del registre d'activitat. Les quotes no hi són: queden bloquejades."""
    member = _member(person)
    targets = {
        "members.memberrequest": list(person.member_requests.values_list("pk", flat=True)),
    }
    if member is not None:
        targets["members.member"] = [member.pk]
        targets["members.membercard"] = list(member.cards.values_list("pk", flat=True))
        targets["members.licencerecord"] = list(member.licence_records.values_list("pk", flat=True))
    return targets
