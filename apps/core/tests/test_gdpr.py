"""Sol·licituds d'esborrat RGPD a la 00 (T-M01-22; spec 00, HU-19; P-M01-F, passos 4 i 5; decisió
028): la pantalla `/gestio/rgpd/` amb M11, el conflicte d'interès, la reautenticació, el rebuig,
i l'excepció acotada dels disparadors del registre d'activitat (RN-51, RN-89). L'esborrat d'una
sòcia de principi a fi és a `apps/members/tests/test_privacy.py`. Només dades inventades.
"""

import pyotp
import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection, transaction
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from apps.accounts import totp
from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL, WRONG_CODE, WRONG_PASSWORD
from apps.core import audit, charges, erasure, files, mail, privacy
from apps.core.models import (
    AppendOnlyError,
    AuditEntry,
    Charge,
    Department,
    ErasureRequest,
    OutgoingEmail,
    Person,
    PrivateFile,
    Role,
)
from apps.core.permissions import has_perm
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

LIST, DETAIL = "administration:gdpr_requests", "administration:gdpr_request_detail"
ROLES = [code for code in Role.Code.values if code not in ("member", "visitor", "guest")]
S = ErasureRequest.Status
REASON = "Motiu inventat de proves"


@pytest.fixture
def pending(personal_account):
    """La sol·licitud pendent d'Anna Puig (compte personal `anna@example.org`)."""
    person = personal_account.person
    person.contact_email, person.phone = "anna@example.org", "+34600000001"
    person.save()
    request, _created = erasure.request_erasure(person, by=personal_account)
    return request


@pytest.fixture
def handler(make_admin):
    account = make_admin("administrator")
    account.set_password(PASSWORD)
    account.save()
    return account


def code_for(account):
    return pyotp.TOTP(totp.secret_of(account.totp_device)).now()


def approval(account, **extra):
    data = {"action": "approve", "confirm": "on", "password": PASSWORD, "code": code_for(account)}
    return {**data, **extra}


def detail(request):
    return reverse(DETAIL, args=[request.pk])


# --- Permisos per rol (M11) -----------------------------------------------------------------


@pytest.mark.parametrize("role", ROLES)
def test_gdpr_screens_need_m11_for_every_role(make_admin, login_as, pending, role):
    """Cada rol de la configuració inicial × les dues pantalles i els dos POST: amb M11, hi
    entra; sense, «no trobat» i res no canvia. El que s'espera surt de la matriu carregada."""
    account = make_admin(role)
    client = login_as(account, AREA_ADMIN)
    allowed = has_perm(account, erasure.HANDLE_PERMISSION)
    for url in (reverse(LIST), detail(pending)):
        assert client.get(url).status_code == (200 if allowed else 404), url
    for data in ({"action": "reject", "reason": REASON}, {"action": "approve"}):
        response = client.post(detail(pending), data)
        if not allowed:
            assert response.status_code == 404
            pending.refresh_from_db()
            assert pending.status == S.PENDING
    assert (reverse(LIST) in client.get(reverse("administration:home")).content.decode()) == (
        allowed
    )


def test_only_the_administrator_has_m11_in_the_initial_matrix(make_admin):
    assert [r for r in ROLES if has_perm(make_admin(r), erasure.HANDLE_PERMISSION)] == [
        "administrator"
    ]


def test_personal_account_does_not_enter(login_as, personal_account, pending):
    client = login_as(personal_account, AREA_PERSONAL)
    for url in (reverse(LIST), detail(pending)):
        response = client.get(url)
        assert response.status_code == 302
        assert response["Location"].startswith(reverse("administration:login"))


def test_services_check_the_permission_too(make_admin, pending):
    """El permís també fora de la vista: sense M11, «no trobat» i res no canvia."""
    secretary = make_admin("secretary")
    with pytest.raises(Http404):
        erasure.approve(pending, by=secretary)
    with pytest.raises(Http404):
        erasure.reject(pending, by=secretary, reason=REASON)
    pending.refresh_from_db()
    assert pending.status == S.PENDING


def test_disabled_handler_cannot_resolve(handler, pending):
    handler.status = Account.Status.DISABLED
    handler.save()
    with pytest.raises(Http404):
        erasure.approve(pending, by=handler)


# --- Pantalles ------------------------------------------------------------------------------


