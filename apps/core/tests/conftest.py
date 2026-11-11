import pytest
from django.utils import timezone

from apps.accounts.models import Account, TotpDevice
from apps.core import mail
from apps.core.crypto import encrypt
from apps.core.models import AccountRole, OutgoingEmail, Person, Role


@pytest.fixture
def email_templates(tmp_path, settings, monkeypatch):
    """Plantilles inventades en una carpeta temporal, abans de les del projecte. Cada una
    declara la seva prioritat (RN-A8); amb `priority=None`, no en declara cap."""
    folder = tmp_path / "emails"
    folder.mkdir()

    def write(
        name, language, subject, body, html=None, priority=OutgoingEmail.Priority.CONFIRMATION
    ):
        (folder / f"{name}.{language}.subject.txt").write_text(subject, encoding="utf-8")
        (folder / f"{name}.{language}.txt").write_text(body, encoding="utf-8")
        if html is not None:
            (folder / f"{name}.{language}.html").write_text(html, encoding="utf-8")
        if priority is not None:
            monkeypatch.setitem(mail.TEMPLATE_PRIORITIES, name, priority)

    templates = [dict(settings.TEMPLATES[0])]
    templates[0]["DIRS"] = [tmp_path, *templates[0]["DIRS"]]
    settings.TEMPLATES = templates
    return write


@pytest.fixture
def make_admin(db):
    """Compte d'administrador amb els rols indicats. Per defecte, operatiu (amb TOTP)."""
    counter = iter(range(1, 10_000))

    def make(*roles, username=None, totp=True, emergency=False, person=None):
        n = next(counter)
        person = person or Person.objects.create(first_name=f"Admin{n}", origin="in_person")
        account = Account.objects.create_admin(person, username or f"admin{n}")
        if emergency:
            account.is_emergency = True
            account.save()
        if totp:
            TotpDevice.objects.create(
                account=account,
                secret_encrypted=encrypt("JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"),
                confirmed_at=timezone.now(),
            )
        for code in roles:
            AccountRole.objects.create(admin_account=account, role=Role.objects.get(code=code))
        return account

    return make
