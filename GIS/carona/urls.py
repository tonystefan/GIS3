from django.contrib import admin
from django.urls import path
from . import views
from django.views.generic.base import View

from .views import(
    CaronaCreate
)
app_name = 'carona'

urlpatterns = [
    path('carona/', views.index, name='index'),
    path('carona_create',CaronaCreate.as_view(), name='carona_create'),
]
