"""T-M07-09 (M07-6): temes i preguntes freqüents (M07b, RN-M07-12)."""

import django.db.models.deletion
from django.db import migrations, models


# fmt: off
class Migration(migrations.Migration):

    dependencies = [
        ('website', '0008_public_images'),
    ]

    operations = [
        migrations.CreateModel(
            name='FaqTopic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='nom')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='ordre')),
            ],
            options={
                'verbose_name': "tema de l'ajuda",
                'verbose_name_plural': "temes de l'ajuda",
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='FaqEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=300, verbose_name='pregunta')),
                ('answer', models.TextField(verbose_name='resposta')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='ordre')),
                ('published', models.BooleanField(default=False, verbose_name='publicada')),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entries', to='website.faqtopic', verbose_name='tema')),
            ],
            options={
                'verbose_name': 'pregunta freqüent',
                'verbose_name_plural': 'preguntes freqüents',
                'ordering': ['topic__order', 'topic__name', 'order', 'pk'],
            },
        ),
    ]
# fmt: on
