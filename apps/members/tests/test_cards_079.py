"""Carnet després de la decisió 079 (T-M01-19; RN-M01-85 i RN-M01-92; CA-M01-87, 88, 104 i 105;
especificació a docs/planning.md#M01-079-qr): QR calculat amb una clau del servidor, versió i
identificador de clau, rotació, PDF des del navegador, revocació amb P21 i carnet nou a petició
del soci. Només dades inventades; les claus d'aquestes proves són inventades.
"""

import hashlib
import re
import time
from datetime import date

import pytest
from django.core.checks import run_checks
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.management import CommandError, call_command
from django.http import Http404
from django.test import Client, override_settings
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import audit
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import card_keys, cards, services
from apps.members.models import Member, MemberCard
from apps.members.services import OwnMemberChange
from apps.members.tests.test_cards import SYSTEM, make_member, paid_member
from apps.members.tests.test_roster import admin_client
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

S = Member.Status
CARD = "members:card"
RENEW = "members:card_renew"
REVOKE = "administration:member_card_revoke"
DETAIL = "administration:member_detail"
# Claus inventades de 32 caràcters o més, només per a aquestes proves.
K1 = "k1:" + "clau-inventada-de-proves-numero-u-1954"  # gitleaks:allow (clau inventada de proves)
K2 = "k2:" + "clau-inventada-de-proves-numero-dos-54"  # gitleaks:allow (clau inventada de proves)
REASON = "Carnet perdut (motiu inventat)"


def with_keys(*keys, active):
    return override_settings(CARD_QR_KEYS=list(keys), CARD_QR_ACTIVE_KEY=active)


def personal_client(member):
    account = Account.objects.create_personal(
        member.person, f"soci{member.pk}@example.org", PASSWORD
    )
    account.status = Account.Status.ACTIVE
    account.save()
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_PERSONAL
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client, account


def qr_path_data(html):
    """El dibuix del QR (el camí de l'SVG), per comparar-ne dos."""
    # Només dins del QR: la pàgina pot dur altres icones en SVG (la barra Ramillete, T-DX-08).
    found = re.search(r'<div class="qr"[^>]*>.*?<path d="([^"]+)"', html, re.S)
    return found.group(1) if found else None


# --- CA-M01-87: el QR es calcula, no es desa, i canvia en reemetre ----------------------------


class TestCaM0187ComputedToken:
    def test_ca_m01_87_only_hash_version_and_key_id_are_stored(self):
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        card = MemberCard.objects.get(member=member)
        assert (card.version, card.key_id) == (1, card_keys.DEV_KID)
        assert card.token_hash == hashlib.sha256(token.encode()).hexdigest()
        stored = " ".join(str(v) for v in MemberCard.objects.values().get().values())
        logged = " ".join(str(v) for e in AuditEntry.objects.values() for v in e.values())
        secret = token.split(".", 1)[1]
        assert token not in stored and secret not in stored
        assert token not in logged and secret not in logged

    def test_ca_m01_87_the_token_is_recomputed_and_is_always_the_same(self):
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        card = MemberCard.objects.get(member=member)
        assert cards.qr_token(card) == token
        assert cards.qr_token(MemberCard.objects.get(pk=card.pk)) == token
        assert token == card_keys.token(member.pk, 1, card_keys.DEV_KID)
        assert cards.valid_card_for_token(token) == card

    def test_ca_m01_87_token_does_not_depend_on_personal_data_or_member_number(self):
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        Member.objects.filter(pk=member.pk).update(member_number=9999)
        type(member.person).objects.filter(pk=member.person_id).update(first_name="Altra")
        assert cards.qr_token(MemberCard.objects.get(member=member)) == token

    def test_ca_m01_87_a_reissued_card_has_a_new_version_and_a_different_qr(self):
        member = paid_member()
        old = cards.issue_card(member, by=SYSTEM)
        new = cards.replace_card(member, by=SYSTEM, reason=REASON)
        versions = list(
            MemberCard.objects.filter(member=member)
            .order_by("pk")
            .values_list("version", flat=True)
        )
        assert versions == [1, 2]
        assert old != new
        assert cards.valid_card_for_token(old) is None  # CA-M01-15
        assert cards.valid_card_for_token(new) is not None
        assert services.verify_card(old)["valid"] is False
        assert services.verify_card(new)["valid"] is True

    def test_two_members_never_share_a_token(self):
        first = cards.issue_card(paid_member(), by=SYSTEM)
        second = cards.issue_card(paid_member("Berta", 1288, document="87654321X"), by=SYSTEM)
        assert first != second

    def test_a_tampered_card_row_shows_no_qr(self):
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        MemberCard.objects.filter(member=member).update(token_hash="b" * 64)
        card = MemberCard.objects.get(member=member)
        assert cards.qr_token(card) is None and cards.qr_svg(card) is None

    def test_ca_m01_87_the_page_shows_the_same_qr_every_time(self):
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        client, _account = personal_client(member)
        first = client.get(reverse(CARD))
        second = client.get(reverse(CARD))
        assert "no-store" in first["Cache-Control"]
        assert qr_path_data(first.content.decode())
        assert qr_path_data(first.content.decode()) == qr_path_data(second.content.decode())
        assert token not in first.content.decode()  # el testimoni és dins del dibuix, no en text
        assert cards.verification_url(token).endswith(f"/carnet/verificar/{token}/")


