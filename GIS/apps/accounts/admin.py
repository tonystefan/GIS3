from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'nome_exibicao', 'empresa', 'cargo']
    search_fields = ['user__username', 'nome_exibicao', 'empresa']