def test_list_shows_pending_and_resolved_without_contact_data(login_as, handler, pending):
    page = login_as(handler, AREA_ADMIN).get(reverse(LIST)).content.decode()
    assert "Anna Puig" in page and detail(pending) in page
    assert "anna@example.org" not in page and "600000001" not in page


def test_detail_shows_what_will_happen_and_no_other_personal_data(login_as, handler, pending):
    page = login_as(handler, AREA_ADMIN).get(detail(pending)).content.decode()
    assert "Anna Puig" in page
    assert "Aprova i executa" in page and "Rebutja" in page
    assert "600000001" not in page  # ni telèfon, ni document, ni adreça


# --- Conflicte d'interès --------------------------------------------------------------------


def test_nobody_resolves_their_own_request(login_as, make_admin, personal_account, pending):
    """Ningú no aprova ni rebutja la seva pròpia sol·licitud: 403 abans de demanar cap
    credencial, res no canvia i l'intent queda al registre."""
    own = make_admin("administrator", person=personal_account.person)
    own.set_password(PASSWORD)
    own.save()
    client = login_as(own, AREA_ADMIN)
    page = client.get(detail(pending)).content.decode()
    assert "És la teva sol·licitud" in page and 'value="approve"' not in page
    for data in (approval(own), {"action": "reject", "reason": REASON}):
        response = client.post(detail(pending), data)
        assert response.status_code == 403
    pending.refresh_from_db()
    assert pending.status == S.PENDING
    assert Person.objects.get(pk=pending.person_id).status == Person.Status.ACTIVE
    attempts = AuditEntry.objects.filter(action=audit.Action.ERASURE_OWN_REJECTED)
    assert attempts.count() == 2
    assert attempts.first().actor_account == own
    with pytest.raises(erasure.OwnErasureRequest):
        erasure.approve(pending, by=own)


# --- Aprovar: confirmació i reautenticació --------------------------------------------------


def test_approving_needs_the_confirmation_box(login_as, handler, pending):
    client = login_as(handler, AREA_ADMIN)
    response = client.post(detail(pending), {**approval(handler), "confirm": ""})
    assert response.status_code == 200
    assert response.context["approve_form"].errors["confirm"]
    pending.refresh_from_db()
    assert pending.status == S.PENDING


@pytest.mark.parametrize(
    ("change", "field", "message"),
    [
        ({"password": "no-es-aquesta"}, "password", WRONG_PASSWORD),
        ({"password": ""}, "password", WRONG_PASSWORD),
        ({"code": "000000"}, "code", WRONG_CODE),
        ({"code": ""}, "code", WRONG_CODE),
    ],
)
def test_approving_asks_for_password_and_code_again(
    login_as, handler, pending, change, field, message
):
    """Reautenticació a la mateixa petició (`minutes=0`): amb la contrasenya o el codi
    incorrectes no s'executa res, l'error surt al costat del camp i l'intent compta per a V-01."""
    client = login_as(handler, AREA_ADMIN)  # acaba d'entrar: no hi ha cap finestra de gràcia
    response = client.post(detail(pending), approval(handler, **change))
    assert response.status_code == 200
    assert response.context["approve_form"].errors[field] == [str(message)]
    assert escape(str(message)) in response.content.decode()
    pending.refresh_from_db()
    assert pending.status == S.PENDING
    assert Person.objects.get(pk=pending.person_id).status == Person.Status.ACTIVE
    handler.refresh_from_db()
    assert handler.failed_login_count == 1


def test_ca_19_1_approving_executes_the_erasure(login_as, handler, personal_account, pending):
    """CA-19.1 i CA-19.2: en aprovar, els comptes queden desactivats, la persona anonimitzada, i
    la pantalla només ensenya la referència anònima."""
    client = login_as(handler, AREA_ADMIN)
    response = client.post(detail(pending), approval(handler))
    assert response.status_code == 302 and response["Location"] == detail(pending)
    pending.refresh_from_db()
    assert pending.status == S.EXECUTED
    assert pending.resolved_by == handler and pending.executed_at is not None
    person = Person.objects.get(pk=pending.person_id)
    assert person.status == Person.Status.ANONYMISED
    assert person.contact_email == "" and person.phone == ""
    personal_account.refresh_from_db()
    assert personal_account.status == Account.Status.DISABLED
    assert not personal_account.has_usable_password()
    for url in (detail(pending), reverse(LIST)):
        page = client.get(url).content.decode()
        assert person.anonymous_ref in page
        assert "Anna" not in page and "anna@example.org" not in page
    actions = list(
        AuditEntry.objects.filter(target_type="core.erasurerequest")
        .order_by("id")
        .values_list("action", flat=True)
    )
    assert actions == [
        audit.Action.ERASURE_REQUESTED,
        audit.Action.ERASURE_APPROVED,
        audit.Action.ERASURE_EXECUTED,
    ]
    # No es pot tornar a resoldre.
    response = client.post(detail(pending), {"action": "reject", "reason": REASON})
    assert response.status_code == 200
    pending.refresh_from_db()
    assert pending.status == S.EXECUTED


