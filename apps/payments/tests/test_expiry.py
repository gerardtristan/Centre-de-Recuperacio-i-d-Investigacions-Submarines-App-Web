"""Caducitat dels mandats sense cobraments en 36 mesos (T-M05a-15; RN-M05a-08). Dates inventades
amb el rellotge controlat (`today`)."""

from datetime import date, datetime

import pytest
from django.utils import timezone

from apps.core.models import AuditEntry, OutgoingEmail
from apps.payments import expiry, tasks
from apps.payments.models import FeePaymentPreference, MandateBankAccount, SepaMandate
from apps.payments.tests.test_mandates import account, member, sign, text  # noqa: F401

pytestmark = pytest.mark.django_db

S = SepaMandate.Status


def dated(mandate, *, signed, collected=None):
    signed_at = timezone.make_aware(datetime(signed.year, signed.month, signed.day, 12))
    SepaMandate.objects.filter(pk=mandate.pk).update(
        signed_at=signed_at, last_collection_on=collected
    )
    return mandate


def status(mandate):
    mandate.refresh_from_db()
    return mandate.status


def test_caduca_el_dia_que_fa_36_mesos_de_l_ultim_cobrament_i_no_esborra_res(sign):  # noqa: F811
    mandate = dated(sign(), signed=date(2022, 3, 1), collected=date(2023, 11, 16))

    assert expiry.expire_mandates(today=date(2026, 11, 15)) == 0
    assert status(mandate) == S.ACTIVE

    assert expiry.expire_mandates(today=date(2026, 11, 16)) == 1
    assert status(mandate) == S.EXPIRED
    assert MandateBankAccount.objects.filter(mandate=mandate).exists()
    entry = AuditEntry.objects.get(action="payments.mandate.expired")
    assert (entry.old_value, entry.new_value, entry.reason) == ("active", "expired", expiry.REASON)
    assert entry.details == {"reference": mandate.reference, "expires_on": "2026-11-16"}
    assert entry.actor_kind == AuditEntry.ActorKind.SYSTEM

    # Idempotent: l'endemà no hi ha res a fer ni cap entrada nova.
    assert expiry.expire_mandates(today=date(2026, 11, 17)) == 0
    assert AuditEntry.objects.filter(action="payments.mandate.expired").count() == 1


def test_sense_cap_cobrament_compta_des_de_la_signatura_p_194(sign):  # noqa: F811
    mandate = dated(sign(), signed=date(2023, 1, 10))

    assert expiry.expire_mandates(today=date(2026, 1, 9)) == 0
    assert expiry.expire_mandates(today=date(2026, 1, 10)) == 1
    assert status(mandate) == S.EXPIRED


def test_un_cobrament_posterior_a_la_signatura_allarga_la_vigencia(sign):  # noqa: F811
    mandate = dated(sign(), signed=date(2023, 1, 10), collected=date(2024, 6, 1))

    assert expiry.expire_mandates(today=date(2026, 1, 10)) == 0
    assert status(mandate) == S.ACTIVE
    assert expiry.expire_mandates(today=date(2027, 6, 1)) == 1


def test_cobrament_del_29_de_febrer_caduca_el_28_de_febrer():
    assert expiry.months_after(date(2024, 2, 29), 36) == date(2027, 2, 28)
    assert expiry.months_after(date(2023, 11, 30), 3) == date(2024, 2, 29)
    assert expiry.months_after(date(2023, 1, 31), 36) == date(2026, 1, 31)


def test_nomes_caduquen_els_actius_i_la_preferencia_no_canvia_p_195(sign, account):  # noqa: F811
    old = dated(sign(), signed=date(2020, 1, 1))
    current = dated(sign(iban="ES2800000000000000000002"), signed=date(2020, 1, 1))
    assert status(old) == S.REVOKED
    FeePaymentPreference.objects.create(
        member=current.member, method="direct_debit", set_by=account, mandate=current
    )
    SepaMandate.objects.filter(pk=current.pk).update(status=S.BLOCKED)

    assert expiry.expire_mandates(today=date(2026, 11, 16)) == 0
    assert (status(old), status(current)) == (S.REVOKED, S.BLOCKED)

    SepaMandate.objects.filter(pk=current.pk).update(status=S.ACTIVE)
    assert expiry.expire_mandates(today=date(2026, 11, 16)) == 1
    preference = FeePaymentPreference.objects.get(member=current.member)
    assert (preference.method, preference.mandate_id) == ("direct_debit", current.pk)


def test_la_tasca_diaria_crida_el_servei(monkeypatch):
    periodic = tasks.app.periodic_registry.periodic_tasks[("payments.expire_mandates", "")]
    assert periodic.cron == "40 4 * * *"
    called = []
    monkeypatch.setattr(expiry, "expire_mandates", lambda: called.append(True))
    tasks.expire_mandates(timestamp=0)
    assert called == [True]


def test_rn_m05a_08_el_soci_rep_un_avis_una_sola_vegada_sense_l_iban(sign, member):  # noqa: F811
    member.person.contact_email = "anna.prova@example.org"
    member.person.save()
    mandate = dated(sign(), signed=date(2023, 1, 10))

    assert expiry.expire_mandates(today=date(2026, 1, 9)) == 0
    assert not OutgoingEmail.objects.exists()
    expiry.expire_mandates(today=date(2026, 1, 10))
    expiry.expire_mandates(today=date(2026, 1, 11))

    email = OutgoingEmail.objects.get()
    assert email.template == "mandat-caducat" and email.to_address == "anna.prova@example.org"
    assert mandate.reference in email.subject and "ES … 0001" in email.body_text
    assert "/socis/pagaments/mandat/" in email.body_text
    assert "00000000000001" not in email.subject + email.body_text


def test_sense_adreca_caduca_igualment_i_no_envia_res(sign):  # noqa: F811
    mandate = dated(sign(), signed=date(2023, 1, 10))
    assert expiry.expire_mandates(today=date(2026, 1, 10)) == 1
    assert status(mandate) == S.EXPIRED
    assert not OutgoingEmail.objects.exists()
