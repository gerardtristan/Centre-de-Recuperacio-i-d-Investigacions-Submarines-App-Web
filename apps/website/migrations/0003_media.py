"""T-M07-07 (M07-6): fotos de la web (RN-M07-05, P-489, P-591)."""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


# fmt: off
class Migration(migrations.Migration):

    dependencies = [
        ('website', '0002_pages'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MediaAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='clau pública')),
                ('storage_key', models.CharField(max_length=100, unique=True, verbose_name="clau a l'emmagatzematge")),
                ('content_type', models.CharField(max_length=100, verbose_name='tipus de contingut')),
                ('size_bytes', models.PositiveBigIntegerField(verbose_name='mida (bytes)')),
                ('alt_text', models.CharField(max_length=300, verbose_name='text alternatiu')),
                ('author', models.CharField(blank=True, max_length=200, verbose_name='autor')),
                ('licence_note', models.CharField(blank=True, max_length=300, verbose_name="permís d'ús")),
                ('shows_people', models.BooleanField(verbose_name="s'hi veuen persones")),
                ('people_consent', models.BooleanField(default=False, verbose_name='hi ha el consentiment de les persones')),
                ('credit', models.CharField(blank=True, max_length=200, verbose_name='crèdit')),
                ('status', models.CharField(choices=[('active', 'Activa'), ('retired', 'Retirada')], default='active', max_length=20, verbose_name='estat')),
                ('retired_reason', models.CharField(blank=True, max_length=300, verbose_name='motiu de la retirada')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='pujada el')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='pujada per')),
            ],
            options={
                'verbose_name': 'foto de la web',
                'verbose_name_plural': 'fotos de la web',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
# fmt: on
