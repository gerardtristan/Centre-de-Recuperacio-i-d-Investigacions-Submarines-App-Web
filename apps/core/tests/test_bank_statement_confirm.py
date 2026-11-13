"""Importació de l'extracte bancari, segona part: pantalla, confirmar i desfer (T-M00-01; spec 00,
HU-21, CA-21.1 a CA-21.5; RN-92, RN-98, RN-101; V-06). Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.core import imports
from apps.core.imports import bank_statement as bs
from apps.core.models import AuditEntry, ImportBatch, ImportLine
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_bank_statement import (
    CARD_ROW,
    HEADER,
    STATEMENT,
    csv_file,
    leaks_account_numbers,
    treasurer,  # noqa: F401 (fixture)
)
from apps.core.tests.test_guest_links import admin_client

pytestmark = pytest.mark.django_db

PAGE = "administration:bank_statement"
CONFIRM = "administration:bank_statement_confirm"
WITH_ERROR = csv_file("31/02/2026;Data impossible;5,00;1,00;", "01/11/2026;Quota;5,00;6,00;")


def upload(client, data, name="extracte.csv"):
    return client.post(reverse(PAGE), {"fitxer": SimpleUploadedFile(name, data, "text/csv")})


def confirmed(by, data=STATEMENT, **kwargs):
    return bs.confirm(bs.preview(data, by=by)["token"], by=by, **kwargs)


def undo_url(batch):
    return reverse("administration:bank_statement_undo", args=[batch.pk])


def nothing_written():
    return not ImportBatch.objects.exists() and not ImportLine.objects.exists()


class TestScreen:
    def test_ca_21_1_preview_on_screen_writes_nothing(self, treasurer):  # noqa: F811
        response = upload(admin_client(treasurer), STATEMENT)
        assert response.status_code == 200
        html = response.content.decode()
        assert "Previsualització" in html and "TRANSF CRIS-AB2CD-K DE PROVA INVENTADA" in html
        assert "+50,00 €" in html and "−12,30 €" in html
        assert not leaks_account_numbers(html)
        assert nothing_written()

    @pytest.mark.parametrize(
        ("data", "name", "message"),
        [
            (b"", "extracte.csv", "El fitxer és buit."),
            (b"%PDF-1.4 no", "extracte.csv", "Aquest tipus de fitxer no és permès."),
            ("Data;Concepte\n01/11/2026;Ç\n".encode("cp1252"), "extracte.csv", "no és permès"),
            (b"Fecha;Concepto\n01/11/2026;x\n", "extracte.csv", str(bs.MESSAGES["format"])),
            (HEADER.encode() + b"\n\n", "extracte.csv", str(bs.MESSAGES["no_lines"])),
            (STATEMENT, "extracte.txt", "Aquest tipus de fitxer no és permès."),
        ],
        ids=["empty", "pdf", "cp1252", "columns", "header-only", "extension"],
    )
    def test_ca_21_5_clear_error_and_nothing_written(self, treasurer, data, name, message):  # noqa: F811
        response = upload(admin_client(treasurer), data, name)
        assert response.status_code == 400
        assert message.replace("'", "&#x27;") in response.content.decode()
        assert nothing_written()

    def test_too_large_upload_never_reaches_the_service(self, treasurer, monkeypatch):  # noqa: F811
        monkeypatch.setattr(bs, "MAX_BYTES", 100)
        assert upload(admin_client(treasurer), STATEMENT).status_code == 413
        assert not AuditEntry.objects.filter(action=bs.audit.Action.BANK_STATEMENT_PREVIEW)

    def test_two_files_are_refused(self, treasurer):  # noqa: F811
        files = [SimpleUploadedFile(f"e{n}.csv", STATEMENT, "text/csv") for n in (1, 2)]
        assert admin_client(treasurer).post(reverse(PAGE), {"fitxer": files}).status_code == 400
        assert nothing_written()

    def test_history_with_undo(self, treasurer):  # noqa: F811
        confirmed(treasurer)
        response = admin_client(treasurer).get(reverse(PAGE))
        assert response.status_code == 200 and "Desfés" in response.content.decode()


class TestConfirm:
    def test_ca_21_3_lines_available_for_reconciliation_and_logged(self, treasurer):  # noqa: F811
        client = admin_client(treasurer)
        token = upload(client, STATEMENT).context["preview"]["token"]
        response = client.post(reverse(CONFIRM), {"testimoni": token}, follow=True)
        assert "Extracte importat" in response.content.decode()
        batch = ImportBatch.objects.get()
        assert (batch.kind, batch.status, batch.confirmed_by) == (
            "bank_statement",
            "confirmed",
            treasurer,
        )
        assert (batch.new_count, batch.duplicate_count, batch.error_count) == (3, 0, 0)
        lines = list(imports.statement_lines(batch).order_by("row"))
        assert [(x.value_date, x.amount_cents, x.balance_cents) for x in lines] == [
            (datetime.date(2026, 11, 2), 5000, 105000),
            (datetime.date(2026, 11, 3), -1230, 103770),
            (datetime.date(2026, 11, 4), -700, 103070),
        ]
        assert not any(leaks_account_numbers(x.concept) for x in lines)
        entry = AuditEntry.objects.get(action=bs.audit.Action.BANK_STATEMENT_CONFIRMED)
        assert entry.actor_account == treasurer and entry.target_id == str(batch.pk)
        assert entry.details == {"counts": {"new": 3, "duplicate": 0, "error": 0}}

    def test_ca_21_2_duplicates_are_kept_without_values(self, treasurer):  # noqa: F811
        confirmed(treasurer)
        data = csv_file(CARD_ROW, "05/11/2026;Quota inventada;30,00;1.060,70;")
        batch = confirmed(treasurer, data)
        assert (batch.new_count, batch.duplicate_count) == (1, 1)
        duplicate = batch.lines.get(row=2)
        assert (duplicate.result, duplicate.amount_cents, duplicate.concept) == (
            "duplicate",
            None,
            "",
        )
        assert imports.statement_lines().count() == 4

    def test_l19_same_file_twice_imports_nothing(self, treasurer):  # noqa: F811
        confirmed(treasurer)
        with pytest.raises(bs.Rejected) as info:
            confirmed(treasurer)
        assert info.value.code == "nothing_to_import"
        assert ImportBatch.objects.count() == 1

    def test_duplicates_are_checked_again_on_confirm(self, treasurer):  # noqa: F811
        first, second = (bs.preview(STATEMENT, by=treasurer)["token"] for _ in range(2))
        bs.confirm(first, by=treasurer)
        with pytest.raises(bs.Rejected) as info:
            bs.confirm(second, by=treasurer)
        assert info.value.code == "nothing_to_import"

    def test_errors_must_be_excluded_explicitly(self, treasurer):  # noqa: F811
        client = admin_client(treasurer)
        token = upload(client, WITH_ERROR).context["preview"]["token"]
        assert client.post(reverse(CONFIRM), {"testimoni": token}).status_code == 400
        assert nothing_written()
        client.post(reverse(CONFIRM), {"testimoni": token, "exclou_errors": "1"})
        batch = ImportBatch.objects.get()
        assert (batch.new_count, batch.error_count, batch.excluded_count) == (1, 1, 1)
        excluded = batch.lines.get(row=2)
        assert (excluded.result, excluded.codes, excluded.concept) == (
            "excluded",
            ["date_invalid"],
            "",
        )

    @pytest.mark.parametrize("change", ["tampered", "other_account", "expired"])
    def test_token_cannot_be_changed_or_reused(self, treasurer, make_admin, monkeypatch, change):  # noqa: F811
        token = bs.preview(STATEMENT, by=treasurer)["token"]
        by = treasurer
        if change == "tampered":
            token = token[:-2] + ("AA" if token[-2:] != "AA" else "BB")
        elif change == "other_account":
            by = make_admin("treasurer")
        else:
            monkeypatch.setattr(bs, "TOKEN_MAX_AGE", -1)
        with pytest.raises(bs.Rejected) as info:
            bs.confirm(token, by=by)
        assert info.value.code == "expired" and nothing_written()


class TestUndo:
    def test_ca_21_4_undo_removes_lines_from_reconciliation(self, treasurer):  # noqa: F811
        batch = confirmed(treasurer)
        response = admin_client(treasurer).post(
            undo_url(batch), {"motiu": "Extracte equivocat (prova)"}, follow=True
        )
        assert "Extracte desfet" in response.content.decode()
        batch.refresh_from_db()
        assert (batch.status, batch.undone_by) == ("undone", treasurer)
        assert not imports.statement_lines().exists()
        assert batch.lines.count() == 3  # no s'esborra res
        entry = AuditEntry.objects.get(action=bs.audit.Action.BANK_STATEMENT_UNDONE)
        assert entry.reason == "Extracte equivocat (prova)"
        assert bs.preview(STATEMENT, by=treasurer)["counts"]["new"] == 3  # es pot tornar a importar

    def test_ca_21_4_reconciled_line_blocks_undo(self, treasurer, monkeypatch):  # noqa: F811
        batch = confirmed(treasurer)
        monkeypatch.setattr(bs, "_reconciled", lambda batch: True)
        with pytest.raises(bs.Rejected) as info:
            bs.undo(batch, by=treasurer, reason="Prova")
        assert info.value.code == "reconciled"
        assert ImportBatch.objects.get().status == "confirmed"

    def test_nothing_points_to_a_fresh_batch(self, treasurer):  # noqa: F811
        assert bs._reconciled(confirmed(treasurer)) is False

    def test_reason_is_required_and_undo_happens_once(self, treasurer):  # noqa: F811
        batch = confirmed(treasurer)
        assert admin_client(treasurer).post(undo_url(batch), {"motiu": "  "}).status_code == 400
        bs.undo(batch, by=treasurer, reason="Prova")
        with pytest.raises(bs.Rejected) as info:
            bs.undo(batch, by=treasurer, reason="Prova")
        assert info.value.code == "not_confirmed"


class TestPermissions:
    @pytest.mark.parametrize("role", [None, "administrator", "secretary", "president"])
    def test_without_m9_not_found_and_nothing_read(self, make_admin, treasurer, role):  # noqa: F811
        batch = confirmed(treasurer)
        client = admin_client(make_admin(*([role] if role else [])))
        assert client.get(reverse(PAGE)).status_code == 404
        assert upload(client, STATEMENT).status_code == 404
        assert client.post(reverse(CONFIRM), {"testimoni": "x"}).status_code == 404
        assert client.post(undo_url(batch), {"motiu": "x"}).status_code == 404
        assert AuditEntry.objects.filter(action=bs.audit.Action.BANK_STATEMENT_PREVIEW).count() == 1
        assert ImportBatch.objects.get().status == "confirmed"

    def test_services_check_m9(self, make_admin, treasurer):  # noqa: F811
        other = make_admin("administrator")
        token = bs.preview(STATEMENT, by=treasurer)["token"]
        with pytest.raises(PermissionDenied):
            bs.confirm(token, by=other)
        batch = bs.confirm(token, by=treasurer)
        with pytest.raises(PermissionDenied):
            bs.undo(batch, by=other, reason="x")
