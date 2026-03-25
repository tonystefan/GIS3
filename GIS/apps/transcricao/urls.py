from django.urls import path
from . import views

app_name = 'transcricao'

urlpatterns = [
    # Dashboard
    path('', views.IndexView.as_view(), name='index'),

    # Jobs
    path('jobs/criar/', views.JobCreateView.as_view(), name='job_create'),
    path('jobs/criar/onedrive/', views.JobCreateOneDriveView.as_view(), name='job_create_onedrive'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/<int:pk>/status/', views.JobStatusView.as_view(), name='job_status'),
    path('jobs/<int:pk>/download/', views.DownloadDocxView.as_view(), name='job_download_docx'),
    path('jobs/lista/', views.JobListPartialView.as_view(), name='job_list_partial'),

    # OneDrive
    path('onedrive/conectar/', views.OneDriveConnectView.as_view(), name='onedrive_connect'),
    path('onedrive/callback/', views.OneDriveCallbackView.as_view(), name='onedrive_callback'),
    path('onedrive/desconectar/', views.OneDriveDisconnectView.as_view(), name='onedrive_disconnect'),
    path('onedrive/arquivos/', views.FileBrowserView.as_view(), name='file_browser'),

    # Glossário
    path('glossario/', views.GlossarioView.as_view(), name='glossario'),
    path('glossario/criar/', views.GlossarioCreateView.as_view(), name='glossario_create'),
    path('glossario/<int:pk>/excluir/', views.GlossarioDeleteView.as_view(), name='glossario_delete'),

    # Cron
    path('api/cron/', views.CronProcessView.as_view(), name='cron_process'),
]
