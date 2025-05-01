from django.contrib import admin
from django.urls import path
from . import views
from django.views.generic.base import View

from .views import(
    CaronaCreate,
    Index,
    ParticipantesUso,
)


urlpatterns = [
    path('index', Index.as_view(), name='carona_index'),
    path('participantes_uso', ParticipantesUso.as_view(), name='participantes_uso'),
    path('carona_create',CaronaCreate.as_view(), name='carona_create'),
]
