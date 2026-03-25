from django.contrib.auth.models import User
from django.db import models

from common.models import TimeStampedModel


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nome_exibicao = models.CharField(max_length=100, blank=True)
    empresa = models.CharField(max_length=100, blank=True)
    cargo = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username

    def get_nome(self):
        return self.nome_exibicao or self.user.get_full_name() or self.user.username