# --- CA-M01-88: identificador de clau i rotació -----------------------------------------------


class TestCaM0188KeyRotation:
    def test_ca_m01_88_rotating_the_active_key_keeps_old_cards_working(self):
        member = paid_member()
        with with_keys(K1, active="k1"):
            token = cards.issue_card(member, by=SYSTEM)
        card = MemberCard.objects.get(member=member)
        assert card.key_id == "k1"
        with with_keys(K1, K2, active="k2"):
            assert cards.valid_card_for_token(token) == card
            assert cards.qr_token(card) == token
            newer = paid_member("Berta", 1288, document="87654321X")
            cards.issue_card(newer, by=SYSTEM)
            assert MemberCard.objects.get(member=newer).key_id == "k2"

    def test_ca_m01_88_a_retired_key_still_verifies_but_the_qr_cannot_be_shown(self):
        member = paid_member()
        with with_keys(K1, active="k1"):
            token = cards.issue_card(member, by=SYSTEM)
        client, account = personal_client(member)
        with with_keys(K2, active="k2"):
            card = MemberCard.objects.get(member=member)
            assert cards.valid_card_for_token(token) == card  # verificar no fa servir cap clau
            assert cards.qr_token(card) is None
            page = client.get(reverse(CARD)).content.decode()
            assert "El codi QR d'aquest carnet no es pot mostrar" in page
            assert qr_path_data(page) is None
            assert "Demana un carnet nou" in page

            response = client.post(reverse(RENEW))
            assert response.status_code == 303
            new = MemberCard.objects.get(member=member, revoked_at__isnull=True)
            assert (new.key_id, new.version) == ("k2", 2)
            assert cards.valid_card_for_token(token) is None
            assert qr_path_data(client.get(reverse(CARD)).content.decode())
            entry = AuditEntry.objects.filter(action=cards.CARD_REVOKED).get()
            assert entry.actor_account == account
            assert entry.reason == cards.OWN_REQUEST_REASON

    def test_cards_from_before_the_079_verify_but_show_no_qr(self):
        member = paid_member()
        legacy = "testimoni-aleatori-anterior-a-la-079"
        card = MemberCard.objects.create(
            member=member, token_hash=hashlib.sha256(legacy.encode()).hexdigest()
        )
        assert card.key_id == ""
        assert cards.valid_card_for_token(legacy) == card
        assert cards.qr_token(card) is None

    def test_reissue_command_replaces_the_cards_of_a_key(self):
        first = paid_member()
        second = paid_member("Berta", 1288, document="87654321X")
        unpaid = paid_member("Carla", 1289, document="11111111H")
        with with_keys(K1, active="k1"):
            old = cards.issue_card(first, by=SYSTEM)
            cards.issue_card(unpaid, by=SYSTEM)
        Member.objects.filter(pk=unpaid.pk).update(status=S.UNPAID)
        with with_keys(K1, K2, active="k2"):
            cards.issue_card(second, by=SYSTEM)
            with pytest.raises(CommandError):
                call_command("reemet_carnets", "--clau", "k2", "--motiu", REASON)
            call_command("reemet_carnets", "--clau", "k1", "--motiu", REASON)
            assert cards.valid_card_for_token(old) is None
            assert MemberCard.objects.get(member=first, revoked_at__isnull=True).key_id == "k2"
            assert MemberCard.objects.filter(member=second).count() == 1  # no era de la clau k1
            # Un impagat no pot tenir carnet nou: es queda amb el carnet revocat.
            assert not MemberCard.objects.filter(member=unpaid, revoked_at__isnull=True).exists()
            revoked = AuditEntry.objects.filter(action=cards.CARD_REVOKED)
            assert {e.reason for e in revoked} == {REASON}
            assert {e.actor_origin for e in revoked} == {"members.reemet_carnets"}


