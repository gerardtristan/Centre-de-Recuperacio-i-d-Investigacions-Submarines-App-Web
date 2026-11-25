"""T-M07-08 (M07-6): notícies (P-M07-B, RN-M07-02)."""

import django.db.models.deletion
from django.db import migrations, models


# fmt: off
class Migration(migrations.Migration):

    dependencies = [
        ('website', '0006_newsletter_sending'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='títol')),
                ('slug', models.SlugField(max_length=80, unique=True, verbose_name='adreça')),
                ('date', models.DateField(verbose_name='data')),
                ('body', models.TextField(verbose_name='cos')),
                ('status', models.CharField(choices=[('draft', 'Esborrany'), ('published', 'Publicada'), ('retired', 'Retirada')], default='draft', max_length=20, verbose_name='estat')),
                ('retired_reason', models.CharField(blank=True, max_length=300, verbose_name='motiu de la retirada')),
                ('image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='website.mediaasset', verbose_name='foto')),
            ],
            options={
                'verbose_name': 'notícia',
                'verbose_name_plural': 'notícies',
                'ordering': ['-date', '-pk'],
            },
        ),
    ]
# fmt: on