def test_ca_19_1_open_session_of_the_person_is_closed(login_as, handler, personal_account, pending):
    """CA-19.1: la sessió que la persona tenia oberta deixa de valer."""
    session = login_as(personal_account, AREA_PERSONAL)
    assert session.get(reverse("core:home")).status_code == 200
    erasure.approve(pending, by=handler)
    response = session.get(reverse("core:home"))
    # Sessió tancada: «La sessió ha caducat» amb el botó cap a l'entrada (081, punt 22).
    assert response.status_code == 401
    assert f'href="{reverse("accounts:login")}?next=' in response.content.decode()


# --- Rebutjar -------------------------------------------------------------------------------


def test_rejecting_needs_a_reason(login_as, handler, pending):
    client = login_as(handler, AREA_ADMIN)
    response = client.post(detail(pending), {"action": "reject", "reason": "  "})
    assert response.status_code == 200
    assert response.context["reject_form"].errors["reason"]
    pending.refresh_from_db()
    assert pending.status == S.PENDING
    with pytest.raises(erasure.ErasureNotAllowed):
        erasure.reject(pending, by=handler, reason=" ")


def test_rejecting_keeps_the_person_and_sends_an_email_without_the_reason(
    login_as, handler, personal_account, pending
):
    client = login_as(handler, AREA_ADMIN)
    response = client.post(detail(pending), {"action": "reject", "reason": REASON})
    assert response.status_code == 302
    pending.refresh_from_db()
    assert (pending.status, pending.rejection_reason) == (S.REJECTED, REASON)
    assert pending.resolved_by == handler and pending.executed_at is None
    assert Person.objects.get(pk=pending.person_id).status == Person.Status.ACTIVE
    personal_account.refresh_from_db()
    assert personal_account.status == Account.Status.ACTIVE
    email = OutgoingEmail.objects.get(template=erasure.REJECTED_EMAIL)
    assert email.to_address == "anna@example.org"
    assert REASON not in email.body_text and "Anna" not in email.body_text
    entry = AuditEntry.objects.get(action=audit.Action.ERASURE_REJECTED)
    assert (entry.old_value, entry.new_value, entry.reason) == ("pending", "rejected", REASON)
    # Pot tornar-la a demanar: només n'hi pot haver una de pendent.
    again, created = erasure.request_erasure(pending.person, by=personal_account)
    assert created and again.pk != pending.pk


def test_unknown_action_is_not_found(login_as, handler, pending):
    client = login_as(handler, AREA_ADMIN)
    assert client.post(detail(pending), {"action": "delete"}).status_code == 404
    assert client.get(reverse(DETAIL, args=[999_999])).status_code == 404


# --- El que no s'executa --------------------------------------------------------------------


def test_ca_19_7_open_charges_block_the_approval_and_nothing_is_touched(login_as, handler, pending):
    """CA-19.7 (pendent de Q-14): amb un càrrec pendent, la pantalla ho diu, no deixa aprovar i
    el servei tampoc; el càrrec no es toca. Es pot rebutjar igualment."""
    department = Department.objects.get(name=Department.GENERAL)
    charge = charges.create_charge(
        pending.person,
        kind=Charge.Kind.FEE,
        amount_cents=9000,
        concept="Quota de soci 2026",
        department=department,
        origin="members",
        by=handler,
    )
    client = login_as(handler, AREA_ADMIN)
    page = client.get(detail(pending)).content.decode()
    assert "Ara no es pot aprovar" in page and 'value="approve"' not in page
    assert "9000" not in page and "90,00" not in page  # cap import a la pantalla
    response = client.post(detail(pending), approval(handler))
    assert response.status_code == 200
    with pytest.raises(erasure.ErasureNotAllowed):
        erasure.approve(pending, by=handler)
    pending.refresh_from_db()
    charge.refresh_from_db()
    assert pending.status == S.PENDING and charge.status == Charge.Status.PENDING
    assert Person.objects.get(pk=pending.person_id).status == Person.Status.ACTIVE
    handler.refresh_from_db()
    assert handler.failed_login_count == 0  # no s'ha arribat a demanar cap credencial


