from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('home.urls')),
    path('', include('carona.urls')),
    path("admin/", admin.site.urls),
    path('', include('admin_coreui.urls')),
]
