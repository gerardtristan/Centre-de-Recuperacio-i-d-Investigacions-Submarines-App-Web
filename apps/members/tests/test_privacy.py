"""RGPD del M01, de principi a fi (T-M01-22; P-M01-F; decisió 028): exportació (CA-M01-18,
CA-M01-39, CA-18.1) i esborrat amb anonimització (CA-M01-19, CA-M01-39, CA-19.1 a CA-19.4).

La persona de les proves passa pels serveis de debò (alta, aprovació, pagament, carnet, perfil,
baixa rebutjada, impagat, llicència, consentiments, correus), de manera que el registre
d'activitat i les taules queden com quedarien en producció. Després de l'esborrat es recorren
TOTS els camps de text, de dates, JSON i d'adreces de TOTES les taules i es comprova que no hi
queda cap valor original. Només dades inventades.
"""

import datetime
import json
import re
from types import SimpleNamespace

import pytest
from django.apps import apps
from django.contrib.postgres.fields import ArrayField
from django.core import mail as django_mail
from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection, models, transaction
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from apps.accounts import invitations, totp
from apps.accounts.models import Account, AccountInvitation, FailedLogin, RecoveryCode
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.accounts.tests.test_personal_totp import with_totp
from apps.core import audit, consents, erasure, files, mail, persons, privacy
from apps.core.models import (
    AuditEntry,
    Charge,
    ErasureRequest,
    OutgoingEmail,
    Payment,
    Person,
    PrivateFile,
)
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import (
    admissions,
    cards,
    join,
    licences,
    member_edit,
    member_requests,
    roster,
    services,
)
from apps.members import privacy as members_privacy
from apps.members.demo_data import _Builder
from apps.members.join import PROVISIONAL_OPTIONAL_TEXTS
from apps.members.models import (
    AnnualFee,
    Member,
    MemberCard,
    MemberRequest,
    MembershipNumberCounter,
    MemberStatusChange,
)
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

# Valors inventats i prou estranys perquè no coincideixin amb cap altre text de la base.
FIRST, LAST = "Brunilda", "Xanguet Escórpora"
EMAIL = "brunilda.xanguet@example.org"
PHONE = "+34 600 987 654"
ADDRESS = "Carrer de la Gamba Vermella, 17"
DOCUMENT = "12345678Z"
BIRTH = datetime.date(1988, 4, 9)
IP = "203.0.113.77"  # TEST-NET-3: mai una adreça real
NEW_EMAIL, NEW_PHONE = "brunilda.nova@example.org", "+34 611 222 333"
HEX64 = re.compile(r"[0-9a-f]{64}")


@pytest.fixture
def staff(make_admin):  # noqa: F811
    """Un compte amb els rols que fan les operacions de preparació i un altre, administrador,
    que atén l'esborrat (M11)."""
    worker = make_admin("secretary", "treasurer", "president", "administrator")
    handler = make_admin("administrator")
    for kind in ("privacy", "membership_terms", "guardian_authorization"):
        consents.publish_text(kind, f"Text de prova: {kind}.", by=handler)
    for kind, content in PROVISIONAL_OPTIONAL_TEXTS.items():
        consents.publish_text(kind, content, by=handler)
    builder = _Builder(secretary=worker, treasurer=worker, admin=handler, password=PASSWORD)
    return SimpleNamespace(worker=worker, handler=handler, builder=builder)


def _request_from(ip):
    request = RequestFactory().post("/", REMOTE_ADDR=ip)
    return request


def _deliver_queued():
    for pk in OutgoingEmail.objects.filter(status="queued").values_list("pk", flat=True):
        mail.deliver(pk)


