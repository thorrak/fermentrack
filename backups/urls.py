from django.urls import path

from . import views

app_name = "backups"

urlpatterns = [
    # Backup Views
    path(route='', view=views.BackupListView.as_view(), name='backup_list'),
    path(route='add/', view=views.BackupCreateView.as_view(), name='backup_add'),
    path(route='restore/', view=views.RestoreView.as_view(), name='backup_restore'),
    path(route='view/<int:pk>/', view=views.BackupDetailView.as_view(), name='backup_detail'),
    path(route='delete/<int:pk>/', view=views.BackupDeleteView.as_view(), name='backup_delete'),
    path(route='download/<int:pk>/', view=views.BackupDownloadView.as_view(), name='backup_download'),
    # path(route='update/<slug:slug>/', view=views.BackupUpdateView.as_view(), name='backup_update'),

]
