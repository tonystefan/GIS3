from django.contrib import admin

from .models import Ata, GlossarioTermo, OneDriveToken, TranscricaoJob


@admin.register(TranscricaoJob)
class TranscricaoJobAdmin(admin.ModelAdmin):
    list_display = ['onedrive_file_name', 'user', 'status', 'duracao_formatada', 'created_at']
    list_filter = ['status', 'user']
    search_fields = ['onedrive_file_name', 'user__username']
    readonly_fields = ['transcricao_raw', 'transcricao_processada', 'erro', 'iniciado_em', 'concluido_em']
    ordering = ['-created_at']


@admin.register(Ata)
class AtaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'data_reuniao', 'local']
    search_fields = ['titulo']
    ordering = ['-data_reuniao']


@admin.register(GlossarioTermo)
class GlossarioTermoAdmin(admin.ModelAdmin):
    list_display = ['termo_correto', 'categoria', 'ativo']
    list_filter = ['categoria', 'ativo']
    search_fields = ['termo_correto']


@admin.register(OneDriveToken)
class OneDriveTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'expires_at', 'is_expired']
    readonly_fields = ['access_token', 'refresh_token']