@pytest.fixture
def brunilda(staff, client):
    """Sòcia de ple dret amb tota la història: alta web amb rebut, aprovació amb invitació, quota
    pagada, carnet reemès, perfil editat per ella i per la secretaria, llicència, impagat marcat
    i desmarcat, baixa demanada i rebutjada, una alta repetida amb contacte nou, consentiments,
    un intent d'entrada fallit, una exportació i una sol·licitud d'esborrat rebutjada."""
    b, worker = staff.builder, staff.worker
    today = timezone.localdate()
    outcome = join.submit(
        {
            "first_name": FIRST,
            "last_name": LAST,
            "id_document_type": "dni",
            "id_document_number": DOCUMENT,
            "contact_email": EMAIL,
            "phone": PHONE,
            "address": ADDRESS,
            "birth_date": BIRTH,
            "membership_type": b.full,
            "accept_privacy": True,
            "accept_membership_terms": True,
            "accept_newsletter": True,
        },
        channel=MemberRequest.Channel.WEB,
        request=_request_from(IP),
    )
    person = outcome.request.person
    member = admissions.approve_join(outcome.request, by=worker)
    fee = member.fees.get()
    b.pay(fee)
    member.refresh_from_db()
    _deliver_queued()  # el rebut i la invitació ja han sortit: queden com a «enviats»

    account = b.personal(person)
    with_totp(account)
    persons.update_profile(
        person,
        actor=account,
        request=_request_from(IP),
        phone="+34 600 987 655",
        city="Pinedademar",
        postal_code="PM-08397",
        province="Maresmeprova",
        landline="938 765 432",
    )
    persons.update_profile(person, actor=account, request=_request_from(IP), phone=PHONE)
    member_edit.edit_member_data(member, by=worker, fields={"first_name": f"{FIRST} Maria"})
    member_edit.edit_member_data(member, by=worker, fields={"first_name": FIRST})
    member_edit.correct_join_date(
        member,
        by=worker,
        joined_on=today - datetime.timedelta(days=3),
        approximate=True,
        reason=f"Ho demana la {FIRST} {LAST} per escrit",
    )
    licences.add_record(
        member,
        by=worker,
        licence_type="FECDAS anual (prova)",
        issued_on=today,
        expires_on=today + datetime.timedelta(days=200),
    )
    services.mark_unpaid(
        member, by=worker, effective_on=today, reason=f"Rebut retornat de la {FIRST} {LAST}"
    )
    services.unmark_unpaid(
        member, by=worker, effective_on=today, reason=f"La {FIRST} ha pagat en efectiu"
    )
    token = cards.replace_card(member, by=worker, reason=f"La {FIRST} ha perdut el carnet")
    leave = member_requests.request_leave(
        member, by=account, reason=f"Soc la {FIRST} {LAST} i me'n vaig a viure fora"
    )
    member_requests.reject(leave, by=worker, reason=f"Parlat amb la {FIRST}: s'ho repensa")
    # Una alta repetida amb el mateix document i un contacte nou (Q-042), ja rebutjada.
    MemberRequest.objects.create(
        kind=MemberRequest.Kind.JOIN,
        person=person,
        requested_type=b.full,
        channel=MemberRequest.Channel.WEB,
        status=MemberRequest.Status.REJECTED,
        resolution_reason=f"La {FIRST} {LAST} ja és sòcia",
        birth_date=BIRTH,
        new_contact_email=NEW_EMAIL,
        new_contact_phone=NEW_PHONE,
        duplicate_warning=[{"match": "document", "person_id": person.pk}],
    )
    # Una altra persona amb una alta que la té com a possible duplicat.
    other = Person.objects.create(first_name="Zacaries", last_name="Verat", origin="web")
    other_request = MemberRequest.objects.create(
        kind=MemberRequest.Kind.JOIN,
        person=other,
        requested_type=b.supporter,
        channel=MemberRequest.Channel.WEB,
        duplicate_warning=[
            {"match": "email", "person_id": person.pk},
            {"match": "name_phone", "person_id": other.pk},
        ],
    )
    consents.grant(person, "images", channel="web", by=account, request=_request_from(IP))
    # Un intent d'entrada fallit des de la seva adreça.
    client.post(
        reverse("accounts:login"), {"login": EMAIL, "password": "no-es-aquesta"}, REMOTE_ADDR=IP
    )
    export = privacy.request_export(person, by=account, request=_request_from(IP))
    first_request, _created = erasure.request_erasure(person, by=account, request=_request_from(IP))
    erasure.reject(first_request, by=staff.handler, reason=f"La {FIRST} ho ha demanat per error")
    person.refresh_from_db()
    return SimpleNamespace(
        person=person,
        member=member,
        account=account,
        fee=fee,
        token=token,
        other_request=other_request,
        export=export,
        invitation=AccountInvitation.objects.filter(person=person).first(),
    )


def erase(subject, staff):
    request, _created = erasure.request_erasure(subject.person, by=subject.account)
    return erasure.approve(request, by=staff.handler)


def forbidden_values(person):
    """Els valors originals que no poden quedar enlloc, tal com es desen (normalitzats)."""
    return {
        "nom": FIRST,
        "cognoms": LAST,
        "cognom": "Xanguet",
        "correu": EMAIL,
        "correu (part local)": "brunilda.xanguet",
        "telèfon": person.phone,
        "telèfon (xifres)": "600987654",
        "telèfon fix": "938765432",
        "adreça": "Gamba Vermella",
        "codi postal": "PM-08397",
        "població": "Pinedademar",
        "província": "Maresmeprova",
        "document": DOCUMENT,
        "data de naixement": BIRTH.isoformat(),
        "adreça IP": IP,
        "contacte nou (correu)": NEW_EMAIL,
        "contacte nou (telèfon)": "611222333",
    }


_SCANNED = (
    models.CharField,
    models.TextField,
    models.JSONField,
    models.DateField,  # també DateTimeField
    models.GenericIPAddressField,
    ArrayField,
)


def leaks(forbidden) -> list[str]:
    """Recorre tots els camps de text, de dates, JSON i d'adreces de totes les taules i torna on
    surt algun dels valors prohibits."""
    found = []
    needles = {label: str(value).lower() for label, value in forbidden.items() if value}
    for model in apps.get_models(include_auto_created=True):
        fields = [f for f in model._meta.concrete_fields if isinstance(f, _SCANNED)]
        if not fields:
            continue
        names = [f.attname for f in fields]
        for row in model._base_manager.values_list("pk", *names):
            for field, value in zip(fields, row[1:], strict=True):
                if value is None or value == "":
                    continue
                text = json.dumps(value, default=str, ensure_ascii=False).lower()
                compact = re.sub(r"[\s-]", "", text)
                for label, needle in needles.items():
                    if needle in text or needle in compact:
                        found.append(f"{model._meta.label}.{field.name} #{row[0]}: {label}")
    return found


