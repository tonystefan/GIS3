# Generated by Django 4.2.9 on 2025-04-25 18:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('carona', '0003_alter_pessoa_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pessoa',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pessoas', to=settings.AUTH_USER_MODEL, verbose_name='usuario'),
        ),
    ]
