"""Verificació pública del carnet (T-M01-20; P15; RN-M01-18, 26, 27, 28; CA-M01-09 part del carnet,
CA-M01-13, CA-M01-14, CA-M01-16). Només dades inventades."""

import logging
import re
from datetime import date, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts import limits
from apps.accounts.models import EmailLinkRequest
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.core.models import AuditEntry, Role
from apps.members import cards, services
from apps.members.fee_rules import local_today
from apps.members.models import Member
from apps.members.tests.test_cards import SYSTEM, add_fee, make_member, paid_member, pay
from apps.members.tests.test_services import make_admin
from apps.members.views import public_card

LIMIT = limits.CARD_VERIFY_WINDOW.max_count
INVENTED = "testimoni-inventat-que-no-existeix-1234567890abcdef"
OTHER_INVENTED = "un-altre-testimoni-inventat"


@pytest.fixture(autouse=True)
def no_padding(monkeypatch):
    # El temps mínim es prova a part; aquí només alentiria la suite.
    monkeypatch.setattr(public_card, "MIN_SECONDS", 0)


def url(token):
    return reverse("members:card_verify", kwargs={"token": token})


def main(response):
    """El contingut de <main>: la resta de la pàgina porta el testimoni CSRF, diferent cada cop."""
    return re.search(r"<main.*?</main>", response.content.decode(), re.S).group(0)


def card_for(member):
    return cards.issue_card(member, by=SYSTEM)


@pytest.mark.django_db
class TestResult:
    def test_valid_card_says_valid_and_nothing_else(self, client):
        # CA-M01-13, sense el número parcial (S-M01-06, [A validar: junta]).
        member = paid_member()
        token = card_for(member)
        response = client.get(url(token))
        assert response.status_code == 200
        page = main(response)
        assert "Vàlid" in page and "No vàlid" not in page
        person = member.person
        for data in (
            person.first_name,
            person.last_name,
            person.id_document_number,
            "87",
            member.type.name,
            cards.token_hash(token),
        ):
            assert data not in page
        assert token not in response.content.decode()

    @pytest.mark.parametrize("case", ["invented", "revoked", "unpaid", "left", "expired"])
    def test_every_invalid_token_gets_the_same_page(self, client, case):
        # CA-M01-14, RN-M01-27: inventat, revocat, impagat, de baixa o caducat, la mateixa pàgina.
        reference = client.get(url(INVENTED))
        if case == "expired":
            # Pagat fa més de 12 mesos (070).
            member = make_member()
            pay(add_fee(member, period=2025), timezone.now() - timedelta(days=400))
        else:
            member = paid_member()
        token = card_for(member)
        if case == "invented":
            token = OTHER_INVENTED
        elif case == "revoked":
            cards.revoke_card(member, by=SYSTEM, reason="Prova")
        elif case == "unpaid":
            Member.objects.filter(pk=member.pk).update(status=Member.Status.UNPAID)
        elif case == "left":
            Member.objects.filter(pk=member.pk).update(
                status=Member.Status.LEFT, left_on=date(2026, 1, 1)
            )
        response = client.get(url(token))
        assert response.status_code == reference.status_code == 200
        assert "No vàlid" in main(response)
        assert main(response) == main(reference)

    def test_unpaid_member_card_is_not_valid_without_revoking_it(self, client):
        # CA-M01-09, part del carnet (D1): marcar l'impagat amb motiu fa que el carnet no
        # revocat respongui «No vàlid»; desmarcar-lo el torna «Vàlid».
        treasurer = make_admin(Role.Code.TREASURER)
        member = paid_member()
        token = card_for(member)
        assert "No vàlid" not in main(client.get(url(token)))
        services.mark_unpaid(member, by=treasurer, effective_on=local_today(), reason="Retornat")
        assert "No vàlid" in main(client.get(url(token)))
        assert cards.active_card(member) is not None
        services.unmark_unpaid(member, by=treasurer, effective_on=local_today(), reason="Pagat")
        assert "No vàlid" not in main(client.get(url(token)))

    @pytest.mark.parametrize("area", [AREA_PERSONAL, AREA_ADMIN])
    def test_public_for_any_session(self, login_as, personal_account, admin_account, area):
        # P15: qualsevol persona, també amb sessió.
        token = card_for(paid_member())
        account = personal_account if area == AREA_PERSONAL else admin_account
        response = login_as(account, area).get(url(token))
        assert response.status_code == 200
        assert "No vàlid" not in main(response) and "Vàlid" in main(response)