def test_last_operational_administrator_is_not_erased(handler, make_admin):
    """RN-RP-13: l'esborrat no pot deixar la plataforma sense cap administrador operatiu."""
    person = Person.objects.create(first_name="Unic", last_name="Admin", origin="in_person")
    only = make_admin("administrator", person=person)
    personal = Account.objects.create_personal(person, "unic@example.org", PASSWORD)
    request, _created = erasure.request_erasure(person, by=personal)
    # `handler` deixa de ser operatiu: només queda el compte de qui demana l'esborrat.
    handler.totp_device.delete()
    approver = make_admin("administrator", totp=False)
    assert erasure.blockers(person)
    with pytest.raises(ValidationError):
        erasure.approve(request, by=approver)
    only.refresh_from_db()
    assert only.status == Account.Status.ACTIVE
    assert Person.objects.get(pk=person.pk).status == Person.Status.ACTIVE


# --- Peces de la 00 -------------------------------------------------------------------------


def test_sent_emails_lose_the_address_and_queued_ones_when_they_go_out(personal_account, handler):
    person = personal_account.person
    sent = mail.queue_email("prova", to="anna@example.org", person=person)
    mail.deliver(sent.pk)
    loose = mail.queue_email("prova", to="anna@example.org")  # sense persona (p. ex. un rebut)
    mail.deliver(loose.pk)
    queued = mail.queue_email("prova", to="anna@example.org", person=person)
    other = mail.queue_email("prova", to="altra@example.org")
    mail.deliver(other.pk)
    request, _created = erasure.request_erasure(person, by=personal_account)
    erasure.approve(request, by=handler)

    replacement = f"{Person.objects.get(pk=person.pk).anonymous_ref.lower()}@anonimitzat.invalid"
    for email in (sent, loose, queued, other):
        email.refresh_from_db()
    assert sent.to_address == loose.to_address == replacement
    assert queued.to_address == "anna@example.org" and queued.status == "queued"
    assert other.to_address == "altra@example.org"
    mail.deliver(queued.pk)
    queued.refresh_from_db()
    assert (queued.status, queued.to_address) == ("sent", replacement)


def test_rn_b8_export_files_of_the_person_are_deleted(
    personal_account, handler, django_capture_on_commit_callbacks
):
    """RN-B8: en un esborrat, els fitxers sense obligació legal s'esborren."""
    person = personal_account.person
    export = privacy.request_export(person, by=personal_account)
    request, _created = erasure.request_erasure(person, by=personal_account)
    with django_capture_on_commit_callbacks(execute=True):
        erasure.approve(request, by=handler)
    export.refresh_from_db()
    assert export.deleted_at is not None
    assert not files.can_access(handler, export)
    assert not PrivateFile.objects.filter(owner=person, deleted_at__isnull=True).exists()


def test_export_file_is_kept_if_the_erasure_is_undone(personal_account, handler, monkeypatch):
    person = personal_account.person
    export = privacy.request_export(person, by=personal_account)
    request, _created = erasure.request_erasure(person, by=personal_account)

    def boom(*args, **kwargs):
        raise RuntimeError("falla a propòsit")

    monkeypatch.setattr(audit, "substitute_identity", boom)
    with pytest.raises(RuntimeError):
        erasure.approve(request, by=handler)
    export.refresh_from_db()
    assert export.deleted_at is None and export.expires_at > timezone.now()
    assert files.can_access(personal_account, export)


# --- L'excepció del disparador del registre d'activitat (core/0019; RN-51, RN-89) ------------


