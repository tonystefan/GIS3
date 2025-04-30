from django.contrib import admin
from django.urls import path
from . import views
from django.views.generic.base import View

from .views import(
    CaronaCreate,
    Index,
)


urlpatterns = [
    path('index', Index.as_view(), name='carona_index'),
    path('carona_create',CaronaCreate.as_view(), name='carona_create'),
]