class TestKeyConfiguration:
    def test_without_keys_a_dev_key_is_derived(self):
        assert list(card_keys.keys()) == [card_keys.DEV_KID]
        assert card_keys.active_key_id() == card_keys.DEV_KID
        assert run_checks(tags=None) == [] or all(e.id != "members.E001" for e in run_checks())

    @override_settings(CARD_QR_KEYS=[], CARD_QR_ACTIVE_KEY="", CARD_QR_KEYS_REQUIRED=True)
    def test_where_keys_are_required_the_startup_check_fails_without_them(self):
        with pytest.raises(ImproperlyConfigured):
            card_keys.keys()
        assert [e.id for e in run_checks() if e.id == "members.E001"] == ["members.E001"]

    @pytest.mark.parametrize(
        ("keys", "active"),
        [
            (["k1:curta"], "k1"),
            (["K1:" + "x" * 40], "K1"),
            (["massallarg1:" + "x" * 40], "massallarg1"),
            ([K1, K1], "k1"),
            ([K1], "k2"),
            ([K1], ""),
        ],
    )
    def test_bad_configuration_fails_the_startup_check(self, keys, active):
        with override_settings(CARD_QR_KEYS=keys, CARD_QR_ACTIVE_KEY=active):
            assert [e.id for e in run_checks() if e.id == "members.E001"] == ["members.E001"]

    def test_check_message_never_contains_a_key(self):
        with override_settings(CARD_QR_KEYS=["k1:curta-i-secreta"], CARD_QR_ACTIVE_KEY="k1"):
            (error,) = [e for e in run_checks() if e.id == "members.E001"]
        assert "curta-i-secreta" not in error.msg


# --- CA-M01-104: el PDF és la impressió del navegador -----------------------------------------


class TestCaM01104Print:
    def test_ca_m01_104_page_has_the_print_button_and_marks_what_is_not_printed(self):
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        client, _account = personal_client(member)
        page = client.get(reverse(CARD)).content.decode()
        assert "data-imprimeix" in page and "Desa com a PDF" in page
        assert "js/imprimeix.js" in page
        for markup in (
            '<section class="no-imprimeix" aria-labelledby="carnet-nou-titol">',
            '<p class="enllacos no-imprimeix">',
            '<div class="accions no-imprimeix">',
        ):
            assert markup in page

    def test_ca_m01_104_print_styles_hide_navigation_and_actions(self, settings):
        css = (settings.BASE_DIR / "static" / "css" / "comptes.css").read_text(encoding="utf-8")
        printing = css[css.index("@media print") :]
        for selector in (".capcalera-compte", ".no-imprimeix"):
            assert selector in printing
        assert "display: none" in printing
        script = (settings.BASE_DIR / "static" / "js" / "imprimeix.js").read_text(encoding="utf-8")
        assert "window.print()" in script and "beforeprint" in script


# --- CA-M01-105: revocació amb P21 i carnet nou a petició del soci ----------------------------