class TestAuditTrigger:
    """L'excepció és a la base de dades. Ni amb el paràmetre posat es pot canviar res que no
    sigui: el valor anterior, el valor nou o el motiu per la referència anònima d'una persona ja
    anonimitzada, i l'adreça IP per res."""

    @pytest.fixture
    def entry(self, personal_account):
        return audit.record(
            "persons.updated",
            actor=personal_account,
            target=personal_account.person,
            field="phone",
            old="600000001",
            new="600000002",
            reason="text lliure",
        )

    @pytest.fixture
    def ref(self, personal_account, handler, entry):
        request, _created = erasure.request_erasure(personal_account.person, by=personal_account)
        erasure.approve(request, by=handler)
        return Person.objects.get(pk=personal_account.person_id).anonymous_ref

    def _run(self, sql, params, *, setting="on"):
        with transaction.atomic(), connection.cursor() as cursor:
            if setting:
                cursor.execute("SELECT set_config('cris.rgpd_anonymise', %s, true)", [setting])
            cursor.execute(sql, params)

    def test_ca_19_4_the_service_substitutes_values_reason_and_ip(self, entry, ref):
        """CA-19.4: el servei deixa la referència on hi havia valors i motiu, i res més canvia."""
        after = AuditEntry.objects.get(pk=entry.pk)
        assert (after.old_value, after.new_value, after.reason) == (ref, ref, ref)
        assert (after.action, after.created_at, after.target_id, after.field) == (
            entry.action,
            entry.created_at,
            entry.target_id,
            entry.field,
        )
        assert after.actor_account_id == entry.actor_account_id

    def test_without_the_setting_nothing_can_be_updated(self, entry, ref):
        for setting in (None, "off", "true"):
            with pytest.raises(DatabaseError, match="no es pot modificar ni esborrar"):
                self._run(
                    "UPDATE core_auditentry SET reason = %s WHERE id = %s",
                    [ref, entry.pk],
                    setting=setting,
                )

    @pytest.mark.parametrize(
        "change",
        [
            "reason = 'un altre text'",
            "old_value = '\"un altre valor\"'",
            "new_value = 'null'",
            "new_value = NULL",
            "reason = 'A-999999'",
            "ip_address = '203.0.113.9'",
            "reason = %(ref)s, action = 'x'",
            "reason = %(ref)s, field = 'x'",
            "reason = %(ref)s, target_id = '1'",
            "reason = %(ref)s, target_type = 'x'",
            "reason = %(ref)s, created_at = now()",
            "reason = %(ref)s, details = '{\"a\": 1}'",
            "reason = %(ref)s, actor_roles = '[\"x\"]'",
            "reason = %(ref)s, actor_origin = 'x'",
            "reason = %(ref)s, actor_person_id = NULL",
        ],
    )
    def test_with_the_setting_only_the_substitution_is_accepted(self, entry, ref, change):
        sql = f"UPDATE core_auditentry SET {change} WHERE id = %(id)s"  # noqa: S608 (text fix)
        with pytest.raises(DatabaseError, match="no es pot modificar ni esborrar"):
            self._run(sql, {"id": entry.pk, "ref": ref})

    def test_with_the_setting_delete_is_still_rejected(self, entry, ref):
        with pytest.raises(DatabaseError, match="no es pot modificar ni esborrar"):
            self._run("DELETE FROM core_auditentry WHERE id = %s", [entry.pk])

    def test_truncate_is_always_rejected(self, entry, ref):
        with pytest.raises(DatabaseError, match="TRUNCATE"):
            self._run("TRUNCATE core_auditentry", None)

    def test_reference_of_a_person_who_is_not_anonymised_is_rejected(self, entry, personal_account):
        with pytest.raises(DatabaseError, match="no es pot modificar ni esborrar"):
            self._run("UPDATE core_auditentry SET reason = %s WHERE id = %s", ["A-0001", entry.pk])
        with pytest.raises(ValueError, match="anonimitzada"):
            audit.substitute_identity(personal_account.person, {}, up_to=entry.pk)

    def test_the_model_still_refuses_updates(self, entry, ref):
        with pytest.raises(AppendOnlyError):
            AuditEntry.objects.filter(pk=entry.pk).update(reason=ref)

    def test_other_peoples_values_are_not_touched_when_the_person_was_the_actor(
        self, personal_account, handler
    ):
        """On la persona és l'actor d'una acció sobre un objecte d'algú altre, els valors no es
        toquen (poden ser dades d'un altre); només se'n buida l'adreça IP."""
        other = Person.objects.create(first_name="Altra", last_name="Persona", origin="web")
        entry = audit.record(
            "persons.updated",
            actor=personal_account,
            target=other,
            field="phone",
            old="611111111",
            new="622222222",
        )
        request, _created = erasure.request_erasure(personal_account.person, by=personal_account)
        erasure.approve(request, by=handler)
        after = AuditEntry.objects.get(pk=entry.pk)
        assert (after.old_value, after.new_value) == ("611111111", "622222222")
        assert after.actor_person.status == Person.Status.ANONYMISED
