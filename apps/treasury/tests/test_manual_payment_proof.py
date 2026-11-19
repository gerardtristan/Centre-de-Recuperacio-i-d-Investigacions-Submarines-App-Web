"""Comprovant opcional del pagament a mà (P-12b; 072, Q-038; P-405). Només dades inventades."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.core import files
from apps.core.models import Payment, PrivateFile
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.tests.test_roster import admin_client
from apps.treasury.tests.test_manual_payment import (  # noqa: F401 (fixtures)
    URL,
    cash,
    fee,
    review,
    treasurer,
)

pytestmark = pytest.mark.django_db
PDF = b"%PDF-1.7\n%rebut inventat\n"


def pay(client, fee, cash, proof):  # noqa: F811
    url = reverse(URL, args=[fee.charge_id])
    _first, token = review(client, url, cash)
    data = {"token": token} | ({"proof": proof} if proof else {})
    return client.post(url, data)


def test_the_proof_is_stored_privately_with_the_payment(fee, treasurer, cash):  # noqa: F811
    client = admin_client(treasurer)
    assert pay(client, fee, cash, SimpleUploadedFile("rebut.pdf", PDF)).status_code == 302
    proof = Payment.objects.get().proof
    assert (proof.kind, proof.owner, proof.content_type) == (
        PrivateFile.Kind.PAYMENT_PROOF,
        fee.charge.person,
        "application/pdf",
    )
    assert proof.download_name == "comprovant-pagament.pdf"
    # RN-B8 i 058, punt 7: és un document econòmic, no s'esborra amb l'esborrat RGPD.
    assert files.expire_owner_files(fee.charge.person) == 0


def test_without_a_proof_nothing_changes(fee, treasurer, cash):  # noqa: F811
    assert pay(admin_client(treasurer), fee, cash, None).status_code == 302
    assert Payment.objects.get().proof is None
    assert not PrivateFile.objects.exists()


def test_a_file_that_is_not_a_receipt_saves_nothing(fee, treasurer, cash):  # noqa: F811
    response = pay(admin_client(treasurer), fee, cash, SimpleUploadedFile("rebut.pdf", b"MZ"))
    assert "no és permès" in response.content.decode()
    assert not Payment.objects.exists() and not PrivateFile.objects.exists()


def test_only_who_records_manual_payments_opens_it(fee, treasurer, cash, make_admin):  # noqa: F811
    client = admin_client(treasurer)
    pay(client, fee, cash, SimpleUploadedFile("rebut.pdf", PDF))
    proof = Payment.objects.get().proof
    url = reverse("administration:private_file", args=[proof.pk])
    assert client.get(url).status_code == 302
    for role in ("secretary", "administrator", "board"):
        assert admin_client(make_admin(role)).get(url).status_code == 404
    # La llista de moviments hi enllaça només per a qui el pot obrir.
    movements = reverse("administration:treasury_movements")
    assert url in client.get(movements).content.decode()
    assert url not in admin_client(make_admin("board")).get(movements).content.decode()
