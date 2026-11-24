"""T-M09A-10b (M09-ajuts-6): paquet enviat i versions (RN-M09A-18 i 21)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


# fmt: off
class Migration(migrations.Migration):

    dependencies = [
        ('grants', '0008_justification_packages'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='grantapplication',
            name='submitted_package',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='grants.justificationpackage', verbose_name='paquet enviat'),
        ),
        migrations.CreateModel(
            name='PackageSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.PositiveSmallIntegerField(verbose_name='versió')),
                ('sent_on', models.DateField(verbose_name="data d'enviament")),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='submissions', to='grants.grantapplication', verbose_name='sol·licitud')),
                ('package', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='submission', to='grants.justificationpackage', verbose_name='paquet')),
                ('requirement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='grants.grantrequirement', verbose_name='requeriment')),
                ('sent_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='enviat per')),
            ],
            options={
                'verbose_name': 'versió enviada del paquet',
                'verbose_name_plural': 'versions enviades del paquet',
                'ordering': ['application', 'version'],
                'constraints': [models.UniqueConstraint(fields=('application', 'version'), name='grant_submission_version_unique'), models.CheckConstraint(condition=models.Q(models.Q(('requirement__isnull', True), ('version', 1)), models.Q(('requirement__isnull', False), ('version__gt', 1)), _connector='OR'), name='grant_submission_requirement_after_v1')],
            },
        ),
    ]
# fmt: on
