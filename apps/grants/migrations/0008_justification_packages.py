"""T-M09A-10a (M09-ajuts-6): paquet de justificació, només INSERT a l'ORM (RN-M09A-11)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


# fmt: off
class Migration(migrations.Migration):

    dependencies = [
        ('core', '0078_website_and_dashboard_permissions'),
        ('grants', '0007_reminders'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JustificationPackage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generated_at', models.DateTimeField(auto_now_add=True, verbose_name='generat el')),
                ('masked', models.BooleanField(verbose_name='amb les còpies emmascarades')),
                ('sha256', models.CharField(max_length=64, verbose_name='sha256 del ZIP')),
                ('totals', models.JSONField(verbose_name='totals')),
                ('excluded', models.JSONField(default=list, verbose_name='excloses')),
                ('items', models.JSONField(default=list, verbose_name='incloses')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='packages', to='grants.grantapplication', verbose_name='sol·licitud')),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='core.privatefile', verbose_name='ZIP')),
                ('generated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='generat per')),
            ],
            options={
                'verbose_name': 'paquet de justificació',
                'verbose_name_plural': 'paquets de justificació',
                'ordering': ['application', 'pk'],
            },
        ),
    ]
# fmt: on