@pytest.mark.django_db
class TestPrivacy:
    def test_headers_noindex_no_cache_no_referrer(self, client):
        response = client.get(url(INVENTED))
        assert "noindex" in response["X-Robots-Tag"]
        assert "no-store" in response["Cache-Control"]
        assert response["Referrer-Policy"] == "no-referrer"

    def test_token_is_not_stored_or_logged(self, client, caplog):
        token = card_for(paid_member())
        before = AuditEntry.objects.count()
        caplog.set_level(logging.DEBUG)
        client.get(url(token))
        client.post(url(token))  # 405
        for _ in range(LIMIT):
            client.get(url(INVENTED))  # l'última, 429
        assert AuditEntry.objects.count() == before
        stored = [str(v) for row in EmailLinkRequest.objects.values() for v in row.values()]
        assert not any(token in v or INVENTED in v for v in stored)
        assert token not in caplog.text and INVENTED not in caplog.text

    def test_other_methods_are_not_allowed_and_do_not_count(self, client):
        assert client.post(url(INVENTED)).status_code == 405
        assert not EmailLinkRequest.objects.exists()

    def test_minimum_response_time(self, client, monkeypatch):
        # RN-M01-27: la resposta espera fins al temps mínim, sigui el testimoni conegut o no.
        monkeypatch.setattr(public_card, "MIN_SECONDS", 0.25)
        clock = iter([100.0, 100.01])
        monkeypatch.setattr(public_card, "monotonic", lambda: next(clock))
        slept = []
        monkeypatch.setattr(public_card, "sleep", slept.append)
        client.get(url(INVENTED))
        assert slept == [pytest.approx(0.24)]


@pytest.mark.django_db
class TestRateLimit:
    def test_blocked_after_the_v01_limit(self, client):
        # CA-M01-16, RN-M01-28: compten totes les consultes, vàlides o no.
        token = card_for(paid_member())
        for i in range(LIMIT):
            assert client.get(url(token if i % 2 else INVENTED)).status_code == 200
        response = client.get(url(token))
        assert response.status_code == 429
        assert "Massa comprovacions seguides" in main(response)
        assert "Vàlid" not in main(response)  # bloquejada, no diu res del carnet

    def test_limit_is_per_origin(self, client):
        for _ in range(LIMIT):
            client.get(url(INVENTED))
        assert client.get(url(INVENTED)).status_code == 429
        assert client.get(url(INVENTED), REMOTE_ADDR="198.51.100.7").status_code == 200

    def test_blocked_requests_do_not_count_and_the_block_ends(self, client):
        for _ in range(LIMIT + 5):
            client.get(url(INVENTED))
        assert EmailLinkRequest.objects.filter(purpose=limits.CARD_VERIFY).count() == LIMIT
        past = timezone.now() - limits.CARD_VERIFY_WINDOW.period - timedelta(seconds=1)
        EmailLinkRequest.objects.update(created_at=past)
        assert client.get(url(INVENTED)).status_code == 200

    def test_separate_from_email_links_and_join(self, client):
        # Els límits del correu i del formulari d'alta no frenen la verificació, ni al revés.
        for _ in range(LIMIT):
            client.get(url(INVENTED))
        assert not limits.origin_limited("127.0.0.1")
        EmailLinkRequest.objects.all().delete()
        for purpose in (EmailLinkRequest.Purpose.RESET_PASSWORD, limits.JOIN):
            for _ in range(LIMIT):
                EmailLinkRequest.objects.create(ip_address="127.0.0.1", purpose=purpose)
        assert client.get(url(INVENTED)).status_code == 200
