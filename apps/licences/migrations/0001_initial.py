"""T-M06-02 (models) i T-M06-03 (M06-6): tipus, versions de preu i llicències. Les versions de preu
només admeten INSERT, també amb una consulta directa (RN-M06-08; patró de treasury/0006). Cap
tipus ni preu inicial: els sis tipus de la 058 són la T-M06-21."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

PRICE_APPEND_ONLY_SQL = """
CREATE FUNCTION licences_price_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Els preus de llicència no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;

CREATE TRIGGER licences_price_no_update_or_delete
    BEFORE UPDATE OR DELETE ON licences_licenceprice
    FOR EACH ROW EXECUTE FUNCTION licences_price_immutable();

CREATE TRIGGER licences_price_no_truncate
    BEFORE TRUNCATE ON licences_licenceprice
    FOR EACH STATEMENT EXECUTE FUNCTION licences_price_immutable();
"""

PRICE_APPEND_ONLY_REVERSE_SQL = """
DROP TRIGGER licences_price_no_truncate ON licences_licenceprice;
DROP TRIGGER licences_price_no_update_or_delete ON licences_licenceprice;
DROP FUNCTION licences_price_immutable();
"""


# fmt: off
class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0059_transfer_reminder_permission'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LicenceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True, verbose_name='nom')),
                ('description', models.TextField(blank=True, verbose_name='descripció')),
                ('category', models.CharField(choices=[('amateur', 'Aficionat'), ('technical', 'Tècnic'), ('other', 'Altres')], max_length=9, verbose_name='categoria')),
                ('validity_rule', models.CharField(choices=[('calendar_year', 'Any natural'), ('days_365', '365 dies'), ('single_day', 'Un dia')], max_length=13, verbose_name='regla de validesa')),
                ('active', models.BooleanField(default=True, verbose_name='actiu')),
            ],
            options={
                'verbose_name': 'tipus de llicència',
                'verbose_name_plural': 'tipus de llicència',
                'constraints': [models.CheckConstraint(condition=models.Q(('category__in', ['amateur', 'technical', 'other'])), name='licences_type_category_valid'), models.CheckConstraint(condition=models.Q(('validity_rule__in', ['calendar_year', 'days_365', 'single_day'])), name='licences_type_validity_rule_valid')],
            },
        ),
        migrations.CreateModel(
            name='LicencePrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('federation_cost_cents', models.PositiveIntegerField(verbose_name='preu de la federació (cèntims)')),
                ('non_member_surcharge_cents', models.PositiveIntegerField(verbose_name='recàrrec de no soci (cèntims)')),
                ('valid_from', models.DateField(verbose_name='vàlid des de')),
                ('valid_to', models.DateField(blank=True, null=True, verbose_name='vàlid fins a')),
                ('note', models.TextField(verbose_name='nota')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='creat per')),
                ('licence_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='prices', to='licences.licencetype', verbose_name='tipus')),
            ],
            options={
                'verbose_name': 'preu de llicència',
                'verbose_name_plural': 'preus de llicència',
                'constraints': [models.CheckConstraint(condition=models.Q(('federation_cost_cents__gt', 0)), name='licences_price_cost_positive'), models.CheckConstraint(condition=models.Q(('valid_to__isnull', True), ('valid_to__gte', models.F('valid_from')), _connector='OR'), name='licences_price_dates_ordered'), models.CheckConstraint(condition=models.Q(('note__regex', '^\\s*$'), _negated=True), name='licences_price_note_required')],
            },
        ),
        migrations.CreateModel(
            name='Licence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('validity_rule', models.CharField(choices=[('calendar_year', 'Any natural'), ('days_365', '365 dies'), ('single_day', 'Un dia')], max_length=13, verbose_name='regla de validesa')),
                ('status', models.CharField(choices=[('requested', 'Sol·licitada'), ('paid', 'Pagada'), ('filed', 'Tramitada'), ('active', 'Vigent'), ('cancelled', 'Cancel·lada'), ('lapsed', 'No tramitada a temps')], max_length=9, verbose_name='estat')),
                ('origin', models.CharField(choices=[('club', 'Del club'), ('external', 'Ja en tenia una'), ('imported_m01', 'Registre del 01')], max_length=12, verbose_name='origen')),
                ('starts_on', models.DateField(verbose_name='inici')),
                ('expires_on', models.DateField(verbose_name='caducitat')),
                ('federation_number', models.CharField(blank=True, max_length=30, verbose_name='número federatiu')),
                ('price_kind', models.CharField(choices=[('member', 'Soci'), ('non_member', 'No soci')], max_length=10, null=True, verbose_name='tipus de preu')),
                ('price_cents', models.PositiveIntegerField(null=True, verbose_name='preu (cèntims)')),
                ('m01_record_ref', models.PositiveBigIntegerField(null=True, verbose_name='registre del 01')),
                ('filed_at', models.DateTimeField(null=True)),
                ('activated_at', models.DateTimeField(null=True)),
                ('cancellation_reason', models.TextField(blank=True, verbose_name='motiu de la cancel·lació')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('activated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('cancelled_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('charge', models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='licence', to='core.charge', verbose_name='càrrec')),
                ('filed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('import_batch', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='core.importbatch', verbose_name="lot d'importació")),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='licences', to='core.person', verbose_name='persona')),
                ('renewal_of', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='renewals', to='licences.licence', verbose_name='renovació de')),
                ('licence_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='licences', to='licences.licencetype', verbose_name='tipus')),
            ],
            options={
                'verbose_name': 'llicència',
                'verbose_name_plural': 'llicències',
                'indexes': [models.Index(fields=['status', 'expires_on'], name='licences_status_expires'), models.Index(fields=['person', 'expires_on'], name='licences_person_expires')],
                'constraints': [models.CheckConstraint(condition=models.Q(('status__in', ['requested', 'paid', 'filed', 'active', 'cancelled', 'lapsed'])), name='licences_licence_status_valid'), models.CheckConstraint(condition=models.Q(('origin__in', ['club', 'external', 'imported_m01'])), name='licences_licence_origin_valid'), models.CheckConstraint(condition=models.Q(('validity_rule__in', ['calendar_year', 'days_365', 'single_day'])), name='licences_licence_validity_rule_valid'), models.CheckConstraint(condition=models.Q(('expires_on__gte', models.F('starts_on'))), name='licences_licence_dates_ordered'), models.CheckConstraint(condition=models.Q(models.Q(('status', 'lapsed'), _negated=True), ('validity_rule', 'single_day'), _connector='OR'), name='licences_licence_lapsed_only_single_day'), models.CheckConstraint(condition=models.Q(models.Q(('status', 'cancelled'), _negated=True), models.Q(('cancellation_reason__regex', '^\\s*$'), _negated=True), _connector='OR'), name='licences_licence_cancel_has_reason'), models.CheckConstraint(condition=models.Q(models.Q(('origin', 'club'), ('price_cents__isnull', False), ('price_kind__isnull', False)), models.Q(models.Q(('origin', 'club'), _negated=True), ('charge__isnull', True), ('price_cents__isnull', True), ('price_kind__isnull', True)), _connector='OR'), name='licences_licence_price_only_club'), models.CheckConstraint(condition=models.Q(('origin', 'imported_m01'), models.Q(('import_batch__isnull', True), ('m01_record_ref__isnull', True)), _connector='OR'), name='licences_licence_import_only_m01'), models.UniqueConstraint(condition=models.Q(('status__in', ('requested', 'paid', 'filed')), models.Q(('validity_rule', 'single_day'), _negated=True)), fields=('person', 'licence_type'), name='licences_licence_one_in_progress'), models.UniqueConstraint(condition=models.Q(('status__in', ('requested', 'paid', 'filed')), ('validity_rule', 'single_day')), fields=('person', 'licence_type', 'starts_on'), name='licences_licence_one_day_in_progress')],
            },
        ),
        migrations.RunSQL(PRICE_APPEND_ONLY_SQL, PRICE_APPEND_ONLY_REVERSE_SQL),
    ]
# fmt: on
