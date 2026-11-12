"""Models del M01 (T-M01-11).

A més del que declara Django, una clau forana composta garanteix que la persona d'una
sol·licitud és la del soci quan la sol·licitud en té (interpretació aprovada el 04/11/2026).
No és cap disparador: és una restricció declarativa de PostgreSQL. Amb `member_id` buit (una
alta) no es comprova (MATCH SIMPLE). Es comprova a l'instant, perquè un servei pugui capturar
l'error dins del seu punt de desat; és diferible perquè la neteja de les proves la pugui ajornar.

Desfer aquesta migració esborra les taules del M01 i les seves dades.
"""

import django.db.models.deletion
import django.db.models.functions.text
import django.db.models.lookups
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

PERSON_MATCHES_MEMBER_SQL = """
ALTER TABLE members_memberrequest
    ADD CONSTRAINT memberrequest_person_matches_member
    FOREIGN KEY (member_id, person_id) REFERENCES members_member (id, person_id)
    DEFERRABLE INITIALLY IMMEDIATE;
"""

DROP_PERSON_MATCHES_MEMBER_SQL = """
ALTER TABLE members_memberrequest DROP CONSTRAINT memberrequest_person_matches_member;
"""


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0009_private_files"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MembershipNumberCounter",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "last_number",
                    models.PositiveIntegerField(default=0, verbose_name="últim número"),
                ),
            ],
            options={
                "verbose_name": "comptador de números de soci",
                "verbose_name_plural": "comptador de números de soci",
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("id", 1)), name="counter_single_row")
                ],
            },
        ),
        migrations.CreateModel(
            name="MembershipType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("code", models.CharField(max_length=20, unique=True, verbose_name="codi")),
                ("name", models.CharField(max_length=60, verbose_name="nom")),
                (
                    "annual_fee_cents",
                    models.PositiveIntegerField(verbose_name="quota anual (cèntims)"),
                ),
                ("active", models.BooleanField(default=True, verbose_name="actiu")),
            ],
            options={
                "verbose_name": "tipus de soci",
                "verbose_name_plural": "tipus de soci",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("annual_fee_cents__gt", 0)),
                        name="membershiptype_fee_positive",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Member",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "member_number",
                    models.PositiveIntegerField(
                        blank=True, null=True, verbose_name="número de soci"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendent"),
                            ("active", "Actiu"),
                            ("unpaid", "Impagat"),
                            ("left", "Baixa"),
                        ],
                        default="pending",
                        max_length=10,
                        verbose_name="estat",
                    ),
                ),
                ("joined_on", models.DateField(verbose_name="data d'alta")),
                (
                    "joined_on_is_approximate",
                    models.BooleanField(default=False, verbose_name="data d'alta aproximada"),
                ),
                ("left_on", models.DateField(blank=True, null=True, verbose_name="data de baixa")),
                (
                    "cluber_id",
                    models.CharField(
                        blank=True, max_length=40, null=True, verbose_name="identificador de Cluber"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "person",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="member",
                        to="core.person",
                        verbose_name="persona",
                    ),
                ),
                (
                    "type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="members",
                        to="members.membershiptype",
                        verbose_name="tipus",
                    ),
                ),
            ],
            options={
                "verbose_name": "soci",
                "verbose_name_plural": "socis",
            },
        ),
        migrations.CreateModel(
            name="MemberStatusChange",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "from_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("pending", "Pendent"),
                            ("active", "Actiu"),
                            ("unpaid", "Impagat"),
                            ("left", "Baixa"),
                        ],
                        max_length=10,
                        verbose_name="estat anterior",
                    ),
                ),
                (
                    "to_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendent"),
                            ("active", "Actiu"),
                            ("unpaid", "Impagat"),
                            ("left", "Baixa"),
                        ],
                        max_length=10,
                        verbose_name="estat nou",
                    ),
                ),
                ("effective_on", models.DateField(verbose_name="data efectiva")),
                ("reason", models.TextField(blank=True, verbose_name="motiu")),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="data i hora"
                    ),
                ),
                (
                    "actor_account",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="compte",
                    ),
                ),
                (
                    "from_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="members.membershiptype",
                        verbose_name="tipus anterior",
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="status_changes",
                        to="members.member",
                        verbose_name="soci",
                    ),
                ),
                (
                    "to_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="members.membershiptype",
                        verbose_name="tipus nou",
                    ),
                ),
            ],
            options={
                "verbose_name": "canvi d'estat o de tipus",
                "verbose_name_plural": "historial dels socis",
            },
        ),
        migrations.CreateModel(
            name="LicenceRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "licence_type",
                    models.CharField(max_length=100, verbose_name="tipus de llicència"),
                ),
                ("issued_on", models.DateField(verbose_name="data d'alta")),
                (
                    "expires_on",
                    models.DateField(blank=True, null=True, verbose_name="data de caducitat"),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[("manual", "Manual"), ("cluber", "Cluber")],
                        max_length=10,
                        verbose_name="origen",
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="licence_records",
                        to="members.member",
                        verbose_name="soci",
                    ),
                ),
            ],
            options={
                "verbose_name": "registre de llicència",
                "verbose_name_plural": "registres de llicència",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            ("expires_on__isnull", True),
                            ("expires_on__gte", models.F("issued_on")),
                            _connector="OR",
                        ),
                        name="licencerecord_expires_after_issue",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("source__in", ["manual", "cluber"])),
                        name="licencerecord_source_valid",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="AnnualFee",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("period", models.PositiveSmallIntegerField(verbose_name="període")),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("annual", "Quota anual"),
                            ("type_change_supplement", "Suplement de canvi de tipus"),
                        ],
                        max_length=25,
                        verbose_name="tipus de quota",
                    ),
                ),
                ("due_on", models.DateField(verbose_name="venciment")),
                (
                    "charge",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="annual_fee",
                        to="core.charge",
                        verbose_name="càrrec",
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="fees",
                        to="members.member",
                        verbose_name="soci",
                    ),
                ),
            ],
            options={
                "verbose_name": "quota",
                "verbose_name_plural": "quotes",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("member", "period", "kind"), name="annualfee_unique_period_kind"
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("kind__in", ["annual", "type_change_supplement"])),
                        name="annualfee_kind_valid",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="MemberCard",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "token_hash",
                    models.CharField(
                        max_length=64, unique=True, verbose_name="empremta del testimoni"
                    ),
                ),
                (
                    "issued_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="emès el"),
                ),
                (
                    "revoked_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="revocat el"),
                ),
                (
                    "revoked_reason",
                    models.TextField(blank=True, verbose_name="motiu de la revocació"),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cards",
                        to="members.member",
                        verbose_name="soci",
                    ),
                ),
            ],
            options={
                "verbose_name": "carnet",
                "verbose_name_plural": "carnets",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("token_hash__regex", "^[0-9a-f]{64}$")),
                        name="membercard_token_hash_sha256_hex",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("revoked_at__isnull", True)),
                        fields=("member",),
                        name="membercard_one_active_per_member",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(("revoked_at__isnull", True), ("revoked_reason", "")),
                            models.Q(
                                ("revoked_at__isnull", False),
                                django.db.models.lookups.GreaterThan(
                                    django.db.models.functions.text.Length(
                                        django.db.models.functions.text.Trim("revoked_reason")
                                    ),
                                    0,
                                ),
                            ),
                            _connector="OR",
                        ),
                        name="membercard_revoked_with_reason",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="MemberRequest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("join", "Alta"),
                            ("change_type", "Canvi de tipus"),
                            ("leave", "Baixa"),
                        ],
                        max_length=12,
                        verbose_name="tipus de sol·licitud",
                    ),
                ),
                (
                    "request_reason",
                    models.TextField(blank=True, verbose_name="motiu de la sol·licitud"),
                ),
                (
                    "resolution_reason",
                    models.TextField(blank=True, verbose_name="motiu de la resolució"),
                ),
                (
                    "channel",
                    models.CharField(
                        choices=[("web", "Web"), ("in_person", "Presencial")],
                        max_length=10,
                        verbose_name="canal",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendent"),
                            ("approved", "Aprovada"),
                            ("rejected", "Rebutjada"),
                            ("cancelled", "Cancel·lada"),
                        ],
                        default="pending",
                        max_length=10,
                        verbose_name="estat",
                    ),
                ),
                (
                    "resolved_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="resolta el"),
                ),
                (
                    "effective_on",
                    models.DateField(blank=True, null=True, verbose_name="data efectiva"),
                ),
                (
                    "duplicate_warning",
                    models.JSONField(
                        blank=True, default=list, verbose_name="avís de possible duplicat"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "member",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="requests",
                        to="members.member",
                        verbose_name="soci",
                    ),
                ),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="member_requests",
                        to="core.person",
                        verbose_name="persona",
                    ),
                ),
                (
                    "resolved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="resolta per",
                    ),
                ),
                (
                    "requested_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="members.membershiptype",
                        verbose_name="tipus demanat",
                    ),
                ),
            ],
            options={
                "verbose_name": "sol·licitud de soci",
                "verbose_name_plural": "sol·licituds de soci",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("kind__in", ["join", "change_type", "leave"])),
                        name="memberrequest_kind_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("channel__in", ["web", "in_person"])),
                        name="memberrequest_channel_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("status__in", ["pending", "approved", "rejected", "cancelled"])
                        ),
                        name="memberrequest_status_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(("kind", "leave"), _negated=True),
                            django.db.models.lookups.GreaterThan(
                                django.db.models.functions.text.Length(
                                    django.db.models.functions.text.Trim("request_reason")
                                ),
                                0,
                            ),
                            _connector="OR",
                        ),
                        name="memberrequest_leave_has_reason",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(("status", "rejected"), _negated=True),
                            django.db.models.lookups.GreaterThan(
                                django.db.models.functions.text.Length(
                                    django.db.models.functions.text.Trim("resolution_reason")
                                ),
                                0,
                            ),
                            _connector="OR",
                        ),
                        name="memberrequest_rejection_has_reason",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(
                                ("kind__in", ["join", "change_type"]),
                                ("requested_type__isnull", False),
                            ),
                            models.Q(("kind", "leave"), ("requested_type__isnull", True)),
                            _connector="OR",
                        ),
                        name="memberrequest_requested_type_by_kind",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("kind", "join"), ("member__isnull", False), _connector="OR"
                        ),
                        name="memberrequest_member_by_kind",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("status", "pending")),
                        fields=("person", "kind"),
                        name="memberrequest_one_pending_per_kind",
                    ),
                ],
            },
        ),
        migrations.AddIndex(
            model_name="member",
            index=models.Index(fields=["status", "type"], name="member_status_type_idx"),
        ),
        migrations.AddConstraint(
            model_name="member",
            constraint=models.UniqueConstraint(
                condition=models.Q(("member_number__isnull", False)),
                fields=("member_number",),
                name="member_unique_number",
            ),
        ),
        migrations.AddConstraint(
            model_name="member",
            constraint=models.UniqueConstraint(
                condition=models.Q(("cluber_id__isnull", False)),
                fields=("cluber_id",),
                name="member_unique_cluber_id",
            ),
        ),
        migrations.AddConstraint(
            model_name="member",
            constraint=models.CheckConstraint(
                condition=models.Q(("status__in", ["pending", "active", "unpaid", "left"])),
                name="member_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="member",
            constraint=models.UniqueConstraint(fields=("id", "person"), name="member_id_person"),
        ),
        migrations.AddIndex(
            model_name="memberstatuschange",
            index=models.Index(
                fields=["member", "created_at"], name="memberstatuschange_member_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="memberstatuschange",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("from_status__in", ["", "pending", "active", "unpaid", "left"])
                ),
                name="memberstatuschange_from_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="memberstatuschange",
            constraint=models.CheckConstraint(
                condition=models.Q(("to_status__in", ["pending", "active", "unpaid", "left"])),
                name="memberstatuschange_to_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="memberstatuschange",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("to_status__in", ["left", "unpaid"]),
                        models.Q(("from_status", "unpaid"), ("to_status", "active")),
                        _connector="OR",
                        _negated=True,
                    ),
                    django.db.models.lookups.GreaterThan(
                        django.db.models.functions.text.Length(
                            django.db.models.functions.text.Trim("reason")
                        ),
                        0,
                    ),
                    _connector="OR",
                ),
                name="memberstatuschange_reason_when_required",
            ),
        ),
        migrations.RunSQL(PERSON_MATCHES_MEMBER_SQL, DROP_PERSON_MATCHES_MEMBER_SQL),
    ]