class TestCaM01105AdminRevocation:
    @pytest.fixture
    def secretary(self, make_admin):  # noqa: F811
        return make_admin(Role.Code.SECRETARY)

    def test_ca_m01_105_secretary_revokes_with_reason_and_it_is_recorded(self, secretary):
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        response = admin_client(secretary).post(
            reverse(REVOKE, args=[member.pk]), {"motiu": f"  {REASON}  "}
        )
        assert response.status_code == 303
        assert services.verify_card(token)["valid"] is False
        card = MemberCard.objects.get(member=member)
        assert card.revoked_at is not None and card.revoked_reason == REASON
        entry = AuditEntry.objects.get(action=cards.CARD_REVOKED)
        assert (entry.actor_account, entry.reason) == (secretary, REASON)
        assert not MemberCard.objects.filter(member=member, revoked_at__isnull=True).exists()

    @pytest.mark.parametrize("reason", ["", "   "])
    def test_ca_m01_105_without_reason_is_rejected(self, secretary, reason):
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        admin_client(secretary).post(reverse(REVOKE, args=[member.pk]), {"motiu": reason})
        assert services.verify_card(token)["valid"] is True
        with pytest.raises(ValidationError):
            cards.revoke_by_admin(member, by=secretary, reason=reason)

    @pytest.mark.parametrize("role", ["treasurer", "administrator", "president", "board"])
    def test_ca_m01_105_without_p21_is_not_found(self, make_admin, role):  # noqa: F811
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        account = make_admin(role)
        response = admin_client(account).post(reverse(REVOKE, args=[member.pk]), {"motiu": REASON})
        assert response.status_code == 404
        with pytest.raises(Http404):
            cards.revoke_by_admin(member, by=account, reason=REASON)
        assert services.verify_card(token)["valid"] is True

    def test_ca_m01_105_own_card_is_rejected_and_recorded(self, make_admin):  # noqa: F811
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        own = make_admin(Role.Code.SECRETARY, person=member.person)
        with pytest.raises(OwnMemberChange):
            cards.revoke_by_admin(member, by=own, reason=REASON)
        admin_client(own).post(reverse(REVOKE, args=[member.pk]), {"motiu": REASON})
        assert services.verify_card(token)["valid"] is True
        assert AuditEntry.objects.filter(action=services.OWN_MEMBER_REJECTED).count() == 2

    def test_ca_m01_105_get_is_not_allowed_and_csrf_is_required(self, secretary):
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        url = reverse(REVOKE, args=[member.pk])
        assert admin_client(secretary).get(url).status_code == 405
        assert admin_client(secretary, csrf=True).post(url, {"motiu": REASON}).status_code == 403
        assert MemberCard.objects.filter(member=member, revoked_at__isnull=True).exists()

    def test_detail_shows_the_form_only_with_p21_and_never_the_token(self, secretary, make_admin):  # noqa: F811
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        detail = reverse(DETAIL, args=[member.pk])
        page = admin_client(secretary).get(detail).content.decode()
        assert "Revoca el carnet" in page and "versió 1" in page
        assert token not in page and "<svg" not in page.split('id="carnet-titol"')[1][:1500]
        other = admin_client(make_admin("administrator")).get(detail).content.decode()
        assert "Revoca el carnet" not in other

    def test_ca_m01_105_after_revocation_the_member_can_request_a_new_card(self, secretary):
        member = paid_member()
        old = cards.issue_card(member, by=SYSTEM)
        cards.revoke_by_admin(member, by=secretary, reason=REASON)
        client, account = personal_client(member)
        page = client.get(reverse(CARD)).content.decode()
        assert "Ara no tens cap carnet." in page and "Demana un carnet nou" in page
        assert client.post(reverse(RENEW)).status_code == 303
        new = MemberCard.objects.get(member=member, revoked_at__isnull=True)
        assert new.version == 2
        assert services.verify_card(old)["valid"] is False
        issued = AuditEntry.objects.filter(action=cards.CARD_ISSUED).order_by("-pk").first()
        assert issued.actor_account == account


class TestOwnRequest:
    def test_a_member_who_cannot_have_a_card_gets_none(self):
        member = make_member(status=S.PENDING)
        client, _account = personal_client(member)
        page = client.get(reverse(CARD)).content.decode()
        assert "Demana un carnet nou" not in page
        response = client.post(reverse(RENEW), follow=True)
        assert not MemberCard.objects.exists()
        assert "Només té carnet un soci actiu" in response.content.decode()

    def test_only_the_own_card_is_renewed(self):
        other = paid_member("Sentinella", 1999, document="87654321X")
        other_token = cards.issue_card(other, by=SYSTEM)
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        client, _account = personal_client(member)
        client.post(reverse(RENEW))
        assert services.verify_card(other_token)["valid"] is True
        assert MemberCard.objects.filter(member=other).count() == 1
        assert MemberCard.objects.filter(member=member).count() == 2

    def test_renew_needs_post_csrf_and_a_session(self):
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        client, account = personal_client(member)
        assert client.get(reverse(RENEW)).status_code == 405
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(account)
        assert strict.post(reverse(RENEW)).status_code in (302, 403)
        assert Client().post(reverse(RENEW)).status_code == 302  # a l'entrada
        assert MemberCard.objects.filter(member=member).count() == 1

    def test_system_issue_date_is_kept(self):
        member = paid_member()
        cards.issue_card(member, by=audit.system("proves"))
        assert MemberCard.objects.get(member=member).issued_at.date() >= date(2026, 1, 1)
