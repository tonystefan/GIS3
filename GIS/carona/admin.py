from django.contrib import admin
from .models import (
    Pessoa,    
    Rota,
    Veiculo,
    PrecoKM,
    Carona,
    Participante,    
)

admin.site.register(Pessoa)
admin.site.register(Rota)
admin.site.register(Veiculo)
admin.site.register(PrecoKM)
admin.site.register(Carona)
admin.site.register(Participante)