# ruff: noqa: F811 (fixtures importades com a paràmetres)
"""Conservació de les fotos dels carnets (T-M02-47; RN-M02-54; VC-57; CA-M02-56). Només dades
inventades."""

import datetime

import pytest
from django.core.files.storage import storages
from django.utils import timezone

from apps.activities import card_photos, filings, tasks
from apps.activities.models import CertificationCardPhoto, CertificationFiling
from apps.core.audit import Action
from apps.core.models import AuditEntry, PrivateFile, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .test_card_photos import cert, holder, photos_on, upload  # noqa: F401 (fixtures)
from .test_filings import levels, padi_cert, secretary, setting  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
F = CertificationFiling


def at(day):
    return timezone.make_aware(datetime.datetime.combine(day, datetime.time(10)))


@pytest.fixture
def three_months(make_admin):
    setting("activities.card_photo_retention_months", 3, make_admin(Role.Code.ADMINISTRATOR))


def test_ca_m02_56_three_months_after_the_homologation_is_done(
    photos_on, three_months, cert, holder, secretary, django_capture_on_commit_callbacks
):
    photo = upload(cert, holder)
    CertificationCardPhoto.objects.filter(pk=photo.pk).update(
        uploaded_at=at(datetime.date(2026, 12, 1))
    )
    filing = filings.request_homologation(cert, by=secretary)
    F.objects.filter(pk=filing.pk).update(
        status=F.Status.DONE, closed_at=at(datetime.date(2027, 1, 1))
    )
    cert.verified_by, cert.verified_at = secretary, at(datetime.date(2027, 1, 1))
    cert.save(update_fields=["verified_by", "verified_at"])

    assert card_photos.purge_expired(datetime.date(2027, 3, 31)) == 0
    assert CertificationCardPhoto.objects.exists()
    with django_capture_on_commit_callbacks(execute=True):
        assert card_photos.purge_expired(datetime.date(2027, 4, 1)) == 1

    assert not CertificationCardPhoto.objects.exists()
    file = PrivateFile.objects.get(pk=photo.file_id)
    assert file.deleted_at is not None and not storages["private"].exists(file.storage_key)
    cert.refresh_from_db()
    assert cert.verified_at is not None  # la titulació continua verificada
    entry = AuditEntry.objects.get(action=card_photos.EXPIRED)
    assert (entry.actor_kind, entry.actor_origin) == ("system", "activities.purge_card_photos")
    assert AuditEntry.objects.get(action=Action.FILE_DELETED).actor_kind == "system"


def test_an_open_homologation_keeps_the_photo(photos_on, three_months, cert, holder, secretary):
    photo = upload(cert, holder)
    filings.request_homologation(cert, by=secretary)
    assert card_photos.delete_after(photo, 3) is None
    assert card_photos.purge_expired(datetime.date(2030, 1, 1)) == 0


def test_without_anything_else_it_expires_months_after_the_upload(
    photos_on, three_months, cert, holder
):
    photo = upload(cert, holder)
    CertificationCardPhoto.objects.filter(pk=photo.pk).update(
        uploaded_at=at(datetime.date(2027, 1, 31))
    )
    photo.refresh_from_db()
    assert card_photos.delete_after(photo, 3) == datetime.date(2027, 4, 30)  # final de mes
    assert card_photos.delete_after(photo, 0) == datetime.date(2027, 1, 31)
    assert card_photos.delete_after(photo, 12) == datetime.date(2028, 1, 31)


def test_the_daily_task_runs_the_purge(photos_on, three_months, cert, holder, monkeypatch):
    calls = []
    monkeypatch.setattr(card_photos, "purge_expired", lambda: calls.append(1) or 0)
    tasks.purge_card_photos(timestamp=0)
    assert calls == [1]