# --- Exportació -----------------------------------------------------------------------------


class TestExport:
    def test_ca_m01_18_export_has_all_the_data_of_the_member(self, brunilda):
        """CA-M01-18: persona, soci, historial, quotes, carnets, sol·licituds, consentiments i
        llicència."""
        data = privacy.export_person(brunilda.person)
        assert data["persona"]["nom"] == FIRST
        assert data["persona"]["numero_de_document"] == DOCUMENT
        assert data["persona"]["correu_de_contacte"] == EMAIL
        assert data["comptes"][0]["identificador_d_entrada"] == EMAIL
        own = data["socis"]
        assert own["soci"]["numero_de_soci"] == brunilda.member.member_number
        assert [h["estat_nou"] for h in own["historial"]] == [
            "Pendent",
            "Actiu",
            "Impagat",
            "Actiu",
        ]
        (fee,) = own["quotes"]
        assert fee["import_centims"] == brunilda.fee.charge.amount_cents
        assert fee["estat"] == "Pagat"
        assert len(fee["pagaments"]) == 1
        assert len(own["carnets"]) == 2  # el primer, revocat, i el reemès
        assert own["carnets"][0]["revocat_el"] is not None
        assert own["llicencies"][0]["tipus"] == "FECDAS anual (prova)"
        assert len(own["correccions_de_la_data_d_alta"]) == 1
        kinds = [item["tipus"] for item in own["sollicituds"]]
        assert kinds == ["Alta", "Baixa", "Alta"]
        assert own["sollicituds"][0]["acceptacions"]
        assert {c["text"] for c in data["consentiments"]} >= {"privacy", "images"}
        assert data["sollicituds_d_esborrat"][0]["estat"] == "Rebutjada"

    def test_ca_m01_39_export_carries_the_birth_date(self, brunilda):
        """CA-M01-39: l'exportació prèvia a l'esborrat porta la data de naixement."""
        data = privacy.export_person(brunilda.person)
        assert data["persona"]["data_de_naixement"] == BIRTH
        assert data["socis"]["sollicituds"][0]["data_de_naixement_declarada"] == BIRTH

    def test_ca_m01_18_export_has_no_token_hash_or_secret(self, brunilda):
        """CA-M01-18 i CA-18.1: cap testimoni, empremta ni secret."""
        content = files_content(brunilda.export)
        account = Account.objects.get(pk=brunilda.account.pk)
        secrets = [
            brunilda.token,
            *MemberCard.objects.values_list("token_hash", flat=True),
            *AccountInvitation.objects.values_list("token_hash", flat=True),
            *RecoveryCode.objects.values_list("code_hash", flat=True),
            brunilda.member.avatar_seed,
            account.password,
            account.totp_device.secret_encrypted,
            totp.secret_of(account.totp_device),
        ]
        assert all(secret for secret in secrets)
        for secret in secrets:
            assert secret not in content
        assert not HEX64.search(content)  # cap empremta SHA-256, sigui de què sigui
        for word in ("token", "hash", "password", "secret", "empremta"):
            assert word not in content.lower()

    def test_ca_m01_18_export_has_no_data_of_other_people(self, brunilda, staff):
        """CA-M01-18 i CA-18.1: només les seves dades. Ni qui ha resolt o registrat res, ni
        altres persones, ni els textos lliures que ha escrit l'administració."""
        other = staff.builder.paid_member(
            "Quimet", "Llobarro Déntol", "quimet@example.org", staff.builder.full
        )
        content = files_content(privacy.request_export(brunilda.person, by=brunilda.account))
        for account in (staff.worker, staff.handler):
            assert account.login not in content
            assert account.person.first_name not in content
        assert "Quimet" not in content and "Llobarro" not in content
        assert str(other.member_number) != str(brunilda.member.member_number)
        assert "Zacaries" not in content and "person_id" not in content
        for text in ("Rebut retornat", "ha perdut el carnet", "s'ho repensa", "ja és sòcia"):
            assert text not in content
        assert NEW_EMAIL not in content  # el contacte nou d'una alta l'ha pogut escriure qualsevol
        # El motiu que ha escrit ella mateixa (baixa demanada per la web) sí que hi és.
        assert "me'n vaig a viure fora" in content

    def test_ca_m01_18_export_of_a_minor_leaves_the_guardian_out(self, staff):
        """Les dades del pare, la mare o el tutor legal són d'una altra persona."""
        b = staff.builder
        request = b.submit("Pol", "Pop Prova", "", b.born(16, 2, 2), b.supporter, guardian=True)
        assert request.guardian_id_document_number
        content = json.dumps(privacy.export_person(request.person), default=str, ensure_ascii=False)
        for value in (
            request.guardian_first_name,
            request.guardian_id_document_number,
            request.guardian_email,
            request.guardian_phone,
        ):
            assert value not in content
        assert "Pop Prova" in content

    def test_ca_18_1_export_is_a_private_json_file_available_seven_days(self, brunilda):
        """CA-18.1 i V-08: JSON, propietat de la persona, caduca als 7 dies, i la sol·licitud
        queda al registre."""
        export = brunilda.export
        assert export.kind == PrivateFile.Kind.GDPR_EXPORT
        assert export.owner == brunilda.person
        assert export.content_type == "application/json"
        days = (export.expires_at - export.created_at).total_seconds() / 86400
        assert 6.99 < days < 7.01
        assert json.loads(files_content(export))["persona"]["cognoms"] == LAST
        entry = AuditEntry.objects.filter(action=audit.Action.EXPORT_REQUESTED).last()
        assert entry.actor_account == brunilda.account
        assert entry.target_id == str(brunilda.person.pk)

    def test_a_new_export_replaces_the_previous_one(
        self, brunilda, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            newer = privacy.request_export(brunilda.person, by=brunilda.account)
        old = PrivateFile.objects.get(pk=brunilda.export.pk)
        assert old.deleted_at is not None
        assert not files.can_access(brunilda.account, old)
        assert privacy.live_export(brunilda.person) == newer

    def test_ca_18_1_only_the_owner_downloads_it_from_the_profile(
        self, brunilda, staff, login_as, client
    ):
        """CA-18.1: el perfil ensenya l'enllaç del seu fitxer; un altre compte personal rep «no
        trobat» i la descàrrega queda al registre."""
        session = login_as(brunilda.account, AREA_PERSONAL)
        page = session.get(reverse("members:profile"))
        link = reverse("core:private_file", args=[brunilda.export.pk])
        assert link in page.content.decode()
        response = session.get(link)
        assert response.status_code == 302
        downloaded = b"".join(session.get(response["Location"]).streaming_content)
        assert json.loads(downloaded)["persona"]["nom"] == FIRST
        assert AuditEntry.objects.filter(
            action=audit.Action.FILE_URL_ISSUED, target_id=str(brunilda.export.pk)
        ).exists()

        other = staff.builder.paid_member(
            "Quimet", "Llobarro", "quimet@example.org", staff.builder.full
        )
        stranger = login_as(staff.builder.personal(other.person), AREA_PERSONAL)
        assert stranger.get(link).status_code == 404
        assert link not in stranger.get(reverse("members:profile")).content.decode()

    def test_ca_18_1_the_request_from_the_profile_prepares_the_file(self, staff, login_as):
        member = staff.builder.paid_member(
            "Quimet", "Llobarro", "quimet@example.org", staff.builder.full
        )
        account = staff.builder.personal(member.person)
        session = login_as(account, AREA_PERSONAL)
        assert privacy.live_export(member.person) is None
        assert session.get(reverse("members:export_data")).status_code == 405
        response = session.post(reverse("members:export_data"))
        assert response.status_code == 302 and response["Location"] == reverse("members:profile")
        export = privacy.live_export(member.person)
        assert export is not None and export.owner == member.person
        assert json.loads(files_content(export))["socis"]["soci"]["numero_de_soci"] == (
            member.member_number
        )


def files_content(file) -> str:
    from django.core.files.storage import storages

    with storages["private"].open(file.storage_key, "rb") as handle:
        return handle.read().decode("utf-8")


# --- Esborrat -------------------------------------------------------------------------------


class TestErasure:
    def test_ca_m01_19_member_left_cards_revoked_fees_blocked_number_reserved(
        self, brunilda, staff
    ):
        """CA-M01-19: el soci queda de baixa, la persona anonimitzada, els carnets revocats, les
        quotes bloquejades (ni esborrades ni modificades) i el número continua reservat."""
        number = brunilda.member.member_number
        money_before = _money_snapshot()
        counter = MembershipNumberCounter.objects.get().last_number
        resolved = erase(brunilda, staff)

        assert resolved.status == ErasureRequest.Status.EXECUTED
        assert resolved.resolved_by == staff.handler and resolved.executed_at is not None
        member = Member.objects.get(pk=brunilda.member.pk)
        assert member.status == Member.Status.LEFT
        assert member.left_on == timezone.localdate()
        last = member.status_changes.order_by("-id").first()
        assert (last.to_status, last.reason) == ("left", str(members_privacy.ERASURE_REASON))
        assert last.actor_account == staff.handler
        assert not member.cards.filter(revoked_at__isnull=True).exists()
        assert services.verify_card(brunilda.token) == services.INVALID_CARD
        # Quotes, càrrecs i pagaments: exactament com estaven, lligats a la persona anonimitzada.
        assert _money_snapshot() == money_before
        assert Charge.objects.filter(person=brunilda.person).count() == 1
        assert AnnualFee.objects.filter(member=member).count() == 1
        # El número no es reutilitza (039): continua al mateix soci i el comptador no recula.
        assert member.member_number == number
        assert MembershipNumberCounter.objects.get().last_number == counter
        newcomer = staff.builder.paid_member(
            "Quimet", "Llobarro", "quimet@example.org", staff.builder.full
        )
        assert newcomer.member_number not in (None, number)
        person = Person.objects.get(pk=brunilda.person.pk)
        assert person.status == Person.Status.ANONYMISED
        assert str(member) == f"{number} {person.anonymous_ref}"

    def test_ca_m01_39_birth_date_is_anonymised(self, brunilda, staff):
        """CA-M01-39 i RN-M01-49: la data de naixement s'anonimitza amb la resta."""
        erase(brunilda, staff)
        person = Person.objects.get(pk=brunilda.person.pk)
        assert person.birth_date is None
        assert not MemberRequest.objects.filter(person=person, birth_date__isnull=False).exists()

    def test_ca_19_1_accounts_disabled_sessions_closed_invitations_invalid(
        self,
        brunilda,
        staff,
        login_as,
        make_admin,  # noqa: F811
    ):
        """CA-19.1: tots els comptes desactivats (també el d'administrador), sessions tancades i
        invitacions invalidades (079, punt 10)."""
        admin = make_admin("secretary", person=brunilda.person, username="brunilda.x")
        session = login_as(brunilda.account, AREA_PERSONAL)
        assert session.get(reverse("members:profile")).status_code == 200
        pending = brunilda.invitation  # la de l'aprovació de l'alta, encara viva
        assert pending.used_at is None and pending.invalidated_at is None
        erase(brunilda, staff)

        ref = Person.objects.get(pk=brunilda.person.pk).anonymous_ref
        for account in Account.objects.filter(person=brunilda.person):
            assert account.status == Account.Status.DISABLED
            assert not account.has_usable_password()
            assert ref.lower() in account.login
            assert account.notification_email == ""
        assert Account.objects.get(pk=admin.pk).login == f"{ref.lower()}.admin"
        response = session.get(reverse("members:profile"))
        # Sessió tancada: «La sessió ha caducat» amb el botó cap a l'entrada (081, punt 22).
        assert response.status_code == 401
        assert f'href="{reverse("accounts:login")}?next=' in response.content.decode()
        pending.refresh_from_db()
        assert pending.invalidated_at is not None
        assert not FailedLogin.objects.filter(account__person=brunilda.person).exists()
        disabled = AuditEntry.objects.filter(action=audit.Action.ACCOUNT_DISABLED_BY_ERASURE)
        assert disabled.count() == 2

    def test_081_totp_and_recovery_codes_are_deleted(
        self,
        brunilda,
        staff,
        make_admin,  # noqa: F811
    ):
        """Decisió 081, punt 18: l'esborrat elimina el secret TOTP i els codis de recuperació de
        tots els comptes de la persona, i cap mecanisme d'accés no continua vigent (enllaç de
        recuperació de la contrasenya)."""
        from apps.accounts import tokens
        from apps.accounts.models import TotpDevice

        admin = make_admin("secretary", person=brunilda.person, username="brunilda.t")
        totp.regenerate_recovery_codes(admin)
        assert TotpDevice.objects.filter(account__person=brunilda.person).count() == 2
        assert RecoveryCode.objects.filter(account=admin).exists()
        reset_token = tokens.make_token(brunilda.account, tokens.RESET_PASSWORD)
        assert tokens.account_for_token(reset_token, tokens.RESET_PASSWORD) is not None
        erase(brunilda, staff)

        assert not TotpDevice.objects.filter(account__person=brunilda.person).exists()
        assert not RecoveryCode.objects.filter(account__person=brunilda.person).exists()
        assert tokens.account_for_token(reset_token, tokens.RESET_PASSWORD) is None
        entry = AuditEntry.objects.get(
            action=audit.Action.ACCOUNT_DISABLED_BY_ERASURE, target_id=str(admin.pk)
        )
        assert entry.details["second_factor_removed"] is True
        assert entry.details["backup_codes_removed"] >= 1
        personal = AuditEntry.objects.get(
            action=audit.Action.ACCOUNT_DISABLED_BY_ERASURE, target_id=str(brunilda.account.pk)
        )
        assert personal.details["second_factor_removed"] is True

    def test_ca_19_2_no_original_value_is_left_in_any_table(
        self, brunilda, staff, django_capture_on_commit_callbacks
    ):
        """CA-19.2 (i CA-19.6): després de l'esborrat, cap valor original (nom, cognoms, correu,
        telèfon, document, adreça, data de naixement, adreça IP, contacte nou) no queda en cap
        camp de cap taula; tampoc als registres econòmics, que no en porten cap de propi."""
        forbidden = forbidden_values(brunilda.person)
        before = leaks(forbidden)
        # La prova mateixa ha de veure les dades abans: si no, no demostraria res.
        for table in (
            "core.Person",
            "accounts.Account",
            "core.AuditEntry",
            "core.OutgoingEmail",
            "members.MemberRequest",
            "members.MemberStatusChange",
            "members.MemberCard",
            "core.ErasureRequest",
            "accounts.FailedLogin",
        ):
            assert any(leak.startswith(table + ".") for leak in before), table

        with django_capture_on_commit_callbacks(execute=True):
            erase(brunilda, staff)
        _deliver_queued()  # la cua envia el correu de confirmació (RN-A14)

        assert leaks(forbidden) == []
        person = Person.objects.get(pk=brunilda.person.pk)
        ref = person.anonymous_ref
        assert ref == f"A-{person.pk:04d}"
        assert (person.first_name, person.last_name) == (ref, "")
        assert person.preferred_language == "ca"
        # La persona també desapareix de les coincidències d'altres sol·licituds.
        brunilda.other_request.refresh_from_db()
        assert brunilda.other_request.duplicate_warning == [
            {"match": "name_phone", "person_id": brunilda.other_request.person_id}
        ]
        # El fitxer de l'exportació ja no hi és (RN-B8).
        export = PrivateFile.objects.get(pk=brunilda.export.pk)
        assert export.deleted_at is not None

    def test_ca_19_2_guardian_data_of_a_minor_is_anonymised(self, staff):
        """CA-19.2, 068: les dades del representant d'una alta s'anonimitzen amb la sol·licitud."""
        b = staff.builder
        request = b.submit(
            "Nil", "Sorell Verat", "nil.sorell@example.org", b.born(16), b.supporter, guardian=True
        )
        guardian = {
            "nom del representant": request.guardian_first_name,
            "document del representant": request.guardian_id_document_number,
            "correu del representant": request.guardian_email,
            "telèfon del representant": request.guardian_phone.replace(" ", ""),
            "cognoms": "Sorell Verat",
            "correu": "nil.sorell@example.org",
        }
        member = b.approve(request)
        b.pay(member.fees.get())
        account = b.personal(member.person)
        _deliver_queued()
        assert leaks(guardian)
        erase(SimpleNamespace(person=member.person, account=account), staff)
        _deliver_queued()
        assert leaks(guardian) == []

    def test_ca_19_3_economic_records_stay_untouched_and_without_personal_data(
        self, brunilda, staff
    ):
        """CA-19.3 (la part que no depèn de Q-14): càrrecs, pagaments i quotes no s'anonimitzen
        ni es destrueixen; queden lligats a la persona anonimitzada, i les seves entrades del
        registre conserven els valors."""
        charge = brunilda.fee.charge
        entries = list(
            AuditEntry.objects.filter(target_type="core.charge", target_id=str(charge.pk)).values(
                "id", "old_value", "new_value", "reason", "details"
            )
        )
        assert entries
        erase(brunilda, staff)
        charge.refresh_from_db()
        assert charge.status == Charge.Status.PAID
        assert charge.person.status == Person.Status.ANONYMISED
        assert Payment.objects.filter(charge=charge).count() == 1
        after = list(
            AuditEntry.objects.filter(target_type="core.charge", target_id=str(charge.pk)).values(
                "id", "old_value", "new_value", "reason", "details"
            )
        )
        assert after == entries

    def test_ca_19_4_audit_keeps_action_date_and_object_with_the_anonymous_reference(
        self, brunilda, staff
    ):
        """CA-19.4: cap entrada s'esborra ni canvia d'acció, data, objecte ni actor; el que
        identifica la persona se substitueix per la referència anònima."""
        fixed = ("id", "created_at", "action", "target_type", "target_id", "field")
        actor = ("actor_kind", "actor_account_id", "actor_person_id", "actor_roles", "details")
        before = list(AuditEntry.objects.order_by("id").values(*fixed, *actor))
        erase(brunilda, staff)
        last = before[-1]["id"]
        assert (
            list(AuditEntry.objects.filter(id__lte=last).order_by("id").values(*fixed, *actor))
            == before
        )
        ref = Person.objects.get(pk=brunilda.person.pk).anonymous_ref
        changes = AuditEntry.objects.filter(
            id__lte=last, action="persons.profile_updated", target_id=str(brunilda.person.pk)
        )
        assert changes.count() >= 2
        for entry in changes:
            assert (entry.old_value, entry.new_value) == (ref, ref)
            assert entry.ip_address is None
            assert entry.actor_person.anonymous_ref == ref
            assert str(entry.actor_person) == ref
        rejected = AuditEntry.objects.get(
            id__lte=last, action="members.request.resolved", field="status"
        )
        assert rejected.reason == ref
        assert rejected.actor_account == staff.worker  # qui ho va fer no canvia
        # Les entrades que escriu l'esborrat: estats i la referència, cap dada personal.
        executed = AuditEntry.objects.get(action=audit.Action.ERASURE_EXECUTED)
        assert executed.details == {"anonymous_ref": ref}
        assert executed.actor_account == staff.handler

    def test_all_or_nothing_if_a_step_fails(self, brunilda, staff, monkeypatch):
        """Tot o res: si falla l'últim pas, no queda ni la baixa, ni el correu, ni res."""
        before = _state(brunilda)
        request, _created = erasure.request_erasure(brunilda.person, by=brunilda.account)
        emails = OutgoingEmail.objects.count()
        entries = AuditEntry.objects.count()

        def boom(*args, **kwargs):
            raise RuntimeError("falla a propòsit")

        monkeypatch.setattr(audit, "substitute_identity", boom)
        with pytest.raises(RuntimeError):
            erasure.approve(request, by=staff.handler)

        assert _state(brunilda) == before
        request.refresh_from_db()
        assert request.status == ErasureRequest.Status.PENDING
        assert request.resolved_by is None
        assert OutgoingEmail.objects.count() == emails
        assert AuditEntry.objects.count() == entries
        assert leaks({"nom": FIRST})  # les dades hi continuen sent

    def test_all_or_nothing_if_the_member_part_fails(self, brunilda, staff, monkeypatch):
        before = _state(brunilda)
        request, _created = erasure.request_erasure(brunilda.person, by=brunilda.account)

        def boom(*args, **kwargs):
            raise ValidationError("falla a propòsit")

        monkeypatch.setattr(members_privacy, "_scrub_requests", boom)
        with pytest.raises(ValidationError):
            erasure.approve(request, by=staff.handler)
        assert _state(brunilda) == before

    def test_confirmation_email_is_queued_before_and_still_goes_out(self, brunilda, staff):
        """RN-A14: el correu de confirmació es posa a la cua abans d'anonimitzar i surt; després,
        l'adreça ja no queda al registre d'enviaments."""
        erase(brunilda, staff)
        email = OutgoingEmail.objects.get(template=erasure.DONE_EMAIL)
        assert (email.status, email.to_address) == ("queued", EMAIL)
        django_mail.outbox.clear()
        mail.deliver(email.pk)
        (sent,) = django_mail.outbox
        assert sent.to == [EMAIL]
        assert FIRST not in sent.body and LAST not in sent.body
        email.refresh_from_db()
        assert email.status == "sent"
        assert email.to_address == persons.anonymous_email(
            Person.objects.get(pk=brunilda.person.pk).anonymous_ref
        )

    def test_pending_requests_are_closed_and_scheduled_leave_is_not_applied_again(
        self, brunilda, staff
    ):
        today = timezone.localdate()
        leave = member_requests.request_leave(
            brunilda.member, by=brunilda.account, reason="Baixa a final d'any"
        )
        member_requests.approve_leave(
            leave, by=staff.worker, effective_on=today + datetime.timedelta(days=30)
        )
        assert member_requests.is_scheduled(leave)
        erase(brunilda, staff)
        leave.refresh_from_db()
        assert leave.applied_at is not None
        assert member_requests.apply_due_leaves(today + datetime.timedelta(days=31)) == []
        assert not MemberRequest.objects.filter(
            person=brunilda.person, status=MemberRequest.Status.PENDING
        ).exists()

    def test_a_person_without_member_with_a_pending_join_is_erased_too(self, staff):
        b = staff.builder
        request = b.submit("Ona", "Llobarro Pendent", "ona@example.org", b.born(30), b.full)
        account = b.personal(request.person)
        erase(SimpleNamespace(person=request.person, account=account), staff)
        _deliver_queued()
        request.refresh_from_db()
        assert request.status == MemberRequest.Status.CANCELLED
        assert request.birth_date is None
        assert not Member.objects.filter(person=request.person).exists()
        assert leaks({"cognoms": "Llobarro Pendent", "correu": "ona@example.org"}) == []


def _money_snapshot():
    return {
        "charges": list(Charge.objects.order_by("pk").values()),
        "payments": list(Payment.objects.order_by("pk").values()),
        "fees": list(AnnualFee.objects.order_by("pk").values()),
    }


def _state(subject):
    person = Person.objects.filter(pk=subject.person.pk).values().get()
    member = Member.objects.filter(pk=subject.member.pk).values().get()
    return {
        "person": person,
        "member": member,
        "accounts": list(Account.objects.filter(person=subject.person).values()),
        "cards": list(MemberCard.objects.filter(member=subject.member).values()),
        "history": list(MemberStatusChange.objects.filter(member=subject.member).values()),
        "requests": list(MemberRequest.objects.filter(person=subject.person).values()),
        "files": list(PrivateFile.objects.filter(owner=subject.person).values()),
    }


# --- Q-14: càrrecs pendents -----------------------------------------------------------------


class TestOpenCharges:
    def test_ca_19_7_with_an_open_charge_the_erasure_is_not_executed(self, staff):
        """CA-19.7 està pendent de Q-14: amb un càrrec pendent, l'esborrat no s'executa i no es
        toca cap càrrec. Cap regla inventada: la sol·licitud continua pendent."""
        b = staff.builder
        member = b.approve(
            b.submit("Marta", "Rap Pendent", "marta.rap@example.org", b.born(40), b.full)
        )
        account = b.personal(member.person)
        request, _created = erasure.request_erasure(member.person, by=account)
        money = _money_snapshot()
        assert erasure.blockers(member.person)
        with pytest.raises(erasure.ErasureNotAllowed):
            erasure.approve(request, by=staff.handler)
        request.refresh_from_db()
        assert request.status == ErasureRequest.Status.PENDING
        assert _money_snapshot() == money
        assert Person.objects.get(pk=member.person.pk).status == Person.Status.ACTIVE
        # Pagada la quota, ja es pot.
        b.pay(member.fees.get())
        assert erasure.blockers(member.person) == []
        assert erasure.approve(request, by=staff.handler).status == "executed"


# --- Després de l'esborrat ------------------------------------------------------------------


class TestAnonymisedPerson:
    def test_cannot_log_in(self, brunilda, staff, client):
        erase(brunilda, staff)
        account = Account.objects.get(pk=brunilda.account.pk)
        for login in (EMAIL, account.login):
            response = client.post(
                reverse("accounts:login"), {"login": login, "password": PASSWORD}
            )
            assert response.status_code == 200  # torna el formulari, sense sessió
            assert "_auth_user_id" not in client.session

    def test_rn_a14_receives_no_email(self, brunilda, staff):
        erase(brunilda, staff)
        person = Person.objects.get(pk=brunilda.person.pk)
        count = OutgoingEmail.objects.count()
        assert mail.queue_email("prova", to=EMAIL, person=person) is None
        assert OutgoingEmail.objects.count() == count
        assert not invitations.eligible(person)

    def test_ca_19_2_is_not_in_the_list_the_search_or_the_export(self, brunilda, staff, login_as):
        """CA-19.2: deixa d'aparèixer en llistats i cerques (i a l'exportació de socis)."""
        number = brunilda.member.member_number
        client = login_as(staff.worker, AREA_ADMIN)
        listing = reverse("administration:members_list")
        assert FIRST in client.get(listing).content.decode()
        erase(brunilda, staff)
        ref = Person.objects.get(pk=brunilda.person.pk).anonymous_ref
        for query in (
            "",
            f"?q={FIRST}",
            f"?q={number}",
            f"?q={DOCUMENT}",
            f"?q={ref}",
            "?estat=left",
        ):
            response = client.get(listing + query)
            assert response.status_code == 200
            assert brunilda.member not in [member for member, _fee in response.context["rows"]]
            if ref not in query:  # la cerca es torna a mostrar al camp
                assert ref not in response.content.decode(), query
        members = roster.filtered_members({}, can_search_document=True)
        assert brunilda.member.pk not in members.values_list("pk", flat=True)
        export = client.get(reverse("administration:members_export") + "?format=csv")
        assert ref not in export.content.decode("utf-8-sig")
        assert (
            persons.find_duplicates(
                id_document_type="dni", id_document_number=DOCUMENT, contact_email=EMAIL
            )
            == persons.DuplicateCheck()
        )

    def test_cannot_be_edited_or_exported_again(self, brunilda, staff):
        erase(brunilda, staff)
        person = Person.objects.get(pk=brunilda.person.pk)
        with pytest.raises(ValidationError):
            persons.update_profile(person, actor=staff.worker, phone="600000000")
        with pytest.raises(ValidationError):
            privacy.request_export(person, by=staff.handler)
        with pytest.raises(ValidationError):
            privacy.anonymise_person(person, by=staff.handler)


# --- L'excepció del disparador de l'historial (members/0018) --------------------------------


class TestStatusHistoryTrigger:
    """L'excepció és a la base de dades: ni amb el paràmetre posat es pot fer res més que
    escriure-hi la referència anònima de la persona d'aquell soci, ja anonimitzada."""

    def _update(self, sql, params):
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SELECT set_config('cris.rgpd_anonymise', 'on', true)")
            cursor.execute(sql, params)

    def test_without_the_setting_the_reason_cannot_change(self, brunilda, staff):
        erase(brunilda, staff)
        ref = Person.objects.get(pk=brunilda.person.pk).anonymous_ref
        change = brunilda.member.status_changes.first()
        with pytest.raises(DatabaseError, match="no es pot modificar ni esborrar"):
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE members_memberstatuschange SET reason = %s WHERE id = %s",
                    [ref, change.pk],
                )

    def test_reason_of_a_member_who_is_not_anonymised_cannot_change(self, brunilda):
        change = brunilda.member.status_changes.exclude(reason="").first()
        for value in ("A-0001", "", "un altre text"):
            with pytest.raises(DatabaseError, match="no es pot modificar ni esborrar"):
                self._update(
                    "UPDATE members_memberstatuschange SET reason = %s WHERE id = %s",
                    [value, change.pk],
                )

    def test_only_the_own_anonymous_reference_is_accepted(self, brunilda, staff):
        b = staff.builder
        other = b.paid_member("Quimet", "Llobarro", "quimet@example.org", b.full)
        erase(SimpleNamespace(person=other.person, account=b.personal(other.person)), staff)
        other_ref = Person.objects.get(pk=other.person.pk).anonymous_ref
        erase(brunilda, staff)
        ref = Person.objects.get(pk=brunilda.person.pk).anonymous_ref
        change = brunilda.member.status_changes.order_by("id").first()
        update = "UPDATE members_memberstatuschange SET reason = %s"
        rejected = [
            (f"{update} WHERE id = %s", ["text lliure", change.pk]),
            # La referència d'una altra persona anonimitzada tampoc.
            (f"{update} WHERE id = %s", [other_ref, change.pk]),
            (f"{update}, to_status = 'active' WHERE id = %s", [ref, change.pk]),
            (f"{update}, effective_on = '2001-01-01' WHERE id = %s", [ref, change.pk]),
            (f"{update}, actor_account_id = NULL WHERE id = %s", [ref, change.pk]),
            (
                "DELETE FROM members_memberstatuschange WHERE %s <> '' AND id = %s",
                [ref, change.pk],
            ),
        ]
        for sql, params in rejected:
            with pytest.raises(DatabaseError, match="no es pot modificar ni esborrar"):
                self._update(sql, params)
        self._update(f"{update} WHERE id = %s", [ref, change.pk])
        assert MemberStatusChange.objects.get(pk=change.pk).reason == ref
