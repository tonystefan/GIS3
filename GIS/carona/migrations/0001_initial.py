# Generated by Django 4.2.9 on 2025-04-25 17:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Rota',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome da Rota')),
                ('distancia', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Distância (km)')),
                ('descricao', models.TextField(blank=True, null=True, verbose_name='Descrição')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativa')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Rotas',
            },
        ),
        migrations.CreateModel(
            name='Veiculo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modelo', models.CharField(max_length=100, verbose_name='Modelo')),
                ('consumo', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Consumo (km/l)')),
                ('capacidade', models.PositiveSmallIntegerField(default=4, verbose_name='Capacidade')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('proprietario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='veiculos', to=settings.AUTH_USER_MODEL, verbose_name='Proprietário')),
            ],
            options={
                'verbose_name': 'Veículo',
                'verbose_name_plural': 'Veículos',
                'ordering': ['modelo', 'proprietario'],
            },
        ),
        migrations.CreateModel(
            name='PrecoKM',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preco', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Preço KM')),
                ('data', models.DateField(verbose_name='Data de Vigência')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='precosKM', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
            ],
            options={
                'verbose_name': 'Preço do Kilometro',
                'verbose_name_plural': 'Preços de Combustível',
                'ordering': ['-data'],
            },
        ),
        migrations.CreateModel(
            name='Carona',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(verbose_name='data')),
                ('direction', models.CharField(choices=[('one_way', 'Somente Ida'), ('round_trip', 'Ida e Volta')], default='round_trip', max_length=10, verbose_name='Direção')),
                ('preco_km', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Preço KM')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='caronas', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
                ('rota', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='caronas', to='carona.rota', verbose_name='Rota')),
                ('veiculo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='caronas', to='carona.veiculo', verbose_name='Veículo')),
            ],
            options={
                'verbose_name_plural': 'Caronas',
                'ordering': ['-data', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Participante',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('carona', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participantes', to='carona.carona', verbose_name='Carona')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='carona_participantes', to=settings.AUTH_USER_MODEL, verbose_name='Participante')),
            ],
            options={
                'verbose_name': 'Participante de Carona',
                'verbose_name_plural': 'Participantes de Carona',
                'ordering': ['carona', 'user'],
                'unique_together': {('carona', 'user')},
            },
        ),
    ]
